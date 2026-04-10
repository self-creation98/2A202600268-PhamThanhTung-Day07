# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** 2026-04-10

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Hai đoạn văn bản có cosine similarity cao có nghĩa là vector embedding của chúng trỏ cùng hướng trong không gian nhiều chiều. Điều này cho thấy chúng có nội dung ngữ nghĩa tương tự — cùng nói về một chủ đề hoặc chứa các khái niệm liên quan.

**Ví dụ HIGH similarity:**
- Sentence A: "Python là một ngôn ngữ lập trình bậc cao."
- Sentence B: "Python là ngôn ngữ lập trình đa năng, dễ học."
- Tại sao tương đồng: Cả hai câu đều nói về Python với tư cách ngôn ngữ lập trình, chia sẻ nhiều từ khóa và khái niệm giống nhau (Python, ngôn ngữ, lập trình).

**Ví dụ LOW similarity:**
- Sentence A: "Bảo hiểm y tế được cung cấp qua Blue Cross Blue Shield."
- Sentence B: "Chúng tôi làm việc theo chu kỳ 6 tuần."
- Tại sao khác: Hai câu nói về chủ đề hoàn toàn khác nhau — bảo hiểm y tế vs quy trình làm việc, không chia sẻ từ khóa hay khái niệm nào.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity đo góc giữa hai vector, không phụ thuộc vào độ dài (magnitude) của vector. Điều này quan trọng vì text embeddings có thể có độ dài khác nhau tùy thuộc vào model hoặc cách normalize. Hai văn bản nói về cùng chủ đề nhưng có độ dài khác nhau vẫn có cosine similarity cao, trong khi Euclidean distance sẽ bị ảnh hưởng bởi sự khác biệt magnitude, cho kết quả không phản ánh đúng mức độ tương đồng ngữ nghĩa.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Áp dụng công thức: `num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))`
> `num_chunks = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23 chunks`
> **Đáp án: 23 chunks**

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> `num_chunks = ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks`
> Chunk count tăng từ 23 lên 25. Overlap nhiều hơn giúp ngữ cảnh ở ranh giới các chunk không bị mất — nếu một câu quan trọng nằm ở cuối chunk trước, nó sẽ được lặp lại ở đầu chunk sau, đảm bảo retrieval không bỏ sót thông tin quan trọng nằm tại vị trí chia cắt.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Employee Handbook (Sổ tay nhân viên) — 37signals

**Tại sao nhóm chọn domain này?**
> Handbook nhân viên là domain lý tưởng cho bài toán RAG vì: (1) nội dung đa dạng nhưng có cấu trúc rõ ràng — từ phúc lợi, chính sách đến quy trình — phù hợp để test nhiều loại query; (2) câu hỏi thường có câu trả lời cụ thể, dễ đánh giá precision; (3) metadata tự nhiên (category, topic) giúp test filter-based retrieval.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | phuc_loi_va_quyen_loi.md | benefits-and-perks.md (dịch VI) | 5,321 | category=benefits, topic=insurance_leave_retirement |
| 2 | bat_dau_lam_viec.md | getting-started.md (dịch VI) | 2,614 | category=onboarding, topic=getting_started |
| 3 | cach_lam_viec.md | how-we-work.md (dịch VI) | 3,727 | category=culture, topic=remote_work_communication |
| 4 | phat_trien_nghe_nghiep.md | making-a-career.md (dịch VI) | 3,551 | category=career, topic=titles_salary_reviews |
| 5 | lam_them_ngoai_gio.md | moonlighting.md (dịch VI) | 2,478 | category=policy, topic=moonlighting |
| 6 | nghi_viec_va_tro_cap.md | severance.md (dịch VI) | 1,079 | category=policy, topic=severance |
| 7 | nghi_le_va_truyen_thong.md | our-rituals.md (dịch VI) | 1,590 | category=culture, topic=rituals_meetups |
| 8 | he_thong_noi_bo.md | our-internal-systems.md (dịch VI) | 1,940 | category=systems, topic=internal_tools |
| 9 | quan_ly_thiet_bi.md | managing-work-devices.md (dịch VI) | 2,338 | category=policy, topic=device_management |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| category | string | benefits, policy, culture, career, onboarding, systems | Cho phép filter theo phân loại chính sách — khi user hỏi về phúc lợi, chỉ tìm trong docs category=benefits, tăng precision |
| topic | string | insurance_leave_retirement, moonlighting, severance | Cho phép filter chi tiết hơn category — ví dụ trong policy có 3 topics khác nhau (moonlighting, severance, device_management) |
| language | string | vi, en | Cho phép filter theo ngôn ngữ — hữu ích khi có cả bản tiếng Anh và tiếng Việt trong store |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Step 1 — Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu với **default `chunk_size=200`**:

