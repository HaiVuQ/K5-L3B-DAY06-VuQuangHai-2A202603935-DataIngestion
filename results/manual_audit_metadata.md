# Manual Audit — Criterion 3: Metadata Completeness & Filter Compliance (`q16` – `q20`)

- **Audit Scope**: All `5 test questions (q16–q20) × top-3 = 15 retrieved records` per strategy (45 records total), cross-checked directly against the original PDF files in `data/raw/`.
- **Metadata Fields Checked**: `source`, `document_id`, `page`, `year`, `task_domain`, and `section`.

## Summary by Strategy

| Strategy | Core Citation (`source`, `page`) | Filter Metadata (`year`, `task_domain`) | Section Header (`section`) | Overall Metadata Accuracy (All Stored Fields) | Test Filter Compliance (`q18`, `q20`) | Dev Filter Compliance (`q12`–`q14`) |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | **15/15** (`100.0%`) | **15/15** (`100.0%`) | `0/15` (`0.0%`, not extracted in fixed-size baseline) | **15/15** (`100.0%` of baseline schema) | **2/2** (`100.0%`, 6/6 records) | **3/3** (`100.0%`, 9/9 records) |
| **B** | **15/15** (`100.0%`) | **15/15** (`100.0%`) | **13/15** (`86.7%`) | **13/15** (`86.7%` strict w/ `section`) / **15/15** (`100.0%` core+filter) | **2/2** (`100.0%`, 6/6 records) | **3/3** (`100.0%`, 9/9 records) |
| **C** | **15/15** (`100.0%`) | **15/15** (`100.0%`) | **13/15** (`86.7%`) | **13/15** (`86.7%` strict w/ `section`) / **15/15** (`100.0%` core+filter) | **2/2** (`100.0%`, 6/6 records) | **3/3** (`100.0%`, 9/9 records) |

## Detailed Audit of 15 Retrieved Test Records (Strategy B & C)

