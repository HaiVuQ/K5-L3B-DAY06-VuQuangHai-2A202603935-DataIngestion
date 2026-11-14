# Báo cáo cá nhân — Day 6: Data Ingestion Engineering

- **Họ và tên**: Vũ Quang Hải
- **MSSV**: `2A202603935`
- **Lớp**: `L3B`
- **Repository**: `https://github.com/HaiVuQ/K5-L3B-DAY06-VuQuangHai-2A202603935-DataIngestion.git`

---

## Dữ liệu và pipeline

- **Chủ đề, nguồn/quyền, số trang và quy tắc tính trang**:
  - **Chủ đề**: Các bộ dữ liệu huấn luyện (Question Answering, Conversational Dialogue, Text Summarization) được trích dẫn trực tiếp trong bảng *Training Datasets* của thẻ mô hình `sentence-transformers/all-MiniLM-L6-v2` trên Hugging Face (`https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2`).
  - **Nguồn và giấy phép** (chi tiết trong `data/manifest.json`):
    1. `gooaq-2021` (`data/raw/gooaq_2021.pdf`): *GOOAQ: Open Question Answering with Diverse Answer Types* (Khashabi et al., NAACL 2021, `arXiv:2104.08727v2`, Apache-2.0 / arXiv non-exclusive license) — 13 trang vật lý, **12 trang hợp lệ** (bỏ trang 10 chỉ chứa References; trang 11–13 là Appendix A–D).
    2. `paq-2021` (`data/raw/paq_2021.pdf`): *PAQ: 65 Million Probably-Asked Questions and What You Can Do With Them* (Lewis et al., TACL 2021, `arXiv:2102.07033v1`, CC-BY-NC 4.0 / MIT) — 16 trang vật lý, **13 trang hợp lệ** (bỏ các trang 11, 12, 13 chỉ chứa References; trang 14–16 là Appendix A).
    3. `reddit-2019` (`data/raw/reddit_2019.pdf`): *A Repository of Conversational Datasets* (Henderson et al., 2019, `arXiv:1904.06472v2`) — 10 trang vật lý, **7 trang hợp lệ** (bỏ các trang 7, 8, 9 chỉ chứa References; trang 10 là Appendix A).
    4. `searchqa-2017` (`data/raw/searchqa_2017.pdf`): *SearchQA: A New Q&A Dataset Augmented with Context from a Search Engine* (Dunn et al., 2017, `arXiv:1704.05179v3`) — 5 trang vật lý, **4 trang hợp lệ** (bỏ trang 5 chỉ chứa References).
    5. `wikihow-2018` (`data/raw/wikihow_2018.pdf`): *WikiHow: A Large Scale Text Summarization Dataset* (Koupaee & Wang, 2018, `arXiv:1810.09305v1`) — 5 trang vật lý, **4 trang hợp lệ** (bỏ trang 5 chỉ chứa References).
  - **Quy tắc tính trang** (nhất quán 100% với `page_counting_rule` trong `data/manifest.json` và `STUDENT.md`): Chỉ tính các trang PDF có nội dung học thuật thực sự đạt tối thiểu **`normalized_char_count >= 500` ký tự sau chuẩn hóa** (trên thực tế, trang hợp lệ ngắn nhất trong corpus có `1,495` ký tự) và không nằm trong danh sách `excluded_pages` chỉ chứa tài liệu tham khảo (References). Tổng cộng: **49 trang vật lý -> 40 trang nội dung hợp lệ** (`167,221` ký tự sau chuẩn hóa), vượt ngưỡng yêu cầu tối thiểu `>= 30 trang`.

- **Chuẩn hóa, lỗi và giới hạn**:
  - **Các bước chuẩn hóa văn bản (`starter/src/ingestion.py`)**:
    1. Chuẩn hóa Unicode `NFKC` và thống nhất ký tự xuống dòng `\r\n`, `\r` về `\n`.
    2. Loại bỏ ký tự điều khiển ẩn/lỗi font trích xuất PDF (`[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]`). Nhật ký `results/ingestion_log.json` ghi nhận đã dọn sạch các ký tự điều khiển lỗi encoding toán học trên `gooaq-2021` trang 6 (`60` ký tự bị loại bỏ) và `paq-2021` trang 3 (`45` ký tự bị loại bỏ).
    3. Nối từ bị ngắt gạch ngang cuối dòng trong bố cục 2 cột (`re.sub(r"([A-Za-z])-\s*\n\s*([a-z])", r"\1\2", text)`), khắc phục triệt để lỗi vỡ từ như `an-\nswer` -> `answer` hoặc `token-\noverlap` -> `tokenoverlap`.
    4. Gộp khoảng trắng thừa trên cùng một dòng và thu gọn `>= 3` dòng trống liên tiếp về `\n\n` để bảo toàn ranh giới đoạn văn cho Chiến lược B và C.
  - **Giới hạn**: `pypdf` đọc luồng văn bản tuyến tính theo cột từ PDF 2 cột nên các bảng biểu nổi (floating tables như Table 2, Table 3) hoặc chú thích cuối trang (footnotes) đôi khi xen vào giữa câu chuyển tiếp giữa hai cột.