| Tài liệu | Strategy | Chunk Count | Avg Length | Nhận xét |
|-----------|----------|-------------|------------|---------|
| phuc_loi_va_quyen_loi.md (5321 chars) | FixedSize(200) | 36 | 196.4 | Quá nhiều chunks, cắt giữa câu |
| | Sentence(3) | 18 | 293.7 | Giữ ranh giới câu |
| | Recursive(200) | 43 | 121.8 | Quá nhiều chunks nhỏ, mất context |
| cach_lam_viec.md (3727 chars) | FixedSize(200) | 25 | 197.1 | Quá nhiều chunks |
| | Sentence(3) | 12 | 308.7 | Tốt |
| | Recursive(200) | 32 | 114.6 | Quá nhỏ |
| phat_trien_nghe_nghiep.md (3551 chars) | FixedSize(200) | 24 | 195.9 | Quá nhiều chunks |
| | Sentence(3) | 13 | 271.1 | Tốt |
| | Recursive(200) | 28 | 124.9 | Quá nhỏ |

**Nhận xét baseline:** Với `chunk_size=200` (default), RecursiveChunker tạo **quá nhiều chunks** (28-43 chunks/file) với avg length chỉ ~120 chars — mỗi chunk quá nhỏ, mất ngữ cảnh. FixedSize(200) cũng tạo 24-36 chunks. Chỉ SentenceChunker giữ chunk size hợp lý (~300 chars).

### Step 2 — Strategy Của Tôi

**Loại:** RecursiveChunker (tuned `chunk_size=500`)

**Mô tả cách hoạt động:**
> RecursiveChunker thử split text bằng separator ưu tiên cao nhất trước (`\n\n` — paragraph break), nếu chunk vẫn quá lớn thì thử separator tiếp theo (`\n`, `. `, ` `, `""`). Cách tiếp cận đệ quy này đảm bảo chunk giữ được cấu trúc ngữ nghĩa tốt nhất có thể — ưu tiên chia theo paragraph trước, rồi mới đến câu, rồi mới đến từ.

**Tại sao tuning chunk_size từ 200 → 500?**
> Baseline Recursive(200) tạo quá nhiều chunks nhỏ (avg 120 chars) — mỗi chunk chỉ chứa 1-2 câu, không đủ context cho retrieval. Tăng lên 500 giúp mỗi chunk chứa trọn 1 section/paragraph (~330 chars avg), giữ nguyên ngữ cảnh mà không quá lớn gây "pha loãng" embedding.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Handbook nhân viên có cấu trúc rõ ràng với sections (`##`), paragraphs, và bullet lists. RecursiveChunker khai thác cấu trúc này bằng cách ưu tiên chia theo paragraph (`\n\n`) — mỗi section thường chứa một policy/topic trọn vẹn.

### 4 Custom Strategies (Exercise 3.1 — Step 2)

Ngoài 3 strategies cơ bản (baseline), tôi thiết kế thêm 4 custom strategies trong cùng file `src/chunking.py` để so sánh:

| Strategy | Cách hoạt động | Phù hợp khi nào? |
|----------|----------------|-------------------|
| **SemanticChunker** | Embed từng câu → tính similarity giữa câu liên tiếp → tách tại nơi similarity giảm dưới threshold | Data không có cấu trúc header rõ ràng |
| **DocStructureChunker** | Detect markdown headers (`##`, `###`) → tách theo section → mỗi chunk giữ header | Data có cấu trúc markdown rõ ràng (handbook, docs) |
| **AgenticChunker** | Dùng LLM quyết định ranh giới chunk: với mỗi paragraph mới, hỏi LLM "SAME topic hay NEW topic?" | Cần semantic accuracy cao, chấp nhận chi phí API |
| **ParentChildChunker** | Tạo 2 tầng: Parent (800 chars, dùng cho LLM context) → Child (200 chars, dùng cho search) | Cần precision cao (child nhỏ) + context đầy đủ (parent lớn) |

### Step 3 — So sánh: Baseline vs My Strategy vs Custom

Chunking statistics trên `phuc_loi_va_quyen_loi.md` (5321 chars) — tất cả strategies nằm trong `src/chunking.py`:

| | Strategy | Chunks | Avg Length | So với Baseline |
|---|----------|--------|-----------|-----------------|
| Baseline | FixedSize(**200**) | 36 | 196 | — (quá nhiều chunks) |
| Baseline | Sentence(3) | 18 | 294 | — (chunk nhỏ gọn) |
| Baseline | Recursive(**200**) | 43 | 122 | — (quá nhỏ, mất context) |
| **★ My Strategy** | **Recursive(500)** | **16** | **331** | **−63% chunks**, **+172% avg length** so với baseline Recursive(200) |
| Custom | Semantic | 18 | 294 | Tương đương Sentence |
| Custom | DocStructure | 17 | 311 | Gần My Strategy |
| Custom | Agentic | 8 | 663 | Ít chunk nhất, topic-focused |
| Custom | ParentChild | 34 | 179 | Nhiều child nhỏ |

