"""Store and search vectors using persistent Qdrant local or PostgreSQL + pgvector."""
import json
import uuid
from pathlib import Path
from typing import Any

from .models import Chunk

PERMITTED_FILTER_FIELDS = {"document_id", "source", "page", "year", "task_domain", "section"}


class QdrantLocalStore:
    """Persistent on-disk vector store using QdrantClient(path=...) with cosine similarity."""

    def __init__(self, storage_path: str | Path, dimensions: int, collection_name: str = "day6_chunks") -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be > 0")
        from qdrant_client import QdrantClient

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.dimensions = dimensions
        self.collection_name = collection_name
        self.client = QdrantClient(path=str(self.storage_path))

    def create_schema(self) -> None:
        from qdrant_client.models import Distance, VectorParams

        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.dimensions, distance=Distance.COSINE),
            )

    @staticmethod
    def _point_uuid(strategy: str, chunk_id: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{strategy}::{chunk_id}"))

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        from qdrant_client.models import FieldCondition, Filter, FilterSelector, MatchValue, PointStruct

        if len(chunks) != len(vectors):
            raise ValueError(f"Chunks count ({len(chunks)}) != vectors count ({len(vectors)})")
        for v in vectors:
            if len(v) != self.dimensions:
                raise ValueError(f"Vector dimension {len(v)} != expected {self.dimensions}")

        # Remove obsolete chunks for the documents being re-ingested under this strategy
        doc_ids = sorted({c.document_id for c in chunks})
        for doc_id in doc_ids:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=FilterSelector(
                    filter=Filter(
                        must=[
                            FieldCondition(key="strategy", match=MatchValue(value=strategy)),
                            FieldCondition(key="document_id", match=MatchValue(value=doc_id)),
                        ]
                    )
                ),
            )

        points: list[PointStruct] = []
        for chunk, vec in zip(chunks, vectors):
            payload = {
                **chunk.metadata,
                "strategy": strategy,
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "source": chunk.source,
                "page": int(chunk.page),
                "text": chunk.text,
            }
            points.append(
                PointStruct(
                    id=self._point_uuid(strategy, chunk.chunk_id),
                    vector=vec,
                    payload=payload,
                )
            )

        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)

    def count_strategy_points(self, strategy: str) -> int:
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        res = self.client.count(
            collection_name=self.collection_name,
            count_filter=Filter(must=[FieldCondition(key="strategy", match=MatchValue(value=strategy))]),
            exact=True,
        )
        return int(res.count)

    def search(
        self,
        strategy: str,
        query_vector: list[float],
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        from qdrant_client.models import FieldCondition, Filter, MatchValue, SearchParams

        if len(query_vector) != self.dimensions:
            raise ValueError(f"Query vector dim {len(query_vector)} != store dim {self.dimensions}")

        must_conditions = [FieldCondition(key="strategy", match=MatchValue(value=strategy))]
        if filters:
            for k, val in filters.items():
                if k not in PERMITTED_FILTER_FIELDS:
                    raise ValueError(f"Filter field '{k}' is not permitted")
                must_conditions.append(FieldCondition(key=k, match=MatchValue(value=val)))

        q_filter = Filter(must=must_conditions)
        if hasattr(self.client, "query_points"):
            resp = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=q_filter,
                limit=top_k,
                with_payload=True,
                search_params=SearchParams(exact=True),
            )
            scored_points = resp.points
        else:
            scored_points = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=q_filter,
                limit=top_k,
                with_payload=True,
                search_params=SearchParams(exact=True),
            )

        results: list[dict[str, Any]] = []
        for rank, pt in enumerate(scored_points, start=1):
            payload = dict(pt.payload or {})
            chunk_id = payload.pop("chunk_id", str(pt.id))
            text = payload.pop("text", "")
            results.append(
                {
                    "rank": rank,
                    "chunk_id": chunk_id,
                    "text": text,
                    "score": round(float(pt.score), 6),
                    "metadata": payload,
                }
            )
        return results


class PgVectorStore:
    """PostgreSQL + pgvector store implementation (compatible with starter contract)."""

    def __init__(self, database_url: str, dimensions: int) -> None:
        if not database_url:
            raise ValueError("database_url is required")
        if dimensions <= 0:
            raise ValueError("dimensions must be > 0")
        self.database_url = database_url
        self.dimensions = dimensions

    def create_schema(self) -> None:
        import psycopg

        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS chunks (
                        strategy TEXT NOT NULL,
                        chunk_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        source TEXT NOT NULL,
                        page INTEGER NOT NULL,
                        year INTEGER,
                        task_domain TEXT,
                        section TEXT,
                        text TEXT NOT NULL,
                        metadata JSONB NOT NULL,
                        embedding vector({self.dimensions}) NOT NULL,
                        PRIMARY KEY (strategy, chunk_id)
                    );
                    """
                )
            conn.commit()

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        import psycopg

        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        for v in vectors:
            if len(v) != self.dimensions:
                raise ValueError(f"Expected vector dim {self.dimensions}, got {len(v)}")

        doc_ids = sorted({c.document_id for c in chunks})
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                if doc_ids:
                    cur.execute(
                        "DELETE FROM chunks WHERE strategy = %s AND document_id = ANY(%s);",
                        (strategy, doc_ids),
                    )
                for c, vec in zip(chunks, vectors):
                    vec_str = "[" + ",".join(f"{x:.8f}" for x in vec) + "]"
                    cur.execute(
                        """
                        INSERT INTO chunks (
                            strategy, chunk_id, document_id, source, page,
                            year, task_domain, section, text, metadata, embedding
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::vector)
                        ON CONFLICT (strategy, chunk_id) DO UPDATE SET
                            document_id = EXCLUDED.document_id,
                            source = EXCLUDED.source,
                            page = EXCLUDED.page,
                            year = EXCLUDED.year,
                            task_domain = EXCLUDED.task_domain,
                            section = EXCLUDED.section,
                            text = EXCLUDED.text,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding;
                        """,
                        (
                            strategy,
                            c.chunk_id,
                            c.document_id,
                            c.source,
                            int(c.page),
                            c.metadata.get("year"),
                            c.metadata.get("task_domain"),
                            c.metadata.get("section"),
                            c.text,
                            json.dumps(c.metadata, ensure_ascii=False),
                            vec_str,
                        ),
                    )
            conn.commit()

    def search(
        self,
        strategy: str,
        query_vector: list[float],
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        import psycopg

        if len(query_vector) != self.dimensions:
            raise ValueError("Invalid query_vector dimensions")

        vec_str = "[" + ",".join(f"{x:.8f}" for x in query_vector) + "]"
        where_clauses = ["strategy = %s"]
        params: list[Any] = [strategy]

        if filters:
            for k, val in filters.items():
                if k not in PERMITTED_FILTER_FIELDS:
                    raise ValueError(f"Filter field '{k}' is not permitted")
                where_clauses.append(f"{k} = %s")
                params.append(val)

        where_sql = " AND ".join(where_clauses)
        sql = f"""
            SELECT chunk_id, text, 1 - (embedding <=> %s::vector) AS score, metadata
            FROM chunks
            WHERE {where_sql}
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """
        full_params = [vec_str, *params, vec_str, top_k]
        results: list[dict[str, Any]] = []
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, full_params)
                for rank, (cid, txt, score, meta) in enumerate(cur.fetchall(), start=1):
                    results.append(
                        {
                            "rank": rank,
                            "chunk_id": cid,
                            "text": txt,
                            "score": round(float(score), 6),
                            "metadata": meta if isinstance(meta, dict) else json.loads(meta),
                        }
                    )
        return results