| Question | Rank | Chunk ID | `source` | `page` | `year` | `task_domain` | `section` | Filter Compliant | Audit Verification vs. PDF |
| --- | :---: | --- | --- | :---: | :---: | --- | --- | :---: | --- |
| `q16` | 1 | `C:gooaq-2021:p08:c003` | `data/raw/gooaq_2021.pdf` | 8 | 2021 | `question_answering` | `Table 2: Error distribution for the two models` | N/A | `source`/`page`/`year`/`task_domain` OK. **Section defect**: paragraph is in Section `5.3 Extrinsic Utility of GOOAQ`, but inherited `Table 2` caption from top of page 8. |
| `q16` | 2 | `C:gooaq-2021:p08:c002` | `data/raw/gooaq_2021.pdf` | 8 | 2021 | `question_answering` | `Table 2: Error distribution for the two models` | N/A | `source`/`page`/`year`/`task_domain` OK. **Section defect**: spans end of Table 2 analysis and Section `5.3` + Table 3, labeled only with `Table 2`. |
| `q16` | 3 | `C:gooaq-2021:p07:c006` | `data/raw/gooaq_2021.pdf` | 7 | 2021 | `question_answering` | `5.2 G OOAQ as a challenge for LMs` | N/A | **OK** (All fields match `gooaq_2021.pdf` p. 7). |
| `q17` | 1 | `C:paq-2021:p08:c001` | `data/raw/paq_2021.pdf` | 8 | 2021 | `question_answering` | `Page_Header_or_Body` | N/A | **OK** (Top of p. 8 continuing Section 5.2.2 before Section 5.2.3 heading). |
| `q17` | 2 | `C:paq-2021:p02:c003` | `data/raw/paq_2021.pdf` | 2 | 2021 | `question_answering` | `Page_Header_or_Body` | N/A | **OK** (Continuation of Section 1 on p. 2 before Section 2 heading). |
| `q17` | 3 | `C:paq-2021:p15:c007` | `data/raw/paq_2021.pdf` | 15 | 2021 | `question_answering` | `A.5 Further details on Inference speed` | N/A | **OK** (All fields match `paq_2021.pdf` p. 15). |
| `q18` | 1 | `C:reddit-2019:p02:c001` | `data/raw/reddit_2019.pdf` | 2 | 2019 | `dialogue` | `Page_Header_or_Body` | **Yes** (`2019`, `dialogue`) | **OK** (Matches filter and `reddit_2019.pdf` p. 2). |
| `q18` | 2 | `C:reddit-2019:p03:c003` | `data/raw/reddit_2019.pdf` | 3 | 2019 | `dialogue` | `3.1 Reddit` | **Yes** (`2019`, `dialogue`) | **OK** (Matches filter and Section `3.1 Reddit` on p. 3). |
| `q18` | 3 | `C:reddit-2019:p02:c003` | `data/raw/reddit_2019.pdf` | 2 | 2019 | `dialogue` | `2 Conversational Dataset Format` | **Yes** (`2019`, `dialogue`) | **OK** (Matches filter and Section `2` on p. 2). |
| `q19` | 1 | `C:searchqa-2017:p01:c002` | `data/raw/searchqa_2017.pdf` | 1 | 2017 | `question_answering` | `Abstract` | N/A | **OK** (Matches `searchqa_2017.pdf` p. 1 Abstract). |
| `q19` | 2 | `C:gooaq-2021:p02:c006` | `data/raw/gooaq_2021.pdf` | 2 | 2021 | `question_answering` | `Page_Header_or_Body` | N/A | **OK** (Metadata accurately identifies `gooaq_2021.pdf` p. 2). |
| `q19` | 3 | `C:searchqa-2017:p03:c002` | `data/raw/searchqa_2017.pdf` | 3 | 2017 | `question_answering` | `3 Related Work` | N/A | **OK** (Matches `searchqa_2017.pdf` p. 3 Section 3). |
| `q20` | 1 | `C:wikihow-2018:p04:c005` | `data/raw/wikihow_2018.pdf` | 4 | 2018 | `summarization` | `5.2 Results` | **Yes** (`2018`, `summarization`) | **OK** (Matches filter and Section `5.2 Results` on p. 4). |
| `q20` | 2 | `C:wikihow-2018:p04:c001` | `data/raw/wikihow_2018.pdf` | 4 | 2018 | `summarization` | `Page_Header_or_Body` | **Yes** (`2018`, `summarization`) | **OK** (Matches filter and top-of-page Table 2/Table 3 block on p. 4). |
| `q20` | 3 | `C:wikihow-2018:p02:c005` | `data/raw/wikihow_2018.pdf` | 2 | 2018 | `summarization` | `3 WikiHow Dataset` | **Yes** (`2018`, `summarization`) | **OK** (Matches filter and Section `3 WikiHow Dataset` on p. 2). |

## Value & Limitation Analysis

1. **How Metadata Helps Scoping (`B` vs. `C`)**:
   - Attaching `year` and `task_domain` to every chunk allows Strategy C to enforce strict pre-filtering in Qdrant (`FieldCondition` on `year` and `task_domain`).
   - For `q18` (`year=2019`, `task_domain="dialogue"`), the vector search scope shrinks from `232` chunks to `37` chunks (`-84.1%`). For `q20` (`year=2018`, `task_domain="summarization"`), it shrinks from `232` chunks to `23` chunks (`-90.1%`), guaranteeing zero false-positive chunks from other papers that also mention `CNN/DailyMail` (such as `searchqa-2017`) or `Reddit` (such as ELI5 in `gooaq-2021`).
2. **Concrete Limitation Observed**:
   - Page-local regex detection of `section` headers in `by_paragraph` chunking has two limitations:
     1. **Floating Table/Figure Captions**: When a table caption (`Table 2: Error distribution...` on `gooaq-2021` page 8) matches the header pattern, subsequent paragraphs in the second column (`C:gooaq-2021:p08:c003`) can inherit the table caption as their `section` attribute if the section header (`5.3 Extrinsic Utility of GOOAQ`) was merged inside an earlier multi-paragraph chunk (`p08:c002`).
     2. **Cross-Page Section Continuity**: Because `chunk_by_paragraph` resets `current_section = "Page_Header_or_Body"` at the start of each page, chunks appearing at the top of a page before a new heading (`6/15` test records) receive `"Page_Header_or_Body"` rather than carrying forward the active section title from the previous page.