### Chunk Coherence Analysis (EVALUATION Metric #2)

**Ví dụ so sánh output chunking trên cùng đoạn text (phuc_loi_va_quyen_loi.md, đoạn "Bảo hiểm y tế"):**

| Strategy | Chunk example (trích) | Coherent? |
|----------|----------------------|----------|
| FixedSizeChunker | `"...chi trả 75% phí bảo hiểm và nhân viên chi trả 25% còn lại. Đăng ký mở vào tháng 11 hàng năm, với bảo hi"` | ❌ Cắt giữa từ "bảo hiểm" — mất ý |
| SentenceChunker | `"Tại Hoa Kỳ, bảo hiểm y tế được cung cấp thông qua Blue Cross Blue Shield PPO. Công ty chi trả 75%...Đăng ký mở vào tháng 11 hàng năm."` | ✅ 3 câu trọn vẹn |
| **RecursiveChunker** | `"## Bảo Hiểm Sức Khỏe\n\nTại Hoa Kỳ, bảo hiểm y tế...Bạn đủ điều kiện nhận bảo hiểm từ ngày đầu tiên làm việc."` | ✅ Trọn vẹn section, có heading |
| DocStructureChunker | `"## Bảo Hiểm Sức Khỏe\n\nTại Hoa Kỳ...đủ điều kiện từ ngày đầu."` | ✅ Giống Recursive, giữ header |
| SemanticChunker | `"Bảo hiểm y tế được cung cấp...chi trả 75%...Đăng ký mở vào tháng 11."` | ✅ Gom câu cùng topic |
| AgenticChunker | `"## Bảo Hiểm Sức Khỏe...bao gồm cả bảo hiểm nha khoa và thị lực..."` | ✅ Gom nhiều subsections liên quan |
| ParentChildChunker | `"Tại Hoa Kỳ, bảo hiểm y tế được cung cấp thông qua Blue Cross Blue Shield PPO."` | ⚠️ Quá ngắn, thiếu context |

### Retrieval Comparison — 7 Strategies × OpenAI Embeddings

Benchmark trên 5 queries với OpenAI `text-embedding-3-small`:

| Strategy | Total Chunks | Hit Rate | Avg Top-1 Score | Q1 | Q2 | Q3 | Q4 | Q5 |
|----------|-------------|----------|----------------|----|----|----|----|-----|
| 1. FixedSize(500) | 60 | **5/5** | 0.5831 | 0.6919 | 0.6863 | 0.5543 | 0.5111 | 0.4719 |
| 2. Sentence(3) | 87 | **5/5** | 0.5840 | 0.7059 | 0.6675 | 0.5436 | 0.5060 | 0.4972 |
| **3. Recursive(500)** | 72 | **5/5** | **0.5981** | **0.7139** | 0.6749 | 0.5889 | 0.4962 | **0.5167** |
| 4. Semantic | 98 | **5/5** | 0.5902 | 0.6903 | 0.6428 | 0.6212 | 0.5200 | 0.4767 |
| 5. DocStructure | 66 | **5/5** | 0.6074 | 0.7024 | 0.6873 | 0.6116 | 0.5384 | 0.4973 |
| **6. Agentic** | 41 | **5/5** | **0.6159** | 0.7001 | **0.6957** | **0.6332** | 0.5165 | **0.5337** |
| 7. ParentChild | 162 | **5/5** | 0.5870 | 0.6756 | 0.6503 | 0.6156 | 0.4861 | 0.5074 |

**Phân tích kết quả:**
> - **Tất cả 7 strategies đều đạt 5/5 hit** với OpenAI embeddings — embedding model đủ mạnh giúp retrieval chính xác bất kể chunking strategy.
> - **AgenticChunker có avg Top-1 score cao nhất (0.6159)** vì tạo ít chunk nhất (41), mỗi chunk chứa trọn topic → embedding rất focused.
> - **DocStructureChunker xếp #2 (0.6074)** — khai thác cấu trúc markdown headers tốt cho handbook.
> - **RecursiveChunker xếp #3 (0.5981)** — trade-off tốt: không cần LLM, không cần embedder cho chunking, score vẫn cao.
> - **ParentChildChunker có score thấp nhất** vì child chunks quá nhỏ (200 chars) → embedding bị fragment, thiếu context.