- **Embedding model/provider/version/số chiều, vector store/version, metric, lệnh chạy và chi phí**:
  - **Embedding model**: `sentence-transformers/all-MiniLM-L6-v2` chạy local hoàn toàn trên CPU thông qua `fastembed==0.2.7` và `onnxruntime==1.23.2` (bản ONNX chính thức từ Hugging Face, **384 chiều**, chuẩn hóa vector đơn vị L2).
  - **Vector store & Metric**:
    - Sử dụng **Qdrant Local persistent storage** (`qdrant-client==1.20.0`, lưu trên đĩa tại `data/qdrant_storage`, collection `day6_chunks`, độ đo `Distance.COSINE`, `exact=True`) do máy chạy Windows không cài Docker Desktop (theo đúng hướng dẫn dự phòng tại `CHECKPOINTS.md` và `docs/README.md`).
    - Đồng thời đã cài đặt đầy đủ lớp `PgVectorStore` (`psycopg[binary]==3.3.8`, toán tử `<=>` cosine distance, `JSONB` metadata filter) trong `starter/src/store.py` và kiểm tra hạ tầng qua `starter/scripts/check_setup.py`.
  - **Tính Idempotent**: Mỗi chunk có khóa định danh tất định `chunk_id = "{strategy}:{document_id}:p{page:02d}:c{idx:03d}"` được băm `uuid5` cố định khi `upsert`. Trong `src/run.py`, mỗi chiến lược được nạp lặp lại 2 lần liên tiếp và xác minh quân số bản ghi không đổi (`A: 390 -> 390`, `B: 232 -> 232`, `C: 232 -> 232`).
  - **Lệnh chạy tái lập**:
    ```powershell
    cd starter
    .\.venv\Scripts\python.exe scripts/check_setup.py
    .\.venv\Scripts\python.exe -m src.run
    ```
  - **Chi phí**: **\$0.00** (100% mô hình mã nguồn mở chạy local trên CPU, không gọi API trả phí).

- **Metadata bắt buộc, trường lọc bổ sung, nguồn giá trị và lý do chọn**:
  - **Metadata bắt buộc**: `document_id`, `source` (đường dẫn file PDF), `title`, `page` (số trang 1-indexed), `page_id`, `chunk_index`, `char_length`, `chunking_method`, `strategy`.
  - **Trường lọc bổ sung**:
    1. `year` (`int`: `2017`, `2018`, `2019`, `2021`) — lấy từ năm công bố chính thức của từng bài báo trong `data/manifest.json`.
    2. `task_domain` (`str`: `"question_answering"`, `"dialogue"`, `"summarization"`) — phân loại tác vụ NLP của từng bộ dữ liệu trong `data/manifest.json`.
    3. `section` (`str`, áp dụng cho B và C) — trích xuất tự động từ tiêu đề mục (`1 Introduction`, `3.1 Reddit`, `5.2 Results`, ...) bằng biểu thức chính quy trong `starter/src/chunking.py`.
  - **Lý do chọn**: Khi truy vấn kho học thuật nhiều bài báo cùng đề cập các tập dữ liệu phổ biến (như `CNN/DailyMail`, `Reddit`, `Natural Questions`), lọc theo `year` và `task_domain` giúp khóa chính xác bài báo mục tiêu trước khi tính điểm tương đồng ngữ nghĩa.

---

## Cấu hình và benchmark

- **A / B / C (tham số cụ thể, khác biệt duy nhất B–C)**:
  - **Chiến lược A (`fixed_size`, không filter)**: Cắt theo cửa sổ ký tự cố định `chunk_size = 500`, `chunk_overlap = 50`, không dùng ranh giới đoạn văn, truy vấn top-3 toàn bộ kho (`filter = None`). Sinh ra **390 chunks** (`mean = 473.4` ký tự, `min = 59`, `max = 500`, `p50 = 500`, `p90 = 500`).
  - **Chiến lược B (`by_paragraph`, không filter)**: Tách theo khối đoạn văn (`\n\n`) và tiêu đề mục (`section`), gộp các đoạn liên tiếp thuộc cùng một mục cho đến ngưỡng `max_chars = 1000` (nếu một đoạn đơn lẻ dài hơn `1000` ký tự thì tách theo câu `. `), gắn thêm trường metadata `section`, truy vấn top-3 toàn bộ kho (`filter = None`). Sinh ra **232 chunks** (`mean = 720.4` ký tự, `min = 112`, `max = 1000`, `p50 = 754`, `p90 = 966`).
  - **Chiến lược C (`by_paragraph` + `metadata_filter`)**: Giữ **nguyên hoàn toàn** thuật toán chunking, kích thước `max_chars = 1000`, bộ 232 chunks và vector embedding của Chiến lược B; **điểm khác biệt duy nhất** giữa B và C là tại bước truy vấn (`evaluation.py`), Chiến lược C truyền điều kiện lọc `{"year": ..., "task_domain": ...}` xuống Qdrant/pgvector đối với các câu hỏi có khai báo `filter`.

