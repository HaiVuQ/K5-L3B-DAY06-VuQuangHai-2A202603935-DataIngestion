"""Implement fixed-size and structure-aware chunking."""
import re
from .models import Chunk, DocumentPage

SECTION_HEADING_RE = re.compile(
    r"^(?:Abstract|Introduction|Conclusion|Conclusions|Acknowledgments|Acknowledgement|"
    r"[1-9](?:\.[1-9])*\.?\s+[A-Z][A-Za-z0-9\s\-:,/()&]+|"
    r"[A-E](?:\.[1-9])?\s+[A-Z][A-Za-z0-9\s\-:,/()&]+|"
    r"Table\s+\d+:.*|Figure\s+\d+:.*)$"
)


def _detect_section(lines: list[str], current_section: str) -> str:
    for line in lines:
        s = line.strip()
        if 3 <= len(s) <= 85 and SECTION_HEADING_RE.match(s):
            return s[:80]
    return current_section


def fixed_size(page: DocumentPage, size: int = 500, overlap: int = 50) -> list[Chunk]:
    """Split text into overlapping character windows and retain page metadata."""
    if size <= 0:
        raise ValueError("size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be >= 0 and < size")

    text = page.text
    if not text:
        return []

    chunks: list[Chunk] = []
    step = size - overlap
    start = 0
    idx = 0
    n = len(text)

    while start < n:
        end = min(start + size, n)
        window = text[start:end].strip()
        if window:
            idx += 1
            chunk_id = f"A:{page.document_id}:p{page.page:02d}:c{idx:03d}"
            meta = {
                **page.metadata,
                "document_id": page.document_id,
                "source": page.source,
                "page": page.page,
                "chunk_index": idx,
                "char_start": start,
                "char_end": end,
                "char_length": len(window),
                "chunking_method": f"fixed_size_{size}_{overlap}",
            }
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=page.document_id,
                    source=page.source,
                    page=page.page,
                    text=window,
                    metadata=meta,
                )
            )
        if end >= n:
            break
        start += step

    return chunks


def _split_into_semantic_blocks(text: str) -> list[str]:
    """Split normalized page text into coherent blocks (sections, paragraphs, tables)."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    blocks: list[str] = []
    cur: list[str] = []

    for line in lines:
        is_heading = bool(3 <= len(line) <= 85 and SECTION_HEADING_RE.match(line))
        prev_ended_sentence = bool(cur and cur[-1].endswith((".", "?", "!", ":", "]")))
        cur_len = sum(len(x) + 1 for x in cur)

        if is_heading and cur:
            blocks.append("\n".join(cur).strip())
            cur = [line]
        elif prev_ended_sentence and cur_len >= 280:
            blocks.append("\n".join(cur).strip())
            cur = [line]
        else:
            cur.append(line)

    if cur:
        blocks.append("\n".join(cur).strip())

    return [b for b in blocks if b]


def _split_oversized_block(block: str, max_size: int) -> list[str]:
    """Split a block exceeding max_size along sentence boundaries, then words if needed."""
    if len(block) <= max_size:
        return [block]

    sentences = re.split(r"(?<=[.?!])\s+", block)
    sub_blocks: list[str] = []
    current = ""

    for sent in sentences:
        if not sent:
            continue
        candidate = f"{current} {sent}".strip() if current else sent
        if len(candidate) <= max_size:
            current = candidate
        else:
            if current:
                sub_blocks.append(current)
            if len(sent) <= max_size:
                current = sent
            else:
                # Hard split oversized sentence by words
                words = sent.split(" ")
                w_cur = ""
                for w in words:
                    w_cand = f"{w_cur} {w}".strip() if w_cur else w
                    if len(w_cand) <= max_size:
                        w_cur = w_cand
                    else:
                        if w_cur:
                            sub_blocks.append(w_cur)
                        w_cur = w[:max_size]
                current = w_cur

    if current:
        sub_blocks.append(current)

    return [sb for sb in sub_blocks if sb]


def by_paragraph(page: DocumentPage, max_size: int = 1000, strategy_label: str = "B") -> list[Chunk]:
    """Group paragraphs/sections, split oversized paragraphs, and retain metadata."""
    if max_size <= 0:
        raise ValueError("max_size must be positive")

    text = page.text
    if not text:
        return []

    raw_blocks = _split_into_semantic_blocks(text)
    expanded_blocks: list[str] = []
    for b in raw_blocks:
        expanded_blocks.extend(_split_oversized_block(b, max_size))

    merged_texts: list[str] = []
    cur_text = ""
    for b in expanded_blocks:
        candidate = f"{cur_text}\n\n{b}".strip() if cur_text else b
        if len(candidate) <= max_size:
            cur_text = candidate
        else:
            if cur_text:
                merged_texts.append(cur_text)
            cur_text = b
    if cur_text:
        merged_texts.append(cur_text)

    chunks: list[Chunk] = []
    current_section = "Page_Header_or_Body"
    for idx, chunk_text in enumerate(merged_texts, start=1):
        current_section = _detect_section(chunk_text.splitlines(), current_section)
        chunk_id = f"{strategy_label}:{page.document_id}:p{page.page:02d}:c{idx:03d}"
        meta = {
            **page.metadata,
            "document_id": page.document_id,
            "source": page.source,
            "page": page.page,
            "section": current_section,
            "chunk_index": idx,
            "char_length": len(chunk_text),
            "chunking_method": f"by_paragraph_max_{max_size}",
        }
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=chunk_text,
                metadata=meta,
            )
        )

    return chunks