**Tại sao tôi vẫn chọn RecursiveChunker làm primary?**
> AgenticChunker có score cao nhất nhưng cần LLM call cho mỗi paragraph → chậm, tốn API cost, không scalable. DocStructureChunker đứng #2 nhưng chỉ hoạt động với markdown. RecursiveChunker đứng #3 với score chênh chỉ 0.02 so với #1, nhưng: (1) không cần LLM, (2) không cần embedder cho chunking, (3) hoạt động với mọi loại text, (4) tham số đơn giản (chunk_size). Đây là best trade-off giữa quality, speed, và generalizability.

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Phạm Thanh Tùng| RecursiveChunker(500) | 10/10 | Giữ trọn paragraph, nhanh, hoạt động với mọi loại text | Score trung bình thấp hơn Agentic/DocStructure |
| Nguyễn Năng Anh | SentenceChunker (max_sentences=3) | 10/10 | Giữ nguyên câu hoàn chỉnh, 5/5 queries tìm đúng file | Chunk dài hơn (avg 294), score Q3/Q4 thấp (~0.50)|
| Nguyễn Ngọc Hiếu | `MarkdownHeaderChunker` | 9.5 | Giữ nguyên vẹn bối cảnh (context) của các chính sách/quy định bằng cách gắn kèm tiêu đề cha (H1, H2). Tránh việc LLM nhầm lẫn giữa các mục "Được phép" và "Không được phép". | Các chunk có thể có kích thước không đồng đều (chunk size variance cao) do độ dài ngắn của từng section trong file markdown khác nhau. |
| Mai Phi Hiếu | `RecursiveChunker` | 9.5 | Giữ nguyên vẹn bối cảnh (context) của các chính sách/quy định bằng cách cắt theo paragraph `\n\n`. Mỗi chunk chứa đúng 1 ý, giúp retrieval chính xác. | Các chunk có kích thước không đồng đều (avg 121.8 chars) — heading đứng riêng tạo chunk quá ngắn, thiếu ngữ cảnh. |
| Dương Phương Thảo | SectionChunker + filter all | 10/10 (5/5 relevant) | Giữ structure, metadata filter hiệu quả | Chunk dài hơn, mock embedder vẫn random trong cùng category |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> **SectionChunker + metadata filter** (Dương Phương Thảo) cho kết quả tổng thể tốt nhất cho domain HR Handbook vì tài liệu 37signals được viết theo cấu trúc rõ ràng (section, heading), và việc kết hợp filter theo `category` giúp loại bỏ nhiễu ngay từ đầu. Tuy nhiên **SentenceChunker** (Nguyễn Năng Anh) và **RecursiveChunker(500)** (Phạm Thanh Tùng) cũng đạt 10/10 — chứng tỏ với domain có câu văn rõ ràng và đoạn văn chuẩn, nhiều strategy đều hoạt động tốt khi dùng embedding thật (OpenAI). Điểm khác biệt nằm ở **chunk size**: chunk quá ngắn (RecursiveChunker avg 121 chars) thiếu ngữ cảnh, chunk quá dài (SentenceChunker avg 294 chars) khó pinpoint thông tin chính xác.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Sử dụng regex `(?<=[.!?])(?:\s|\n)` để detect ranh giới câu — lookbehind cho dấu kết thúc câu (`.`, `!`, `?`) theo sau bởi whitespace hoặc newline. Sau khi split, strip whitespace thừa và lọc bỏ chuỗi rỗng. Gom sentences thành chunk theo `max_sentences_per_chunk` bằng cách duyệt qua list sentences với bước nhảy `max_sentences_per_chunk`. Edge case xử lý: text rỗng trả `[]`, text không có dấu câu trả nguyên text.

**`RecursiveChunker.chunk` / `_split`** — approach:
> `chunk()` gọi `_split()` đệ quy. `_split()` kiểm tra base case: nếu text <= chunk_size thì trả [text]. Nếu hết separator hoặc separator = "" thì force-split theo ký tự. Với mỗi separator, split text thành parts, rồi merge nhỏ lại: nếu tổng current_chunk + separator + part <= chunk_size thì gom, nếu không thì flush current_chunk và xử lý part (nếu part > chunk_size thì recurse với separator tiếp theo).

### EmbeddingStore