- **≥20 câu: phân chia ≥15 dev / ≥5 test, câu metadata filter và cách kiểm chứng evidence**:
  - Bộ câu hỏi chuẩn `benchmark/questions.json` gồm **20 câu hỏi** (`q01`–`q20`), chia thành:
    - **Tập `dev` (`15` câu, `q01`–`q15`)**: Gồm 5 câu trực tiếp (`direct`: `q01`, `q04`, `q07`, `q08`, `q15`), 3 câu diễn giải (`paraphrase`: `q03`, `q06`, `q11`), 4 câu điều kiện/ngoại lệ (`condition_exception`: `q02`, `q05`, `q09`, `q10`) và **3 câu lọc metadata** (`metadata_filter`: `q12` lọc `year=2019, task_domain=dialogue`; `q13` lọc `year=2017, task_domain=question_answering`; `q14` lọc `year=2018, task_domain=summarization`).
    - **Tập `test` (`5` câu, `q16`–`q20`)**: Gồm 1 câu trực tiếp (`q16`), 1 câu diễn giải (`q17`), 1 câu điều kiện/ngoại lệ (`q19`) và **2 câu lọc metadata** (`q18` lọc `year=2019, task_domain=dialogue`; `q20` lọc `year=2018, task_domain=summarization`).
  - **Kiểm chứng `evidence_quote` và lịch sử rà soát/đánh giá lại bộ `test`**:
    - Mọi câu hỏi trong `benchmark/questions.json` đều có `evidence_quote` (cùng `alternative_gold` / `supporting_page_quote` trên đúng trang chuẩn) bao phủ **100% mọi mệnh đề và con số** trong `expected_answer` (bao gồm cả chi tiết bài kiểm tra khoảng nửa tá câu hỏi ở `q03`, điều kiện giữ lại câu trả lời dài tối đa 3 từ ở `q19`, hai câu số liệu bình luận/luồng/TensorFlow examples ở `q18`, và cả bảng điểm ROUGE-L `26.54` lẫn giải thích *inverted pyramid* ở `q20`). Hàm chấm `evaluate_query` trong `starter/src/evaluation.py` kiểm tra đồng thời `source_id`, `page` và độ phủ chuỗi/từ khóa của `evidence_quote` (`>= 85%` token của quote nằm trong chunk trên đúng trang chuẩn); đặc biệt với câu hỏi hai vế như `q20` (có thêm `supporting_page_quote`), `evaluate_query` yêu cầu top-3 trên trang chuẩn phải khớp **cả `evidence_quote` (bảng số liệu) lẫn `supporting_page_quote` (đoạn văn giải thích)** mới được tính `evidence_hit_at_3 = true`.
    - **Ghi chú minh bạch về lịch sử cập nhật nhãn/evidence tập `test`** (`test_split_audit_and_reevaluation_note` trong `benchmark/questions.json`): 20 câu hỏi (`q01`–`q15` dev, `q16`–`q20` test) được tạo lúc `11:12` và chạy qua toàn bộ pipeline nạp/nhúng/truy vấn lúc `15:37:25`. Sau lần chạy đầu, trong bước rà soát độ bao phủ của nhãn chuẩn (cập nhật lúc `16:05` và `23:26`), một số câu (gồm `q03, q04, q08, q12, q14` ở tập `dev` và `q16, q18, q19, q20` ở tập `test`) đã được bổ sung thêm câu trích dẫn vào `evidence_quote` / `supporting_page_quote` và tinh chỉnh `expected_answer` để khớp 100% với văn bản PDF, sau đó chạy lại bước chấm điểm (`evaluate_query` & `summarize`) trên các kết quả top-3 đã truy xuất. Do đó, báo cáo ghi nhận minh bạch rằng **tập `test` cuối cùng đã trải qua bước rà soát/bổ sung `evidence_quote` và đánh giá lại sau lần chạy đầu** (chứ không còn là một tập *blind holdout* hoàn toàn chưa chạm tới sau lần chạy đầu), dù câu hỏi truy vấn (`question`), vector nhúng và thứ tự các chunk trả về trong `traces_top3.json` không hề thay đổi.

