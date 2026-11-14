"""Real embedding provider using local sentence-transformers/all-MiniLM-L6-v2."""
from typing import Protocol


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class MyEmbedder:
    """Real local embedding adapter for sentence-transformers/all-MiniLM-L6-v2.

    Uses FastEmbed (ONNX Runtime) or SentenceTransformers to compute 384-dimensional
    L2-normalized embeddings locally. Never falls back to random/mock vectors.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        if not model_name:
            raise ValueError("model_name must be provided")
        self.model_name = model_name
        self._backend = None
        self._engine = ""

        try:
            from fastembed import TextEmbedding
            self._backend = TextEmbedding(model_name=self.model_name)
            self._engine = "fastembed-onnx"
        except Exception as exc_fastembed:
            try:
                from sentence_transformers import SentenceTransformer
                self._backend = SentenceTransformer(self.model_name)
                self._engine = "sentence-transformers"
            except Exception as exc_st:
                raise RuntimeError(
                    f"Failed to initialize real embedding model '{self.model_name}'. "
                    f"FastEmbed error: {exc_fastembed}; SentenceTransformers error: {exc_st}"
                ) from exc_st

        probe = self.embed_query("dimension check probe")
        self.dimensions = len(probe)
        if self.dimensions <= 0:
            raise RuntimeError("Embedding model returned empty vector")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._engine == "fastembed-onnx":
            vecs = list(self._backend.embed(texts))
            return [[float(x) for x in v] for v in vecs]
        vecs = self._backend.encode(texts, normalize_embeddings=True)
        return [[float(x) for x in v] for v in vecs]

    def embed_query(self, question: str) -> list[float]:
        if not question or not question.strip():
            raise ValueError("Query question must be non-empty")
        if self._engine == "fastembed-onnx":
            vec = next(iter(self._backend.query_embed(question)))
            return [float(x) for x in vec]
        vec = self._backend.encode([question], normalize_embeddings=True)[0]
        return [float(x) for x in vec]