**`add_documents` + `search`** — approach:
> `add_documents` gọi `_make_record` cho mỗi doc, tạo embedding bằng `self._embedding_fn(doc.content)`, lưu dict {id, content, embedding, metadata} vào `self._store`. `search` embed query, rồi tính dot product giữa query embedding với mỗi stored embedding, sort descending, trả top_k. Sử dụng `_dot()` helper đã có sẵn.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` filter trước: duyệt `self._store`, chỉ giữ records có metadata match tất cả key-value trong `metadata_filter`, rồi chạy `_search_records` trên filtered set. `delete_document` dùng list comprehension lọc bỏ records có `metadata['doc_id'] == doc_id`, so sánh size trước/sau để trả True/False.

### KnowledgeBaseAgent

**`answer`** — approach:
> RAG 3 bước: (1) `self.store.search(question, top_k)` lấy chunks relevant nhất; (2) Build prompt với format "Context: [1] chunk1 [2] chunk2 ... Question: {question} Answer:"; (3) Gọi `self.llm_fn(prompt)` và trả kết quả. Prompt structure rõ ràng giúp LLM biết context nào available và câu hỏi cần trả lời.

### Pipeline Architecture

```
Document files (.md) 
    → RecursiveChunker (chunk_size=500) 
        → Chunks (72 chunks from 9 files)
            → OpenAI text-embedding-3-small 
                → EmbeddingStore (in-memory)
                    → search(query, top_k=3) 
                        → KnowledgeBaseAgent.answer()
```

### Test Results

```
tests/test_solution.py — 42 passed, 1 warning
======================== 42 passed in 1.32s ========================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Mock Score | OpenAI Score | OpenAI đúng? |
|------|-----------|-----------|---------|------------|-------------|-------------|
| 1 | Nhân viên được nghỉ phép 20 ngày mỗi năm. | Công ty cung cấp 20 ngày nghỉ phép hàng năm cho nhân viên. | HIGH | +0.0524 | **+0.8487** | ✅ Đúng |
| 2 | Bảo hiểm y tế được cung cấp qua Blue Cross Blue Shield. | Chúng tôi làm việc theo chu kỳ 6 tuần. | LOW | -0.0710 | **+0.2648** | ✅ Đúng |
| 3 | Lương được trả ở mức top 10% theo thị trường San Francisco. | 37signals trả lương theo mức cao nhất ngành tại San Francisco. | HIGH | -0.0645 | **+0.6504** | ✅ Đúng |
| 4 | Mọi người được khuyến khích làm ca hỗ trợ khách hàng. | Quản lý thiết bị Mac được thực hiện qua Kandji. | LOW | +0.0334 | **+0.3040** | ⚠️ Gần ngưỡng |
| 5 | Nghỉ phép dài hạn 6 tuần sau mỗi 3 năm. | Sabbatical kéo dài 6 tuần được cung cấp cho nhân viên. | HIGH | +0.0124 | **+0.6628** | ✅ Đúng |

**So sánh Mock vs OpenAI:**
> - **Mock embeddings: 2/5 dự đoán đúng** — Hash-based embeddings hoàn toàn không hiểu ngữ nghĩa. Pair 1, 3, 5 dù cùng ý nghĩa nhưng score gần 0 vì text khác nhau → hash khác nhau.
> - **OpenAI embeddings: 4/5 dự đoán đúng** — Model hiểu semantic: "nghỉ phép 20 ngày" ↔ "20 ngày nghỉ phép" đạt 0.85, "sabbatical 6 tuần" ↔ "6 tuần nghỉ phép" đạt 0.66.
> - **Pair 4 bất ngờ:** OpenAI cho score 0.30 (dự đoán LOW) — cao hơn kỳ vọng vì cả 2 câu đều liên quan đến "hoạt động công ty" dù topic khác nhau. Cho thấy semantic embeddings capture cả broad topic similarity, không chỉ exact topic match.

**Bài học quan trọng:**  
> Embedding model quality quyết định khả năng hiểu ngữ nghĩa. Mock embeddings (hash-based) hoàn toàn random, OpenAI embeddings phản ánh chính xác semantic similarity. Đây là foundation quan trọng nhất cho RAG — nếu embeddings không tốt, chunking strategy dù tốt cũng không cứu được.

---

## 6. Results — Cá nhân (10 điểm)

### Setup

- **Embedding model:** OpenAI `text-embedding-3-small`
- **Chunking strategy:** RecursiveChunker (chunk_size=500) — 9 files → 72 chunks
- **Search:** Top-3, in-memory dot product

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Nhân viên được nghỉ phép bao nhiêu ngày mỗi năm? | 20 ngày nghỉ phép + 11 ngày lễ. Tối đa tích lũy 27 ngày. |
| 2 | Công ty có chính sách gì về làm thêm ngoài giờ? | Cho phép công việc phụ thỉnh thoảng, diễn thuyết, kinh doanh phụ vài giờ/tuần. Không được làm cho đối thủ. |
| 3 | Nhân viên mới cần gặp ai trong tuần đầu tiên? | Quản lý, nhóm, buddy 37signals, và People Ops (Andrea). |
| 4 | Mức lương tối thiểu và cách tính lương tại công ty? | Lương tối thiểu $73,500. Top 10% San Francisco. Cùng role cùng level trả như nhau. |
| 5 | Công ty dùng hệ thống nào để theo dõi lỗi lập trình? | Sentry theo dõi lỗi. Grafana giám sát hệ thống. Dash cho logging. |