- **Tiêu chí chọn chiến lược đã chốt trước khi xem test và giải thích sự thống nhất**:
  - **Quy tắc gốc đã khóa lúc `11:12` trước khi chạy thực nghiệm** (giữ nguyên nguyên văn trong `benchmark/questions.json` tại trường `selection_criteria_locked_before_test`):
    > *"Select the strategy with the highest Dev Evidence Hit@3; break ties using Dev Hit@1, then manual Chunk Coherence score (/2), then Grounding Quality (/2), and finally lower chunk count / ingestion time."*
    > (Ưu tiên chiến lược có `Dev Evidence Hit@3` cao nhất; chỉ khi hòa `Dev Evidence Hit@3` mới xét tiếp đến các tiêu chí phá hòa).
  - **Ghi chú làm rõ về điều khoản phá hòa (tie-break) sau lần chạy đầu** (được ghi minh bạch tại trường `tie_break_clarification_after_initial_run` trong `benchmark/questions.json`):
    - Trong câu mô tả gốc lúc `11:12`, danh sách tie-break có liệt kê `Grounding Quality (/2)` ở vị trí thứ 3. Sau lần chạy đầu, nhóm thực hiện làm rõ về mặt phương pháp luận rằng: vì `Grounding Quality (/2)` được chấm trên tập `test` (`q16`–`q20`), nên nếu xảy ra hòa trên `dev`, quy tắc tie-break hợp lệ trước khi xem `test` chỉ được phép dùng các chỉ số đo trên tập `dev`/corpus (`Dev Hit@1`, `Chunk Coherence (/2)`, `Dev Filter Compliance`, số lượng chunk / thời gian nạp) chứ không bao giờ dùng `test Grounding`.
    - Quan trọng nhất: trên thực tế **không xảy ra hòa ở tiêu chí chính cấp 1 (`Dev Evidence Hit@3`)** vì Chiến lược A đạt `8/15 (53.33%)` vượt lên trên Chiến lược B và C (`6/15 = 40.00%`). Do đó điều khoản tie-break không bao giờ được kích hoạt và **việc làm rõ điều khoản tie-break sau lần chạy đầu hoàn toàn không làm thay đổi lựa chọn Chiến lược A**.
  - **Áp dụng đúng quy tắc đã khóa (Không thay đổi tiêu chí hậu nghiệm)**:
    - Trên tập `dev`, **Chiến lược A đạt `Dev Evidence Hit@3 = 8/15 (53.33%)`** (trúng `q05, q08, q09, q11, q12, q13, q14, q15`), cao hơn **Chiến lược B và C cùng đạt `6/15 (40.00%)`** (trúng `q07, q08, q09, q11, q12, q13`).
    - Do không xảy ra hòa ở tiêu chí cấp 1 (`Dev Evidence Hit@3`), **theo đúng tiêu chí đã khóa trước thực nghiệm, Chiến lược A là chiến lược thắng trên tập `dev` và được chọn làm chiến lược chính thức để đánh giá trên tập `test`**, đạt kết quả trên `test` là **`Test Hit@1 = 2/5 (40.00%)`**, **`Test Evidence Hit@3 = 2/5 (40.00%)`**, **`Grounding = 1.20 / 2.00`**.
  - **Phân tích đối chiếu đa tiêu chí (Tại sao kết quả thực nghiệm cho thấy quy tắc khóa đơn biến bộc lộ hạn chế so với Chiến lược C)**:
    - Mặc dù Chiến lược A thắng theo tiêu chí cấp 1 (`Dev Evidence Hit@3`), kết quả trên chính tập `dev` cho thấy **sự xung đột gay gắt giữa `Dev Evidence Hit@3` và các tiêu chí chất lượng còn lại**: Chiến lược A có **`Dev Hit@1` rất thấp (`1/15 = 6.67%`, chỉ trúng `q13`)** và **điểm mạch lạc `Chunk Coherence` rất kém (`0.70 / 2.00`**, do cắt cố định 500 ký tự làm cụt đầu/cuối câu ở 10/10 mẫu), đồng thời tốn nhiều hơn 68% số chunk (`390` so với `232`) và không có bộ lọc metadata.
    - Ngược lại, ngay trên tập `dev`, **Chiến lược B và C đạt `Dev Hit@1` cao gấp 4 lần (`4/15 = 26.67%` ở `q08, q11, q12, q13`)**, nâng **`Chunk Coherence` lên `1.70 / 2.00`**, giảm `40.5%` số chunk (`232` vs. `390`), giảm `38.6%` thời gian nạp (`194.12s` vs. `316.24s`), và **Chiến lược C đảm bảo `100%` (`3/3` câu dev filter) thu hẹp đúng phạm vi tài liệu theo `year` và `task_domain`**.
    - Khi đối chiếu kết quả tất cả các chiến lược trên tập `test` (được lưu đầy đủ trong `results/metrics_summary.json` và `results/traces_top3.json`), **Chiến lược B và C thực tế đạt `Test Evidence Hit@3 = 3/5 (60.00%)` và `Grounding = 1.40 / 2.00`**, vượt qua Chiến lược A (`2/5 = 40.00%`, `Grounding = 1.20 / 2.00`). Vì vậy, báo cáo giữ nguyên **Chiến lược A là chiến lược được chọn theo đúng tiêu chí khóa trước khi xem `test`**, đồng thời phân tích đầy đủ lý do kỹ thuật vì sao **Chiến lược C** vượt trội về độ chính xác vị trí đầu (`Hit@1`), tính mạch lạc (`Coherence`), kiểm soát phạm vi (`Metadata Filtering`) và chất lượng trả lời cuối (`Test Grounding`).

---

## Kết quả

### Bảng 1 — Kết quả định lượng (Retrieval Relevance & Hiệu năng)

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian | Chi phí |
|---|---|---|---|---|---|---|
| **A** (`fixed_size_500_50`, no filter — **Thắng theo tiêu chí khóa `Dev Hit@3`**) | `dev` | `1/15` (`6.67%`) | `8/15` (`53.33%`) | 390 (`mean=473.4`, `p50=500`, `p90=500`) | Ingest (2x idempotent): `316.24s`<br>(`chunk=0.06s`, `embed=187.48s`, `upsert=128.70s`) | \$0.00 (local CPU) |
| **A** (`fixed_size_500_50`, no filter — **Thắng theo tiêu chí khóa `Dev Hit@3`**) | `test` | `2/5` (`40.00%`) | `2/5` (`40.00%`) | 390 (`min=59`, `max=500`, `stdev=89.0`) | (chạy chung lần đo trên) | \$0.00 (local CPU) |
| **B** (`by_paragraph_max_1000`, no filter) | `dev` | `4/15` (`26.67%`) | `6/15` (`40.00%`) | 232 (`mean=720.4`, `p50=754`, `p90=966`) | Ingest (2x idempotent): `221.77s`<br>(`chunk=0.40s`, `embed=148.38s`, `upsert=72.99s`) | \$0.00 (local CPU) |
| **B** (`by_paragraph_max_1000`, no filter) | `test` | `2/5` (`40.00%`) | `3/5` (`60.00%`) | 232 (`min=112`, `max=1000`, `stdev=194.6`) | (chạy chung lần đo trên) | \$0.00 (local CPU) |
| **C** (`by_paragraph_max_1000` + metadata filter — **Tối ưu đa tiêu chí**) | `dev` | `4/15` (`26.67%`) | `6/15` (`40.00%`) | 232 (`mean=720.4`, `p50=754`, `p90=966`) | Ingest (2x idempotent): `194.12s`<br>(`chunk=0.41s`, `embed=176.60s`, `upsert=17.10s`) | \$0.00 (local CPU) |
| **C** (`by_paragraph_max_1000` + metadata filter — **Tối ưu đa tiêu chí**) | `test` | `2/5` (`40.00%`) | `3/5` (`60.00%`) | 232 (`min=112`, `max=1000`, `stdev=194.6`) | (chạy chung lần đo trên) | \$0.00 (local CPU) |

