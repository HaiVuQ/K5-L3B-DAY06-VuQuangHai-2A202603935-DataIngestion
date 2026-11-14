# Manual Audit — Criterion 2: Chunk Coherence (`coh_01` – `coh_10`)

- **Scale**:
  - `0`: Cut mid-thought, missing subject/context, or jumbles unrelated layout blocks so the main idea cannot be understood standalone.
  - `1`: Understandable main topic, but starts/ends mid-sentence or lacks surrounding context.
  - `2`: Self-contained, grammatical, and preserves complete paragraph/section boundaries.
- **Sampling Protocol**: 10 fixed midpoint character positions (`coh_01` to `coh_10`) pre-selected across corpus pages before comparing strategies (`results/coherence_samples_raw.json`).

## Summary by Strategy

| Strategy | Chunking Method | Score `0` | Score `1` | Score `2` | Total (`/20`) | Average (`/2.0`) |
| --- | --- | :---: | :---: | :---: | :---: | :---: |
| **A** | `fixed_size` (`size=500`, `overlap=50`) | 3 | 7 | 0 | 7 / 20 | **0.70 / 2.00** |
| **B** | `by_paragraph` (`max_chars=1000`) | 0 | 3 | 7 | 17 / 20 | **1.70 / 2.00** |
| **C** | `by_paragraph` (`max_chars=1000` + metadata filter) | 0 | 3 | 7 | 17 / 20 | **1.70 / 2.00** |

## Per-Sample Scoring Table

| Sample ID | Page ID | Anchor Char | Strategy A (`chunk_id` / Score) | Strategy B (`chunk_id` / Score) | Strategy C (`chunk_id` / Score) | Audit Rationale |
| --- | --- | :---: | --- | --- | --- | --- |
| `coh_01` | `gooaq-2021:p01` | 2104 | `A:gooaq-2021:p01:c005` (**1**) | `B:gooaq-2021:p01:c003` (**1**) | `C:gooaq-2021:p01:c003` (**1**) | **A** starts mid-sentence (`or direct answer QA)...`) and ends at a comma (`short responses and,`). **B/C** keep complete sentences and the `1 Introduction` header, but the last sentence is split by page-bottom footnote 1. |
| `coh_02` | `gooaq-2021:p02` | 2555 | `A:gooaq-2021:p02:c006` (**1**) | `B:gooaq-2021:p02:c004` (**2**) | `C:gooaq-2021:p02:c004` (**2**) | **A** starts mid-word (`wer types:`) and cuts off mid-word (`because response flu`). **B/C** capture all three research questions `(Q1)-(Q3)` and the full hypothesis for `(Q1)`. |
| `coh_03` | `gooaq-2021:p03` | 2342 | `A:gooaq-2021:p03:c006` (**1**) | `B:gooaq-2021:p03:c005` (**2**) | `C:gooaq-2021:p03:c005` (**2**) | **A** cuts off at `in order to discover longe`, losing the 5-token filter rule and 5M question count. **B/C** capture the entire `3.1.1 Query Extraction` subsection intact. |
| `coh_04` | `gooaq-2021:p04` | 2057 | `A:gooaq-2021:p04:c005` (**1**) | `B:gooaq-2021:p04:c004` (**2**) | `C:gooaq-2021:p04:c004` (**2**) | **A** starts mid-sentence (`rating of the answer quality...`) and ends at a dangling header `3.3 Dataset`. **B/C** preserve two complete paragraphs (`Assessment results.` and `3.3 Dataset Analysis`). |
| `coh_05` | `gooaq-2021:p05` | 2135 | `A:gooaq-2021:p05:c005` (**0**) | `B:gooaq-2021:p05:c004` (**1**) | `C:gooaq-2021:p05:c004` (**1**) | **A** starts mid-word (`s, (Tsnippet)...`), jumps mid-clause into footnote 5, and cuts off before finishing the footnote. **B/C** start cleanly at `4.1 Problem Setup` and finish footnote 5, though interrupted mid-clause by two-column footnote placement. |
| `coh_06` | `gooaq-2021:p06` | 1859 | `A:gooaq-2021:p06:c005` (**1**) | `B:gooaq-2021:p06:c003` (**2**) | `C:gooaq-2021:p06:c003` (**2**) | **A** starts with `ble.` and merges the Figure 5 text box with a truncated caption (`similar temp`). **B/C** cleanly isolate the comparative answer block inside Figure 5. |
| `coh_07` | `gooaq-2021:p07` | 2299 | `A:gooaq-2021:p07:c006` (**0**) | `B:gooaq-2021:p07:c004` (**2**) | `C:gooaq-2021:p07:c004` (**2**) | **A** starts with fragment `r than 10% of the cases.` and cuts off at `where even 200k labeled`, omitting the predicate of the sentence. **B/C** keep the entire `(Q2)` analysis paragraph to its period. |
| `coh_08` | `gooaq-2021:p08` | 2098 | `A:gooaq-2021:p08:c005` (**1**) | `B:gooaq-2021:p08:c003` (**2**) | `C:gooaq-2021:p08:c003` (**2**) | **A** starts with `ong-answer dataset.` and cuts off at `evaluated on GOOAQ r`. **B/C** preserve both paragraphs comparing Table 3 and Table 4 results. |
| `coh_09` | `gooaq-2021:p09` | 2213 | `A:gooaq-2021:p09:c005` (**1**) | `B:gooaq-2021:p09:c004` (**2**) | `C:gooaq-2021:p09:c004` (**2**) | **A** starts with `on of models...` and bleeds into `Acknowledgement / The authors would lik`. **B/C** isolate the exact concluding paragraph of Section 6. |
| `coh_10` | `gooaq-2021:p11` | 1570 | `A:gooaq-2021:p11:c004` (**0**) | `B:gooaq-2021:p11:c002` (**1**) | `C:gooaq-2021:p11:c002` (**1**) | **A** starts mid-sentence, merges Appendix C prose with footnote 8 and Figure 6 table rows, and cuts off at `what is the differe`. **B/C** preserve the full `C Invalid Questions and Answers` paragraph. |