### Kết Quả Của Tôi (OpenAI + RecursiveChunker)

| # | Query | Top-1 Retrieved Chunk | Score | Relevant? | Top-3 all relevant? |
|---|-------|-----------------------|-------|-----------|---------------------|
| 1 | Nghỉ phép bao nhiêu ngày? | phuc_loi_va_quyen_loi — "Ngoài PTO và ngày lễ hàng năm, cứ mỗi ba năm..." | 0.7139 | ✅ Đúng doc, đúng topic | ✅ Top-3 đều từ phuc_loi |
| 2 | Chính sách làm thêm ngoài giờ? | lam_them_ngoai_gio — "# Lưu Ý Về Việc Làm Thêm Ngoài Giờ..." | 0.6749 | ✅ Đúng doc, đúng topic | ✅ Top-3 đều từ moonlighting |
| 3 | Nhân viên mới gặp ai? | bat_dau_lam_viec — "Quản lý của bạn. Bạn và quản lý sẽ gặp vào ngày đầu tiên..." | 0.5889 | ✅ Đúng doc, đúng topic | ✅ Top-2 từ bat_dau |
| 4 | Mức lương tối thiểu? | phat_trien_nghe_nghiep — "Dữ liệu Radford được xem xét mỗi năm..." | 0.4962 | ✅ Đúng doc, đúng topic | ✅ Top-2 từ career |
| 5 | Hệ thống theo dõi lỗi? | he_thong_noi_bo — "Chúng tôi theo dõi lỗi lập trình trên Sentry..." | 0.5167 | ✅ Đúng doc, đúng topic | ✅ Top-1 chứa chính xác Sentry |

**Bao nhiêu queries trả về chunk relevant trong top-3?** **5 / 5** ✅

### So Sánh Trước vs Sau: Mock → OpenAI + Chunking

| # | Query | Mock (no chunk) | OpenAI + Chunking | Cải thiện |
|---|-------|----------------|-------------------|----------|
| 1 | Nghỉ phép | ❌ Top-1 sai (career, 0.08) | ✅ Top-1 đúng (benefits, **0.71**) | Score: ×9 |
| 2 | Làm thêm | ⚠️ Top-3 đúng (0.02) | ✅ Top-1 đúng (**0.67**) | Score: ×33 |
| 3 | Nhân viên mới | ❌ Top-1 sai (systems, 0.15) | ✅ Top-1 đúng (onboarding, **0.59**) | Score: ×4 |
| 4 | Mức lương | ❌ Top-1 sai (onboarding, 0.14) | ✅ Top-1 đúng (career, **0.50**) | Score: ×4 |
| 5 | Theo dõi lỗi | ❌ Top-1 sai (moonlighting, 0.16) | ✅ Top-1 đúng (systems, **0.52**) | Score: ×3 |
| | **Tổng** | **1/5 in Top-3** | **5/5 in Top-1** | **🎉** |

### Retrieval Precision Analysis (EVALUATION Metric #1)

**Chấm điểm theo rubric (2 điểm/query):**

| # | Query | Top-3 relevant? | Agent answer chính xác? | Điểm |
|---|-------|-----------------|------------------------|------|
| 1 | Nghỉ phép bao nhiêu ngày? | ✅ Top-1, 2, 3 đều relevant | ✅ Context chứa "20 ngày nghỉ phép" | **2 / 2** |
| 2 | Chính sách làm thêm? | ✅ Top-1, 2, 3 đều relevant | ✅ Context chứa "không được làm cho đối thủ" | **2 / 2** |
| 3 | Nhân viên mới gặp ai? | ✅ Top-1, 2 relevant | ✅ Context chứa "quản lý, buddy, People Ops" | **2 / 2** |
| 4 | Mức lương tối thiểu? | ✅ Top-1, 2 relevant | ✅ Context chứa "top 10% San Francisco" | **2 / 2** |
| 5 | Hệ thống theo dõi lỗi? | ✅ Top-1 relevant | ✅ Context chứa "Sentry, Grafana" | **2 / 2** |
| | | | **Tổng Retrieval Quality:** | **10 / 10** |

**Score Distribution Analysis:**

| # | Top-1 Score | Top-2 Score | Top-3 Score | Gap (Top1-Top3) | Phân biệt? |
|---|------------|------------|------------|-----------------|-----------|
| 1 | 0.7139 | 0.6552 | 0.6020 | 0.1119 | ✅ Relevant docs cluster ở 0.6-0.7, noise ở ~0.4 |
| 2 | 0.6749 | 0.6425 | 0.5783 | 0.0966 | ✅ Top-3 đều relevant, gap rõ với noise |
| 3 | 0.5889 | 0.5539 | 0.5363 | 0.0526 | ✅ Top-2 relevant, Top-3 là doc khác nhưng score gần |
| 4 | 0.4962 | 0.4826 | 0.4405 | 0.0557 | ⚠️ Gap nhỏ hơn, nhưng Top-1,2 đúng |
| 5 | 0.5167 | 0.4471 | 0.4460 | 0.0707 | ✅ Top-1 tách biệt rõ |