### Bảng 2 — Kết quả kiểm định chất lượng thủ công (Coherence, Metadata & Grounding)

| Strategy | Coherence trung bình /2 (n) | Metadata đủ và đúng (n/N) | Filter tuân thủ (n/N hoặc N/A) | Grounding 0/1/2 (số câu) và trung bình /2 |
|---|---|---|---|---|
| **A** (`fixed_size_500_50`) | **0.70 / 2.00** (`n=10`: `3` câu điểm 0, `7` câu điểm 1, `0` câu điểm 2) | **15/15** (`100.0%`) cho `source, page, year, task_domain`; **0/15** (`0.0%`) nếu tính cả trường `section` (không trích xuất) | `N/A` (không bật filter; tự nhiên khớp `3/3` dev và `2/2` test nhờ từ khóa tên tập dữ liệu) | `0`: 1 câu (`q19`)<br>`1`: 2 câu (`q18`, `q20`)<br>`2`: 2 câu (`q16`, `q17`)<br>Trung bình: **1.20 / 2.00** (`n=5`) |
| **B** (`by_paragraph_max_1000`, no filter) | **1.70 / 2.00** (`n=10`: `0` câu điểm 0, `3` câu điểm 1, `7` câu điểm 2) | **15/15** (`100.0%`) cho `source, page, year, task_domain`; **13/15** (`86.7%`) nếu kiểm tra khắt khe cả tên mục `section` | `N/A` (không bật filter; tự nhiên khớp `3/3` dev và `2/2` test) | `0`: 1 câu (`q19`)<br>`1`: 1 câu (`q18`)<br>`2`: 3 câu (`q16`, `q17`, `q20`)<br>Trung bình: **1.40 / 2.00** (`n=5`) |
| **C** (`by_paragraph_max_1000` + metadata filter) | **1.70 / 2.00** (`n=10`: `0` câu điểm 0, `3` câu điểm 1, `7` câu điểm 2) | **15/15** (`100.0%`) cho `source, page, year, task_domain`; **13/15** (`86.7%`) nếu kiểm tra khắt khe cả tên mục `section` | **Dev**: `3/3` câu (`100.0%`, `9/9` hits)<br>**Test**: `2/2` câu (`100.0%`, `6/6` hits) | `0`: 1 câu (`q19`)<br>`1`: 1 câu (`q18`)<br>`2`: 3 câu (`q16`, `q17`, `q20`)<br>Trung bình: **1.40 / 2.00** (`n=5`) |

- **Đường dẫn trace, nhãn thủ công và cách chọn mẫu**:
  - Nhật ký nạp và chuẩn hóa từng trang PDF: `results/ingestion_log.json`
  - Trace top-3 đầy đủ cho 20 câu × 3 chiến lược (`60` truy vấn, `180` bản ghi): `results/traces_top3.json`
  - Tổng hợp chỉ số định lượng và thống kê phân phối chunk: `results/metrics_summary.json`
  - Mẫu ngẫu nhiên cố định theo vị trí giữa trang (`coh_01`–`coh_10`) và bảng chấm Coherence: `results/coherence_samples_raw.json`, `results/manual_audit_coherence.json`, `results/manual_audit_coherence.md`
  - Kiểm toán thủ công 15 bản ghi `test` (`q16`–`q20` × top-3) về Metadata: `results/manual_audit_metadata.json`, `results/manual_audit_metadata.md`
  - Chấm điểm thủ công Downstream Grounding (`q16`–`q20`): `results/manual_audit_grounding.json`, `results/manual_audit_grounding.md`
  - Nhật ký thực nghiệm 3 lần chạy A, B, C: `artifacts/experiment_log.csv`
  - **Ghi chú xác minh thời gian đo (`executed_at` vs. `evaluation_recomputed_at`)**: Trong `results/metrics_summary.json` và `artifacts/experiment_log.csv`, mốc `"executed_at": "2026-11-14T15:37:25.874260+07:00"` là thời điểm thực thi đầy đủ toàn bộ quá trình đọc PDF (`22.4365s`), cắt chunk, nhúng ONNX trên CPU và nạp lặp `2x idempotent` vào Qdrant (`A = 316.2428s`, `B = 221.7665s`, `C = 194.1171s`). Khi bổ sung `evidence_quote` trong `benchmark/questions.json` và nâng cấp hàm `evaluate_query` cho câu `q20`, bước chấm điểm lại (`evaluate_query` và `summarize`) được chạy trực tiếp trên các top-3 chunks đã lưu và được ghi nhận riêng tại trường `"evaluation_recomputed_at"` trong `metrics_summary.json` (không nạp/nhúng lại vector nên các con số thời gian ingest 4 chữ số thập phân của phiên chạy `15:37:25` được giữ nguyên trung thực).
  - **Cách chọn mẫu Coherence**: Trước khi so sánh các chiến lược, pipeline chọn cố định 10 trang đầu tiên và lấy ký tự chính giữa trang (`anchor_midpoint_char = len(page_text) // 2`) làm mỏ neo (`coh_01` đến `coh_10`), sau đó lấy đúng chunk chứa ký tự mỏ neo đó ở mỗi chiến lược A, B, C để chấm đối xứng.

