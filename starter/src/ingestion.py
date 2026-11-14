"""Read and normalize source data."""
import re
import unicodedata
from pathlib import Path
from typing import Any
import pypdf

from .models import DocumentPage


def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace without discarding useful structure."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = "".join(
        ch for ch in text
        if ch in ("\n", "\t") or (ord(ch) >= 32 and ord(ch) != 127)
    )
    # Rejoin hyphenated line breaks across column wraps (e.g., "an-\nswer" -> "answer")
    text = re.sub(r"([A-Za-z])-\s*\n\s*([a-z])", r"\1\2", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_pdf(
    path: Path,
    document_id: str,
    source: str,
    doc_metadata: dict[str, Any] | None = None,
    valid_pages: list[int] | None = None,
    exclusion_reasons: dict[str, str] | None = None,
    ingestion_log: list[dict[str, Any]] | None = None,
) -> list[DocumentPage]:
    """Extract each physical page; keep its page number and source.

    Detect and record pages with no text or garbled control characters, and filter
    out non-content pages (e.g., references-only pages) documented in the manifest.
    """
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    reader = pypdf.PdfReader(str(path))
    pages: list[DocumentPage] = []
    base_meta = dict(doc_metadata or {})
    excl_reasons = exclusion_reasons or {}

    for idx, pdf_page in enumerate(reader.pages, start=1):
        raw_text = pdf_page.extract_text() or ""
        ctrl_count = sum(1 for ch in raw_text if ord(ch) < 32 and ch not in "\n\r\t")
        norm_text = normalize_text(raw_text)

        log_entry: dict[str, Any] = {
            "document_id": document_id,
            "source": source,
            "page": idx,
            "raw_char_count": len(raw_text),
            "normalized_char_count": len(norm_text),
            "control_char_count": ctrl_count,
            "status": "included",
            "notes": "",
        }

        if not norm_text:
            log_entry["status"] = "excluded_empty"
            log_entry["notes"] = "Empty page after text extraction and normalization"
            if ingestion_log is not None:
                ingestion_log.append(log_entry)
            continue

        if valid_pages is not None and idx not in valid_pages:
            reason = excl_reasons.get(str(idx), "Excluded per manifest page counting rule")
            log_entry["status"] = "excluded_non_content"
            log_entry["notes"] = reason
            if ingestion_log is not None:
                ingestion_log.append(log_entry)
            continue

        if ctrl_count > 10:
            log_entry["notes"] = (
                f"Removed {ctrl_count} non-printable PDF figure/font control characters; body text retained."
            )

        if ingestion_log is not None:
            ingestion_log.append(log_entry)

        page_meta = {
            **base_meta,
            "document_id": document_id,
            "source": source,
            "page": idx,
            "page_id": f"{document_id}:p{idx:02d}",
            "char_count": len(norm_text),
        }
        pages.append(
            DocumentPage(
                document_id=document_id,
                source=source,
                page=idx,
                text=norm_text,
                metadata=page_meta,
            )
        )

    return pages