> **Nhận xét:** Score distribution với OpenAI embeddings phân biệt tốt hơn rất nhiều so với mock. Scores nằm trong range [0.44, 0.71] — rộng hơn mock [−0.07, 0.16]. Relevant documents cluster ở vùng score cao hơn, giúp phân biệt rõ ràng giữa kết quả relevant và noise.

### Metadata Utility Analysis (EVALUATION Metric #3)

**So sánh A/B: `search()` vs `search_with_filter()` — OpenAI embeddings**

**Query test:** "Công ty có chính sách gì về làm thêm ngoài giờ?"

| | `search()` (không filter) | `search_with_filter(category=policy)` |
|---|--------------------------|--------------------------------------|
| Top-1 | lam_them_ngoai_gio (score=0.6748) ✅ | lam_them_ngoai_gio (score=0.6749) ✅ |
| Top-2 | lam_them_ngoai_gio (score=0.6425) ✅ | lam_them_ngoai_gio (score=0.6425) ✅ |
| Top-3 | lam_them_ngoai_gio (score=0.5783) ✅ | lam_them_ngoai_gio (score=0.5784) ✅ |

**Filter Effectiveness:**
> - Với OpenAI embeddings, `search()` không filter đã cho kết quả xuất sắc (Top-3 đều đúng). Filter `category=policy` cho kết quả tương đương — vì embedding model đã đủ mạnh để rank đúng.
> - Filter hữu ích hơn trong 2 trường hợp: (1) embedding model yếu hơn, (2) search space rất lớn (ngàn documents) — filter giảm search space, tăng tốc và giảm noise.

**Recall Trade-off:**
> - Filter `category=benefits` cho query trên → không trả về document đúng (lam_them_ngoai_gio có category=policy). **Filter SAI category sẽ mất kết quả tốt.**
> - Bài học: metadata filter là "double-edged sword" — hiệu quả khi intent mapping chính xác, nhưng gây hại khi mapping sai. Cần intent detection hoặc cho user chọn category.

### Grounding Quality Analysis (EVALUATION Metric #4)

**Kiểm tra: Agent answer có dựa trên retrieved context hay bịa?**

| # | Query | Context đúng? | Agent dựa trên context? | Source traceable? |
|---|-------|--------------|------------------------|------------------|
| 1 | Nghỉ phép bao nhiêu ngày? | ✅ Context chứa "20 ngày nghỉ phép" | ✅ Agent trích dẫn đúng | ✅ [1] phuc_loi_va_quyen_loi |
| 2 | Chính sách làm thêm? | ✅ Context chứa "không được làm cho đối thủ" | ✅ Agent trích dẫn đúng | ✅ [1] lam_them_ngoai_gio |
| 3 | Nhân viên mới gặp ai? | ✅ Context chứa "quản lý, buddy" | ✅ Agent trích dẫn đúng | ✅ [1] bat_dau_lam_viec |
| 4 | Mức lương tối thiểu? | ✅ Context chứa "top 10% SF" | ✅ Agent trích dẫn đúng | ✅ [1] phat_trien_nghe_nghiep |
| 5 | Hệ thống theo dõi lỗi? | ✅ Context chứa "Sentry" | ✅ Agent trích dẫn đúng | ✅ [1] he_thong_noi_bo |

**Kết luận Grounding Quality:**
> - **Source Traceability: ✅ TỐT** — Prompt structure `[1] chunk1 [2] chunk2 ...` cho phép trace rõ ràng chunk nào được dùng.
> - **Factual Accuracy: ✅ TỐT** — Với OpenAI embeddings + chunking, context retrieved đúng topic → agent trả lời chính xác. RAG agent quality = retrieval quality.
> - **Insight:** Agent không hallucinate (bịa) — nó faithful với context. Khi retrieval đúng (OpenAI) → answer đúng. Khi retrieval sai (mock) → answer sai. **RAG system chỉ tốt bằng retrieval.**

### Data Strategy Impact (EVALUATION Metric #5)