---

## Phân tích và kết luận

- **So sánh A–B và B–C; 2 ví dụ sai có ID câu và nguồn**:
  - **So sánh A và B (Tác động của Chunking theo cấu trúc vs. Cố định)**:
    - *Trên tập `dev`*: Chiến lược B tăng **Hit@1 gấp 4 lần** so với A (`4/15 = 26.67%` ở `q08`, `q11`, `q12`, `q13` so với chỉ `1/15 = 6.67%` ở `q13` của A) và nâng điểm **Coherence từ `0.70/2.00` lên `1.70/2.00`**. Tuy nhiên, A lại có `Dev Evidence Hit@3` cao hơn B (`8/15 = 53.33%` ở `q05, q08, q09, q11, q12, q13, q14, q15` so với `6/15 = 40.00%` ở `q07, q08, q09, q11, q12, q13` của B — tức A trúng thêm `q05`, `q14`, `q15` ở rank 2–3 trong khi B trúng thêm `q07`). Nguyên nhân kỹ thuật rất rõ ràng: mô hình `all-MiniLM-L6-v2` nén toàn bộ đoạn văn vào một vector 384 chiều (và giới hạn độ dài tối đa 256 wordpieces). Khi Chiến lược B gộp nhiều đoạn văn tới gần `1000` ký tự (ví dụ ở `q14`, B trả về `B:wikihow-2018:p02:c005`, `B:wikihow-2018:p03:c004` và `B:wikihow-2018:p01:c001`, trong khi câu chứa con số `230,000` nằm trong chunk dài ở cuối trang 3), vector biểu diễn bị pha loãng bởi nhiều chủ đề phụ trong cùng một chunk, khiến các chunk tổng quan ngắn hơn vượt lên chiếm top-3.
    - *Trên tập `test` và Grounding*: Chiến lược B và C vượt trội hơn A cả về **Test Evidence Hit@3 (`3/5 = 60.00%` so với `2/5 = 40.00%`)** lẫn **Grounding (`1.40/2.00` so với `1.20/2.00`)**. Ở câu `q20` (`wikihow-2018`), Chiến lược A cắt trang 4 thành 9 mảnh nhỏ nên chỉ lấy được phần lời văn giải thích *Inverted Pyramid* (`A:wikihow-2018:p04:c008`, `p04:c007`) mà làm rơi mất bảng số liệu ROUGE-L (`A:wikihow-2018:p04:c001`). Ngược lại, Chiến lược B và C gom gọn trang 4 thành 5 khối đoạn/bảng nên lấy được cả đoạn giải thích `C:wikihow-2018:p04:c005` (Rank 1) lẫn toàn bộ Bảng 2 `C:wikihow-2018:p04:c001` chứa dòng `Pointer-generator + coverage ... 26.54` (Rank 2).
  - **So sánh B và C (Tác động của Metadata Filtering)**:
    - Trong bộ 5 bài báo này, do mỗi bài viết về một bộ dữ liệu có tên riêng biệt (`GOOAQ`, `PAQ`, `Reddit`, `SearchQA`, `WikiHow`), truy vấn ngữ nghĩa ở Chiến lược B vốn đã tự nhiên đưa các chunk đúng bài báo lên đầu, nên B và C cho kết quả `Hit@1` và `Evidence Hit@3` bằng nhau (`4/15` và `6/15` trên dev, `2/5` và `3/5` trên test).
    - Tuy nhiên, Chiến lược C mang lại **đảm bảo tất định (deterministic scope isolation)** và giảm mạnh chi phí tính toán tích vô hướng: ở `q18` (`year=2019, task_domain=dialogue`), bộ lọc giảm số ứng viên từ `232` xuống `37` chunks (`-84.1%`); ở `q20` (`year=2018, task_domain=summarization`), bộ lọc giảm số ứng viên từ `232` xuống chỉ còn `23` chunks (`-90.1%`), loại bỏ hoàn toàn nguy cơ lấy nhầm các đoạn thảo luận về `CNN/DailyMail` trong bài `searchqa-2017` (`year=2017`).
  - **Phân tích 2 ví dụ truy xuất sai cụ thể (kèm ID câu, nguồn và chunk ID)**:
    1. **Ví dụ lỗi 1 — `q10` (Tập `dev`, loại `condition_exception`, nguồn chuẩn `reddit-2019` trang 3)**:
       - *Câu hỏi*: Hỏi về điều kiện lọc bỏ bình luận Reddit theo số ký tự (`> 128` hoặc `< 9` ký tự) và nội dung (`[deleted]` hoặc `[removed]`).
       - *Hiện tượng trong `results/traces_top3.json`*: Cả A, B, C đều trượt `Evidence Hit@3` (`false`), mặc dù **đã truy xuất đúng trang 3 của `reddit_2019.pdf`** (`gold_page_retrieved_in_top3 = true`, `evidence_split_error = true`). Cụ thể, Chiến lược A trả về `A:reddit-2019:p02:c001` (Rank 1, điểm `0.8816`), `A:reddit-2019:p03:c005` (Rank 2, điểm `0.8773`) và `A:reddit-2019:p03:c003` (Rank 3, điểm `0.8709`); Chiến lược B/C trả về `B:reddit-2019:p02:c001` / `C:reddit-2019:p02:c001` (Rank 1, điểm `0.8866`), `B:reddit-2019:p03:c002` / `C:reddit-2019:p03:c002` (Rank 2, điểm `0.8735`) và `B:reddit-2019:p03:c003` / `C:reddit-2019:p03:c003` (Rank 3, điểm `0.8695`).
       - *Nguyên nhân gốc rễ*: Câu bằng chứng chuẩn (`"The example is filtered if either feature has more than 128 characters, or fewer than 9 characters, or if its text is set to [deleted] or [removed]."`) nằm ở `B:reddit-2019:p03:c004` (`969` ký tự) và bị cắt giữa `A:reddit-2019:p03:c006` với `A:reddit-2019:p03:c007`. Đoạn này diễn đạt bằng thuật ngữ kỹ thuật (`either feature`, `context`, `response`) mà không lặp lại từ `"Reddit"` hay `"conversational"`, trong khi các đoạn giới thiệu tổng quan (`p02:c001` nói `"after preprocessing around 3.7B comments from Reddit... conversational threads"`, `p03:c002` mô tả quy mô tập dữ liệu từ 2015–2018 và `p03:c003` nói `"consistent filtering, processing... Reddit conversations"`) chứa mật độ từ khóa trùng khớp với câu hỏi cao hơn nên chiếm hết 3 vị trí đầu.
    2. **Ví dụ lỗi 2 — `q19` (Tập `test`, loại `condition_exception`, nguồn chuẩn `searchqa-2017` trang 2)**:
       - *Câu hỏi*: Hỏi về các thuộc tính khiến snippet trong SearchQA bị loại bỏ khi làm sạch (`air-date`, bản sao câu hỏi, các từ `"Jeopardy!"`, `"quiz"`, `"trivia"`) và độ dài câu trả lời tối đa được giữ lại (`<= 3` từ).
       - *Hiện tượng trong `results/traces_top3.json`*: Chiến lược A trả về `A:searchqa-2017:p02:c009` (Rank 1, mục *Training, Validation and Test Sets*), `A:gooaq-2021:p07:c011` (Rank 2) và `A:gooaq-2021:p02:c009` (Rank 3). Chiến lược B và C trả về `B:searchqa-2017:p01:c002` (Rank 1, *Abstract*), `B:gooaq-2021:p02:c006` (Rank 2) và `B:searchqa-2017:p03:c002` (Rank 3, *Closed-World Question-Answering*). Điểm Grounding = `0/2`.
       - *Nguyên nhân gốc rễ*: Thứ nhất, câu hỏi `q19` không có metadata filter nên các đoạn nói về `"snippet response questions"` của bài `gooaq-2021` cạnh tranh trực tiếp và chiếm Rank 2. Thứ hai, dense embedding `all-MiniLM-L6-v2` ưu tiên sự tương đồng chủ đề chung (`"SearchQA"`, `"snippets"`, `"question-answer pair"`) ở phần *Abstract* (`p01:c002`), trong khi đoạn chứa quy tắc làm sạch cụ thể trên trang 2 (`B:searchqa-2017:p02:c003` và `p02:c004`) chứa nhiều danh từ riêng và ký hiệu (`Jeopardy!`, `J! Archive`, `three or less words`) có khoảng cách cosine xa hơn so với câu hỏi khái quát.

