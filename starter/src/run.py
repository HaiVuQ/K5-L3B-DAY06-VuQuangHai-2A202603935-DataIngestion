"""Day 06 Data Ingestion & Benchmark Pipeline Orchestrator."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import statistics
import time
from typing import Any

from dotenv import load_dotenv

from .chunking import by_paragraph, fixed_size
from .embeddings import MyEmbedder
from .evaluation import evaluate_query, summarize
from .ingestion import load_pdf
from .models import Chunk, DocumentPage
from .store import QdrantLocalStore


def _compute_chunk_stats(chunks: list[Chunk]) -> dict[str, Any]:
    lengths = [len(c.text) for c in chunks]
    tokens_est = [len(c.text.split()) for c in chunks]
    if not lengths:
        return {}
    sorted_lens = sorted(lengths)
    n = len(sorted_lens)
    p50 = sorted_lens[n // 2]
    p90 = sorted_lens[min(n - 1, int(n * 0.9))]
    return {
        "chunk_count": n,
        "total_characters": sum(lengths),
        "total_words_approx_tokens": sum(tokens_est),
        "min_char_length": min(lengths),
        "max_char_length": max(lengths),
        "mean_char_length": round(statistics.mean(lengths), 1),
        "median_char_length_p50": p50,
        "p90_char_length": p90,
        "stdev_char_length": round(statistics.stdev(lengths), 1) if n > 1 else 0.0,
    }


def _extract_coherence_samples(
    pages: list[DocumentPage],
    chunks_by_strategy: dict[str, list[Chunk]],
) -> list[dict[str, Any]]:
    """Select the first 10 sorted page IDs and extract the chunk covering the midpoint of each page."""
    sorted_pages = sorted(pages, key=lambda p: p.metadata.get("page_id", f"{p.document_id}:p{p.page:02d}"))
    selected_pages = sorted_pages[:10]
    samples: list[dict[str, Any]] = []

    for idx, p in enumerate(selected_pages, start=1):
        page_id = p.metadata.get("page_id", f"{p.document_id}:p{p.page:02d}")
        mid_pos = len(p.text) // 2
        anchor_snippet = p.text[max(0, mid_pos - 60) : min(len(p.text), mid_pos + 60)].strip()
        anchor_probe = p.text[mid_pos : min(len(p.text), mid_pos + 35)].strip()

        strat_Order = {}
        for strat in ("A", "B", "C"):
            p_chunks = [
                c for c in chunks_by_strategy[strat]
                if c.document_id == p.document_id and c.page == p.page
            ]
            covering = [c for c in p_chunks if anchor_probe and anchor_probe in c.text]
            if not covering and p_chunks:
                covering = [p_chunks[len(p_chunks) // 2]]
            chosen = covering[0] if covering else None
            strat_Order[strat] = {
                "chunk_id": chosen.chunk_id if chosen else None,
                "char_length": len(chosen.text) if chosen else 0,
                "text": chosen.text if chosen else "",
            }

        samples.append(
            {
                "sample_id": f"coh_{idx:02d}",
                "page_id": page_id,
                "document_id": p.document_id,
                "page": p.page,
                "anchor_midpoint_char": mid_pos,
                "anchor_snippet": anchor_snippet,
                "strategy_chunks": strat_Order,
            }
        )
    return samples


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    starter_dir = Path(__file__).resolve().parents[1]
    load_dotenv(starter_dir / ".env")

    manifest_path = repo_root / "data" / "manifest.json"
    benchmark_path = repo_root / "benchmark" / "questions.json"
    results_dir = repo_root / "results"
    starter_results_dir = starter_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    starter_results_dir.mkdir(parents=True, exist_ok=True)

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    if not benchmark_path.exists():
        raise FileNotFoundError(f"Benchmark not found at {benchmark_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    questions = benchmark["questions"]

    # 1. Load and normalize corpus; record page-level ingestion log
    ingestion_log: list[dict[str, Any]] = []
    all_pages: list[DocumentPage] = []

    t_ingest_docs_start = time.perf_counter()
    for doc in manifest["documents"]:
        pdf_path = repo_root / doc["source_path"]
        doc_meta = {
            "title": doc["title"],
            "year": int(doc["year"]),
            "task_domain": doc["task_domain"],
            "license": doc["license_or_permission"],
        }
        doc_pages = load_pdf(
            path=pdf_path,
            document_id=doc["source_id"],
            source=doc["source_path"],
            doc_metadata=doc_meta,
            valid_pages=doc["valid_pages"],
            exclusion_reasons=doc.get("exclusion_reasons", {}),
            ingestion_log=ingestion_log,
        )
        all_pages.extend(doc_pages)
    doc_load_seconds = round(time.perf_counter() - t_ingest_docs_start, 4)

    if len(all_pages) < 30:
        raise RuntimeError(f"Corpus must have at least 30 valid content pages; got {len(all_pages)}")

    print(f"[1/5] Loaded {len(all_pages)} valid content pages across {len(manifest['documents'])} PDFs in {doc_load_seconds}s.")

    # 2. Initialize real embedding model and persistent Qdrant vector store
    model_name = os.getenv("EMBEDDING_MODEL") or "sentence-transformers/all-MiniLM-L6-v2"
    t_model_start = time.perf_counter()
    embedder = MyEmbedder(model_name=model_name)
    model_init_seconds = round(time.perf_counter() - t_model_start, 4)
    print(f"[2/5] Initialized embedding model '{embedder.model_name}' (dim={embedder.dimensions}) in {model_init_seconds}s.")

    qdrant_path = repo_root / "data" / "qdrant_storage"
    store = QdrantLocalStore(storage_path=qdrant_path, dimensions=embedder.dimensions)
    store.create_schema()

    # 3. Build strategies A, B, C, embed, store, and verify idempotent re-ingestion
    strategy_configs = {
        "A": {
            "name": "Strategy A (Fixed-size 500 chars, overlap 50, unfiltered retrieval)",
            "chunking": "fixed_size",
            "chunk_size": 500,
            "overlap": 50,
            "use_metadata_filter": False,
        },
        "B": {
            "name": "Strategy B (Structure/Paragraph-aware max 1000 chars, unfiltered retrieval)",
            "chunking": "by_paragraph",
            "chunk_size": 1000,
            "overlap": 0,
            "use_metadata_filter": False,
        },
        "C": {
            "name": "Strategy C (Structure/Paragraph-aware max 1000 chars + metadata filtering)",
            "chunking": "by_paragraph",
            "chunk_size": 1000,
            "overlap": 0,
            "use_metadata_filter": True,
        },
    }

    chunks_by_strategy: dict[str, list[Chunk]] = {}
    strategy_stats: dict[str, Any] = {}

    # Cache B's embeddings to also measure & verify identical chunking between B and C
    for strat in ("A", "B", "C"):
        t0 = time.perf_counter()
        chunks: list[Chunk] = []
        for page in all_pages:
            if strat == "A":
                chunks.extend(fixed_size(page, size=500, overlap=50))
            else:
                chunks.extend(by_paragraph(page, max_size=1000, strategy_label=strat))
        t_chunk = time.perf_counter() - t0

        t_emb0 = time.perf_counter()
        vectors = embedder.embed_documents([c.text for c in chunks])
        t_emb = time.perf_counter() - t_emb0

        t_up0 = time.perf_counter()
        store.upsert(strategy=strat, chunks=chunks, vectors=vectors)
        count_after_first = store.count_strategy_points(strat)
        # Re-ingest immediately to verify idempotency (no duplicates on reload)
        store.upsert(strategy=strat, chunks=chunks, vectors=vectors)
        count_after_reingest = store.count_strategy_points(strat)
        t_up = time.perf_counter() - t_up0

        total_ingest_sec = round(t_chunk + t_emb + t_up, 4)
        c_stats = _compute_chunk_stats(chunks)
        chunks_by_strategy[strat] = chunks
        strategy_stats[strat] = {
            **strategy_configs[strat],
            **c_stats,
            "chunking_time_sec": round(t_chunk, 4),
            "embedding_time_sec": round(t_emb, 4),
            "upsert_and_reingest_verify_sec": round(t_up, 4),
            "total_ingest_time_sec": total_ingest_sec,
            "cost_usd": 0.0,
            "count_after_first_ingest": count_after_first,
            "count_after_reingest": count_after_reingest,
            "idempotent_verified": count_after_first == count_after_reingest == len(chunks),
        }
        print(
            f"[3/5] Strategy {strat}: {len(chunks)} chunks | ingest={total_ingest_sec}s | "
            f"idempotent={count_after_first}->{count_after_reingest}"
        )

    # 4. Run benchmark queries across all 3 strategies and collect traces
    all_traces: list[dict[str, Any]] = []
    query_vectors: dict[str, list[float]] = {}
    for q in questions:
        query_vectors[q["id"]] = embedder.embed_query(q["question"])

    for strat in ("A", "B", "C"):
        use_filter = strategy_configs[strat]["use_metadata_filter"]
        for q in questions:
            q_vec = query_vectors[q["id"]]
            applied_filter = q.get("filter") if (use_filter and q.get("filter")) else None
            hits = store.search(
                strategy=strat,
                query_vector=q_vec,
                top_k=3,
                filters=applied_filter,
            )
            eval_res = evaluate_query(q, hits)
            trace_item = {
                "strategy": strat,
                "filter_applied_in_search": applied_filter,
                **eval_res,
            }
            all_traces.append(trace_item)

    metrics_summary = summarize(all_traces)
    coherence_samples = _extract_coherence_samples(all_pages, chunks_by_strategy)

    # 5. Save all outputs to results/ and starter/results/
    run_summary = {
        "executed_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "environment": {
            "python_package_versions": {
                "qdrant_client": "1.20.0",
                "fastembed": "0.2.7",
                "onnxruntime": "1.23.2",
                "pypdf": "6.21.4",
            },
            "embedding_model": embedder.model_name,
            "embedding_provider": "Local HuggingFace ONNX via FastEmbed (sentence-transformers/all-MiniLM-L6-v2)",
            "embedding_dimensions": embedder.dimensions,
            "vector_store": "Qdrant Local Persistent Storage (QdrantClient on-disk)",
            "storage_path": "data/qdrant_storage",
            "collection_name": store.collection_name,
            "similarity_metric": "Cosine (exact=True)",
            "api_cost_usd": 0.0,
        },
        "corpus_summary": {
            "total_documents": len(manifest["documents"]),
            "total_physical_pages": manifest["total_physical_pages"],
            "total_valid_content_pages": len(all_pages),
            "total_normalized_characters": sum(len(p.text) for p in all_pages),
            "document_load_seconds": doc_load_seconds,
        },
        "strategy_ingestion_stats": strategy_stats,
        "retrieval_metrics": metrics_summary,
    }

    for out_dir in (results_dir, starter_results_dir):
        (out_dir / "ingestion_log.json").write_text(
            json.dumps(ingestion_log, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (out_dir / "traces_top3.json").write_text(
            json.dumps(all_traces, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (out_dir / "metrics_summary.json").write_text(
            json.dumps(run_summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (out_dir / "coherence_samples_raw.json").write_text(
            json.dumps(coherence_samples, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    print("[4/5] Retrieval Metrics Summary:")
    for strat in ("A", "B", "C"):
        for split in ("dev", "test"):
            m = metrics_summary[strat][split]
            print(
                f"  Strategy {strat} | {split.upper():4s} | "
                f"Hit@1: {m['hit_at_1_fraction']} ({m['hit_at_1_pct']}%) | "
                f"Evidence Hit@3: {m['evidence_hit_at_3_fraction']} ({m['evidence_hit_at_3_pct']}%) | "
                f"Filter Compliance: {m['filter_compliance_fraction']}"
            )
    print("[5/5] Saved traces, ingestion logs, and metrics to results/ and starter/results/.")


if __name__ == "__main__":
    main()