| Khía cạnh | Đánh giá | Chi tiết |
|-----------|---------|----------|
| Document Selection | ✅ Tốt | 9 docs đủ đa dạng (6 categories), mỗi doc có chủ đề rõ ràng, queries có gold answers cụ thể |
| Metadata Design | ✅ Tốt | 3 trường (category, topic, language) — category filter hoạt động, giảm search space |
| Chunking Rationale | ✅ Tốt | RecursiveChunker khai thác cấu trúc sections/paragraphs của handbook. 4 advanced strategies bổ sung để so sánh |
| Embedding Model | ✅ Đột phá | OpenAI `text-embedding-3-small` cải thiện retrieval từ 1/5 → 5/5. **Embedding quality là yếu tố quan trọng nhất** |

> **So sánh giữa các thành viên:** Cùng bộ tài liệu, cùng 5 queries. Với OpenAI embeddings, sự khác biệt retrieval score giữa các strategy chỉ ~0.03 (0.58-0.62). Điều này cho thấy **embedding model quality** quan trọng hơn chunking strategy. Tuy nhiên, chunking strategy vẫn ảnh hưởng đến Avg Top-1 score: Agentic (0.62) > DocStructure (0.61) > Recursive (0.60) > ParentChild (0.59).

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Chunking strategy phải phù hợp với cấu trúc dữ liệu. Với handbook có sections rõ ràng, RecursiveChunker và DocStructureChunker cho kết quả tốt nhất — nhưng AgenticChunker vượt trội vì nó hiểu ngữ nghĩa, không chỉ dựa vào format. Trade-off giữa quality, speed, và cost là bài học chính: Agentic cho quality cao nhất nhưng chậm và tốn API, Recursive cho quality gần bằng nhưng miễn phí và nhanh.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Metadata filtering cực kỳ hữu ích khi embedding model yếu hoặc search space lớn. Với OpenAI embeddings trên tập 72 chunks nhỏ, filter KHÔNG cải thiện đáng kể. Nhưng trong production với hàng ngàn documents, filter giảm search space là bắt buộc.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> (1) **Bắt đầu với embedder thật từ đầu** — phát hiện mock embeddings đang cản trở toàn bộ pipeline. Embedding quality > chunking strategy. (2) **Chunking trước khi embed luôn** — document dài bị "pha loãng" embedding, chunks nhỏ focused hơn. (3) **Thử hybrid search** — kết hợp keyword (BM25) với semantic search để bù cho edge cases.

### Failure Analysis (Exercise 3.5)

**Failure case với OpenAI + Chunking:**

**Query:** "Mức lương tối thiểu và cách tính lương tại công ty là gì?"

**Mô tả failure:**
> - Top-1 chunk (score=0.4962) chứa thông tin về "Dữ liệu Radford" và "xem xét mỗi năm" — relevant nhưng KHÔNG chứa trực tiếp con số "$73,500".
> - Chunk chứa "$73,500" nằm ở Top-2 (score=0.4826) — gần nhưng không phải Top-1.
> - Gap giữa Top-1 và Top-2 chỉ 0.014 — rất nhỏ, cho thấy model không phân biệt rõ.

**Tại sao thất bại?**
> - **Chunk boundary:** RecursiveChunker tách "salary calculation" và "minimum salary" thành 2 chunks khác nhau vì chúng ở 2 paragraphs khác nhau trong source.
> - **Query specificity:** Query hỏi 2 thứ ("mức lương tối thiểu" + "cách tính") → cần thông tin từ 2 chunks. Không chunk nào chứa đủ cả 2.
> - **Score: 0.496** — thấp nhất trong 5 queries, cho thấy multi-aspect queries khó hơn single-aspect.

**Đề xuất cải thiện:**
> 1. **Query decomposition:** Tách query thành sub-queries ("mức lương tối thiểu là bao nhiêu?" + "cách tính lương thế nào?"), search riêng rồi merge.
> 2. **Larger chunks or overlap:** Tăng chunk_size hoặc thêm overlap để 2 paragraphs liên quan nằm cùng chunk.
> 3. **Re-ranking:** Dùng cross-encoder re-rank Top-10 results thay vì chỉ dựa vào bi-encoder similarity.
> 4. **ParentChildChunker:** Dùng children cho precise search, parent cho full context — giải quyết vấn đề split information.

**Failure case cũ (Mock embeddings) — để so sánh:**
> Với mock embeddings, Query 1 ("Nghỉ phép bao nhiêu ngày?") trả về `phat_trien_nghe_nghiep.md` (career development) — hoàn toàn sai document. Root cause: mock embeddings tạo vector dựa trên hash MD5, không hiểu ngữ nghĩa → retrieval gần như random. Chuyển sang OpenAI embeddings giải quyết triệt để vấn đề này.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 9 / 10 |
| Chunking strategy | Nhóm | 14 / 15 |
| My approach | Cá nhân | 9 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results (retrieval quality 10/10) | Cá nhân | 10 / 10 |
| Core implementation (42/42 tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 4 / 5 |
| **Tổng** | | **86 / 100** |