- **Chiến lược chọn, đánh đổi, điều kiện áp dụng**:
  - **Chiến lược được chọn theo quy tắc khóa trước thực nghiệm (`selection_criteria_locked_before_test`)**: **Chiến lược A** (`fixed_size = 500`, `overlap = 50`) là chiến lược thắng trên `dev` theo đúng tiêu chí cấp 1 đã khóa (`Dev Evidence Hit@3 = 8/15 = 53.33%` so với `6/15 = 40.00%` của B và C), và đạt `2/5 (40.00%)` trên tập `test`.
  - **Khuyến nghị kỹ thuật từ phân tích đa tiêu chí**: Nếu xét tổng thể 5 nhóm tiêu chí của bài lab (Retrieval `Hit@1` & `Hit@3`, `Chunk Coherence`, `Metadata & Filtering`, `Downstream Grounding`, và chi phí lưu trữ/thời gian nạp), **Chiến lược C** (`by_paragraph`, `max_chars = 1000`, kèm metadata filter `year + task_domain`) thể hiện sự cân bằng vượt trội cho môi trường sản xuất:
    - So với Chiến lược A, Chiến lược C giảm `40.5%` số lượng vectors cần lưu trữ (`232` vs. `390`), giảm `38.6%` thời gian nạp (`194.12s` vs. `316.24s`), tăng gấp 4 lần `Dev Hit@1` (`26.67%` vs. `6.67%`), tăng `Test Evidence Hit@3` từ `40.00%` lên `60.00%`, nâng điểm mạch lạc `Coherence` từ `0.70/2.00` lên `1.70/2.00` và nâng `Grounding` từ `1.20/2.00` lên `1.40/2.00`.
    - Đổi lại, việc cho phép chunk dài tới `1000` ký tự (tương đương ~180–230 từ) khiến một số chi tiết nhỏ nằm ở cuối đoạn dài bị pha loãng trong vector 384 chiều (làm `Dev Evidence Hit@3` đạt `6/15` thấp hơn `8/15` của A). Bài học rút ra là quy tắc khóa trước thực nghiệm không nên chỉ dùng `Dev Evidence Hit@3` làm khóa phân cấp tuyệt đối mà cần đặt ngưỡng sàn `Chunk Coherence >= 1.50/2.00` kết hợp điểm trung bình của `Dev Hit@1` và `Dev Evidence Hit@3`.
  - **Điều kiện áp dụng**:
    - **Chiến lược A** phù hợp khi cần tìm nhanh các mệnh đề sự kiện đơn lẻ ngắn (`1–2` câu) và chấp nhận ghép nhiều mảnh cắt cụt vào prompt.
    - **Chiến lược C** phù hợp cho hệ thống RAG hỏi đáp tài liệu kỹ thuật/bài báo khoa học có cấu trúc mục rõ ràng, có bảng số liệu đi kèm đoạn phân tích, và có thể lọc trước theo năm xuất bản (`year`) hoặc lĩnh vực (`task_domain`).

