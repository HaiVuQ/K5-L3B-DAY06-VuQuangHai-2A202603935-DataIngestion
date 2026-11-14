# Manual Audit — Criterion 5: Downstream Grounding Quality (`q16` – `q20`)

- **Scale**:
  - `0`: Top-3 retrieved chunks contain no relevant evidence to answer the question.
  - `1`: Top-3 retrieved chunks contain partial context (e.g., rounded overview numbers or qualitative explanation) but miss required conditions, exceptions, or exact table figures.
  - `2`: Top-3 retrieved chunks contain sufficient, complete evidence to answer the question accurately and cite `source + page`.

## Summary by Strategy

| Strategy | Score `0` | Score `1` | Score `2` | Total (`/10`) | Average (`/2.0`) |
| --- | :---: | :---: | :---: | :---: | :---: |
| **A** (`fixed_size_500_50`) | 1 | 2 | 2 | 6 / 10 | **1.20 / 2.00** |
| **B** (`by_paragraph_max_1000`, no filter) | 1 | 1 | 3 | 7 / 10 | **1.40 / 2.00** |
| **C** (`by_paragraph_max_1000` + metadata filter) | 1 | 1 | 3 | 7 / 10 | **1.40 / 2.00** |

## Per-Question Grounding Audit (`q16` – `q20`)

| Question ID | Type | Strategy A Score & Top-3 Chunks | Strategy B Score & Top-3 Chunks | Strategy C Score & Top-3 Chunks | Grounding Comparison & Audit Notes |
| --- | --- | --- | --- | --- | --- |
| `q16` | `direct` | **2** (`A:gooaq-2021:p08:c005`, `p07:c009`, `p08:c006`) | **2** (`B:gooaq-2021:p08:c003`, `p08:c002`, `p07:c006`) | **2** (`C:gooaq-2021:p08:c003`, `p08:c002`, `p07:c006`) | **A** retrieves the prose summary of Table 3 (`21.8` and `22.9` vs `19.0` and `22.7`). **B/C** retrieve both the prose summary (`p08:c003`) at Rank 1 and the raw Table 3 (`p08:c002`, showing `21.7` and `22.9`) at Rank 2. |
| `q17` | `paraphrase` | **2** (`A:paq-2021:p08:c002`, `p08:c001`, `p02:c004`) | **2** (`B:paq-2021:p08:c001`, `p02:c003`, `p15:c007`) | **2** (`C:paq-2021:p08:c001`, `p02:c003`, `p15:c007`) | All three strategies retrieve both gold locations (`paq-2021:p08` and `paq-2021:p02`) stating that RePAQ won the `500MB` and `Smallest System` tracks with disk images of `336MB` and `29MB`. |
| `q18` | `metadata_filter` | **1** (`A:reddit-2019:p02:c001`, `p03:c005`, `p01:c006`) | **1** (`B:reddit-2019:p02:c001`, `p03:c003`, `p02:c003`) | **1** (`C:reddit-2019:p02:c001`, `p03:c003`, `p02:c003`) | All three strategies retrieve the rounded figures on p. 2/p. 3 (`3.7B comments`, `256M conversational threads`, `727M valid context-response pairs`), which partially answers the question (`1`), but miss the p. 3 paragraph containing the exact integers (`3,680,746,776`, `256,095,216`, `727,013,715`) and the `2015 to 2018` span. |
| `q19` | `condition_exception` | **0** (`A:searchqa-2017:p02:c009`, `gooaq-2021:p07:c011`, `p02:c009`) | **0** (`B:searchqa-2017:p01:c002`, `gooaq-2021:p02:c006`, `searchqa-2017:p03:c002`) | **0** (`C:searchqa-2017:p01:c002`, `gooaq-2021:p02:c006`, `searchqa-2017:p03:c002`) | Dense semantic search matches high-level "SearchQA snippet" descriptions (Abstract/Related Work/Splits) rather than the specific exclusion paragraph (`air-date`, `"Jeopardy!"`, `"quiz"`, `"trivia"`, `three or less words long`) on `searchqa-2017` p. 2. |
| `q20` | `metadata_filter` | **1** (`A:wikihow-2018:p04:c008`, `p04:c007`, `p02:c008`) | **2** (`B:wikihow-2018:p04:c005`, `p04:c001`, `p02:c005`) | **2** (`C:wikihow-2018:p04:c005`, `p04:c001`, `p02:c005`) | **Key A vs. B/C differentiator**: Strategy **A** explains the Inverted Pyramid style vs. WikiHow steps (Ranks 1 & 3), but misses Table 2 (`Pointer-generator + coverage = 26.54` ROUGE-L) because page 4 was fragmented into 9 small chunks. Strategies **B & C** retrieve both the Inverted Pyramid explanation (Ranks 1 & 3) and Table 2 (`p04:c001`, Rank 2), earning a full **2/2**. |
