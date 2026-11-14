# STUDENT — Thông tin bài nộp cá nhân

- Họ và tên: Vũ Quang Hải
- MSSV: 2A202603935
- Lớp: L3B
- Ngày làm bài: 2026-11-14
- Nguồn tài liệu đã chọn: 5 bài báo khoa học tiếng Anh (PDF) thuộc bảng bộ dữ liệu huấn luyện (Training Datasets) gắn trực tiếp trên trang Hugging Face `https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2` (gồm: `gooaq_2021.pdf`, `paq_2021.pdf`, `reddit_2019.pdf`, `searchqa_2017.pdf`, `wikihow_2018.pdf`).
- Tổng số tài liệu và tổng số trang: 5 tài liệu PDF — tổng cộng **49 trang vật lý**, trong đó giữ lại **40 trang nội dung hợp lệ** (`167,221` ký tự sau chuẩn hóa; đạt yêu cầu `>= 30 trang nội dung thực`) theo đúng quy tắc trong `data/manifest.json`: chỉ tính các trang có nội dung học thuật thực sự với độ dài sau chuẩn hóa `normalized_char_count >= 500` ký tự (trang hợp lệ ngắn nhất thực tế có `1,495` ký tự) và loại bỏ 9 trang chỉ chứa danh mục tài liệu tham khảo (`excluded_pages` - References).
- Ngôn ngữ tài liệu: Tiếng Anh (English)
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (chạy local qua `fastembed` / ONNX Runtime, vector 384 chiều, chuẩn hóa L2, cosine similarity)
- Vector store: Qdrant Local lưu bền vững trên đĩa (`qdrant-client`, thư mục `data/qdrant_storage`, collection `day6_chunks`; đồng thời hỗ trợ `PgVectorStore` PostgreSQL + `pgvector` trong `starter/src/store.py`)
- Chiến lược được chọn để chạy test:
  - **Theo đúng tiêu chí đã khóa trước khi xem `test` (`selection_criteria_locked_before_test` trong `benchmark/questions.json` — ưu tiên `Dev Evidence Hit@3` cao nhất)**: **Chiến lược A** (`fixed_size`, `chunk_size=500`, `overlap=50`) thắng trên tập `dev` với `Dev Evidence Hit@3 = 8/15 (53.33%)` (so với `6/15 = 40.00%` của B và C) nên được chọn làm chiến lược chính thức theo quy tắc đã khóa để đánh giá trên `test` (đạt `Test Hit@1 = 2/5`, `Test Evidence Hit@3 = 2/5`).
  - **Đối chiếu đa tiêu chí hậu nghiệm (được lưu đầy đủ trong `results/` cho cả A, B, C)**: Báo cáo phân tích rõ sự đánh đổi khi quy tắc khóa đơn biến (`Dev Evidence Hit@3`) chọn A dù **Chiến lược C** (`by_paragraph`, `max_chars=1000` + `metadata_filter` trên `year`, `task_domain`) vượt trội trên các tiêu chí còn lại (`Dev Hit@1 = 4/15` so với `1/15` của A, `Coherence = 1.70/2.00` so với `0.70/2.00`, `100%` tuân thủ filter, giảm 40.5% số chunk, và đạt `Test Evidence Hit@3 = 3/5`, `Grounding = 1.40/2.00`). Tập `test` (`q16`–`q20`) cũng được ghi chú minh bạch là đã qua bước rà soát/bổ sung đầy đủ `evidence_quote` và chấm điểm lại (`evaluation_recomputed_at`) trên kết quả truy xuất của phiên chạy `15:37:25`.
- Link repo GitHub cá nhân: `https://github.com/HaiVuQ/K5-L3B-DAY06-VuQuangHai-2A202603935-DataIngestion.git`
- Cam kết liêm chính học thuật: Tôi cam kết đã tự thực hiện pipeline, tự kiểm tra bộ câu hỏi benchmark, giữ nguyên tiêu chí đã khóa trước khi xem `test`, không dùng nhãn `test` để chọn chiến lược, và không bịa số liệu hay kết quả.