- **Hạn chế của dữ liệu, nhãn, test nhỏ, đo thời gian/chi phí**:
  - **Tập `test` nhỏ (`N = 5` câu)**: Mỗi câu hỏi trên tập `test` chiếm tới `20%` độ đo, nên sự khác biệt 1 câu (như câu `q20`) tạo ra bước nhảy `20%` (`40%` lên `60%`). Do đó cần kết hợp đọc cả kết quả trên tập `dev` (`N = 15`), số lỗi chia tách bằng chứng (`evidence_split_error`) và kiểm định thủ công.
  - **Thiên lệch nhãn thủ công (Single-Annotator Bias)**: Các điểm `Coherence` (`10` mẫu) và `Grounding` (`5` câu test) cùng bộ câu hỏi benchmark do một người thực hiện chấm và thiết kế; dù đã cố định vị trí mẫu `anchor_midpoint_char` trước khi chấm để giảm thiên vị, kết quả vẫn mang tính chủ quan của một người đánh giá.
  - **Giới hạn độ dài token của `all-MiniLM-L6-v2` (Max Sequence Length = 256 wordpieces)**: Các chunk có kích thước gần `1000` ký tự và chứa nhiều con số/ký hiệu bảng biểu có thể vượt ngưỡng 256 wordpieces, khiến phần đuôi của chunk bị cắt cụt khi tính embedding.
  - **Hạn chế trích xuất PDF 2 cột và gán nhãn `section`**: Như đã chỉ ra trong `results/manual_audit_metadata.md` (`13/15 = 86.7%`), bộ nhận diện tiêu đề mục theo từng trang đôi khi nhận nhầm dòng chú thích bảng đầu trang (`Table 2: Error distribution...` ở `gooaq-2021` trang 8) làm tên `section` cho đoạn văn cột phải, hoặc gán nhãn mặc định `Page_Header_or_Body` cho các đoạn đầu trang kế tiếp mục của trang trước.

- **Nếu làm lại hoặc mở rộng, cải tiến gì?**
  1. **Giảm `max_chars` của `by_paragraph` xuống `650–750` ký tự kèm câu dẫn ngữ cảnh (Contextual Header Prefix)**: Đảm bảo mọi đoạn văn đều nằm gọn trong giới hạn `256` wordpieces của `all-MiniLM-L6-v2` (khắc phục hiện tượng pha loãng vector trên tập `dev` để đạt đồng thời `Dev Evidence Hit@3` cao như A và `Coherence` cao như C) đồng thời tiền tố hóa chuỗi `"[Doc: {title} | Section: {section}] "` vào đầu văn bản trước khi nhúng để những đoạn thiếu từ khóa tên bài báo (như `q10` trên `reddit-2019` trang 3) vẫn giữ được ngữ cảnh toàn cục.
  2. **Kết hợp Hybrid Search (BM25 + Dense Vector) và Cross-Encoder Reranker**: Nhiều lỗi truy xuất (như `q10` cần tìm con số `128 characters`, `[deleted]`, `[removed]` hay `q19` cần tìm `"Jeopardy!"`, `"quiz"`, `"trivia"`) là truy vấn khớp từ khóa chính xác. Kết hợp điểm lexical BM25 với cosine similarity của `all-MiniLM-L6-v2` (Reciprocal Rank Fusion) trên top-10 rồi rerank xuống top-3 sẽ giải quyết triệt để cả `q10`, `q18` và `q19`.
  3. **Liên thông trạng thái `current_section` xuyên qua các trang PDF và tách riêng regex cho `Table`/`Figure`**: Duy trì biến `active_section` xuyên suốt toàn bộ một tài liệu `document_id` thay vì đặt lại ở mỗi trang mới, đồng thời lưu `table_caption` thành một trường metadata riêng tách biệt với `section`.
