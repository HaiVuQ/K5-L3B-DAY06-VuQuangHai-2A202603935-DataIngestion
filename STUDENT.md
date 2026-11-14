# STUDENT — Thông tin bài nộp cá nhân

- Họ và tên: Vũ Quang Hải
- MSSV: 2A202603935
- Lớp: L3B
- Ngày làm bài: 2026-11-14
- Nguồn tài liệu đã chọn: 5 bài báo khoa học tiếng Anh (PDF) thuộc bảng bộ dữ liệu huấn luyện (Training Datasets) gắn trực tiếp trên trang Hugging Face `https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2` (gồm: `gooaq_2021.pdf`, `paq_2021.pdf`, `reddit_2019.pdf`, `searchqa_2017.pdf`, `wikihow_2018.pdf`).
- Tổng số tài liệu và tổng số trang: 5 tài liệu PDF — tổng cộng **49 trang vật lý**, trong đó giữ lại **40 trang nội dung hợp lệ** (`167,221` ký tự sau chuẩn hóa; đạt yêu cầu `>= 30 trang nội dung thực`) và loại bỏ 9 trang chỉ chứa danh mục tài liệu tham khảo (References).
- Ngôn ngữ tài liệu: Tiếng Anh (English)
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (chạy local qua `fastembed` / ONNX Runtime, vector 384 chiều, chuẩn hóa L2, cosine similarity)
- Vector store: Qdrant Local lưu bền vững trên đĩa (`qdrant-client`, thư mục `data/qdrant_storage`, collection `day6_chunks`; đồng thời hỗ trợ `PgVectorStore` PostgreSQL + `pgvector` trong `starter/src/store.py`)
- Chiến lược được chọn để chạy test: Chiến lược **C** (`by_paragraph`, `max_chars=1000`, kèm metadata `year`, `task_domain`, `section` và áp dụng metadata filter trên `year` + `task_domain` khi câu hỏi có `filter`) — đồng thời xuất đầy đủ kết quả đối chiếu của cả A, B, C trên tập `dev` và `test` trong `results/`.
- Link repo GitHub cá nhân: `https://github.com/HaiVuQ/K5-L3B-DAY06-VuQuangHai-2A202603935-DataIngestion.git`
- Cam kết liêm chính học thuật: Tôi cam kết đã tự thực hiện pipeline, tự kiểm tra bộ câu hỏi benchmark, không dùng nhãn `test` để chọn chiến lược, và không bịa số liệu hay kết quả.
