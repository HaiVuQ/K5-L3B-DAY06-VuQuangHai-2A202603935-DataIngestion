"""Evaluate retrieved evidence and preserve per-query traces."""
import re
from typing import Any


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def _chunk_matches_evidence(chunk_text: str, evidence_quote: str) -> tuple[bool, bool, float]:
    """Check whether chunk_text contains full or partial evidence_quote.

    Returns (is_full_hit, is_partial_fragment, token_coverage).
    """
    norm_chunk = _flat(chunk_text)
    norm_quote = _flat(evidence_quote)
    if not norm_quote:
        return False, False, 0.0

    if norm_quote in norm_chunk:
        return True, False, 1.0

    # Check if key clauses/lines of the evidence quote are all present
    quote_lines = [ _flat(ln) for ln in evidence_quote.splitlines() if len(_flat(ln)) >= 12 ]
    if quote_lines and all(ln in norm_chunk for ln in quote_lines):
        return True, False, 1.0

    # Check token/shingle overlap to detect split evidence across chunks
    words = [w for w in re.findall(r"[a-z0-9.]+", norm_quote) if len(w) >= 2]
    if not words:
        return False, False, 0.0
    matched = sum(1 for w in words if w in norm_chunk)
    ratio = matched / len(words)

    # Consider >= 85% substantive token presence on the exact gold page as full hit
    # when a single long quote was slightly wrapped, and 40%-84% as partial split evidence.
    if ratio >= 0.85:
        return True, False, round(ratio, 3)
    if ratio >= 0.40:
        return False, True, round(ratio, 3)
    return False, False, round(ratio, 3)


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    """Check source/page and enough gold evidence; keep hit@1 and hit@3 trace.

    Accept any documented alternative gold evidence. Do not infer human grounding
    or chunk coherence labels from exact string match.
    """
    gold_candidates = [
        {
            "gold_source_id": question["gold_source_id"],
            "gold_page": int(question["gold_page"]),
            "evidence_quote": question["evidence_quote"],
        }
    ]
    for alt in question.get("alternative_gold", []) or []:
        gold_candidates.append(
            {
                "gold_source_id": alt["gold_source_id"],
                "gold_page": int(alt["gold_page"]),
                "evidence_quote": alt["evidence_quote"],
            }
        )

    q_filter = question.get("filter")
    annotated_hits: list[dict[str, Any]] = []
    partial_on_gold_page = 0

    for h in hits[:3]:
        meta = h.get("metadata", {})
        doc_id = meta.get("document_id")
        page_no = int(meta.get("page", -1))
        text = h.get("text", "")

        is_source_page_match = False
        is_evidence_hit = False
        is_partial_evidence = False
        best_cov = 0.0
        matched_gold_info = None

        for cand in gold_candidates:
            if doc_id == cand["gold_source_id"] and page_no == cand["gold_page"]:
                is_source_page_match = True
                full_ok, part_ok, cov = _chunk_matches_evidence(text, cand["evidence_quote"])
                if cov > best_cov:
                    best_cov = cov
                if full_ok:
                    is_evidence_hit = True
                    matched_gold_info = f"{cand['gold_source_id']}:p{cand['gold_page']:02d}"
                    break
                if part_ok:
                    is_partial_evidence = True

        if is_partial_evidence and not is_evidence_hit:
            partial_on_gold_page += 1

        filter_compliant = None
        if q_filter:
            filter_compliant = all(meta.get(fk) == fv for fk, fv in q_filter.items())

        annotated_hits.append(
            {
                **h,
                "source_page_match": is_source_page_match,
                "evidence_hit": is_evidence_hit,
                "partial_evidence_on_gold_page": is_partial_evidence and not is_evidence_hit,
                "evidence_token_coverage_on_gold_page": best_cov,
                "matched_gold": matched_gold_info,
                "filter_compliant": filter_compliant,
            }
        )

    hit_at_1 = bool(annotated_hits and annotated_hits[0]["evidence_hit"])
    hit_at_3 = any(item["evidence_hit"] for item in annotated_hits[:3])
    page_hit_at_3 = any(item["source_page_match"] for item in annotated_hits[:3])
    evidence_split_across_chunks = (not hit_at_3) and (partial_on_gold_page >= 1)

    filter_top3_compliant = None
    if q_filter:
        filter_top3_compliant = bool(annotated_hits) and all(
            bool(item["filter_compliant"]) for item in annotated_hits[:3]
        )

    return {
        "question_id": question["id"],
        "split": question["split"],
        "question_type": question.get("type", "general"),
        "question": question["question"],
        "expected_answer": question["expected_answer"],
        "gold_source_id": question["gold_source_id"],
        "gold_page": int(question["gold_page"]),
        "evidence_quote": question["evidence_quote"],
        "alternative_gold": question.get("alternative_gold", []),
        "filter": q_filter,
        "hit_at_1": hit_at_1,
        "evidence_hit_at_3": hit_at_3,
        "gold_page_retrieved_in_top3": page_hit_at_3,
        "evidence_split_error": evidence_split_across_chunks,
        "filter_top3_compliant": filter_top3_compliant,
        "top_3_hits": annotated_hits,
    }


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Hit@1 and Evidence Hit@3 by strategy and dev/test split."""
    by_group: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for tr in traces:
        strat = tr.get("strategy", "unknown")
        split = tr.get("split", "unknown")
        by_group.setdefault((strat, split), []).append(tr)

    summary: dict[str, Any] = {}
    for (strat, split), items in sorted(by_group.items()):
        total = len(items)
        h1 = sum(1 for x in items if x["hit_at_1"])
        h3 = sum(1 for x in items if x["evidence_hit_at_3"])
        p3 = sum(1 for x in items if x.get("gold_page_retrieved_in_top3"))
        split_err = sum(1 for x in items if x.get("evidence_split_error"))

        filter_items = [x for x in items if x.get("filter")]
        f_total = len(filter_items)
        f_ok = sum(1 for x in filter_items if x.get("filter_top3_compliant"))

        summary.setdefault(strat, {})[split] = {
            "total_questions": total,
            "hit_at_1_count": h1,
            "hit_at_1_fraction": f"{h1}/{total}",
            "hit_at_1_pct": round(100.0 * h1 / total, 2) if total else 0.0,
            "evidence_hit_at_3_count": h3,
            "evidence_hit_at_3_fraction": f"{h3}/{total}",
            "evidence_hit_at_3_pct": round(100.0 * h3 / total, 2) if total else 0.0,
            "gold_page_hit_at_3_fraction": f"{p3}/{total}",
            "evidence_split_errors": split_err,
            "filter_questions_count": f_total,
            "filter_compliance_fraction": f"{f_ok}/{f_total}" if f_total > 0 else "N/A",
            "filter_compliance_pct": round(100.0 * f_ok / f_total, 2) if f_total > 0 else None,
        }

    return summary
