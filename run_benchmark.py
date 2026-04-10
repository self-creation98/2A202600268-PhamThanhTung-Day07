"""
Benchmark script for Lab 7 — Complete comparison of ALL chunking strategies.

  PART 1: Similarity Predictions (Mock vs OpenAI)
  PART 2: Chunking Statistics (count, avg_length for all strategies)
  PART 3: Retrieval Comparison — 7 strategies × OpenAI embeddings
  PART 4: Mock vs OpenAI on primary strategy (Recursive)
  PART 5: Metadata Filter test
"""
from __future__ import annotations
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from src.chunking import (
    compute_similarity,
    FixedSizeChunker,
    SentenceChunker,
    RecursiveChunker,
    SemanticChunker,
    DocStructureChunker,
    AgenticChunker,
    ParentChildChunker,
)
from src.embeddings import _mock_embed, OpenAIEmbedder
from src.models import Document
from src.store import EmbeddingStore
from src.agent import KnowledgeBaseAgent

# ── Shared data ──────────────────────────────────────────────
handbook_data = [
    {"file": "data/phuc_loi_va_quyen_loi.md", "category": "benefits", "language": "vi", "topic": "insurance_leave_retirement"},
    {"file": "data/bat_dau_lam_viec.md", "category": "onboarding", "language": "vi", "topic": "getting_started"},
    {"file": "data/cach_lam_viec.md", "category": "culture", "language": "vi", "topic": "remote_work_communication"},
    {"file": "data/phat_trien_nghe_nghiep.md", "category": "career", "language": "vi", "topic": "titles_salary_reviews"},
    {"file": "data/lam_them_ngoai_gio.md", "category": "policy", "language": "vi", "topic": "moonlighting"},
    {"file": "data/nghi_viec_va_tro_cap.md", "category": "policy", "language": "vi", "topic": "severance"},
    {"file": "data/nghi_le_va_truyen_thong.md", "category": "culture", "language": "vi", "topic": "rituals_meetups"},
    {"file": "data/he_thong_noi_bo.md", "category": "systems", "language": "vi", "topic": "internal_tools"},
    {"file": "data/quan_ly_thiet_bi.md", "category": "policy", "language": "vi", "topic": "device_management"},
]

queries = [
    {"query": "Nhân viên được nghỉ phép bao nhiêu ngày mỗi năm?",
     "gold": "20 ngày nghỉ phép + 11 ngày lễ. Tối đa tích lũy 27 ngày.",
     "gold_source": "phuc_loi_va_quyen_loi"},
    {"query": "Công ty có chính sách gì về làm thêm ngoài giờ?",
     "gold": "Cho phép công việc phụ thỉnh thoảng. Không được làm cho đối thủ.",
     "gold_source": "lam_them_ngoai_gio"},
    {"query": "Nhân viên mới cần gặp ai trong tuần đầu tiên?",
     "gold": "Quản lý, nhóm, buddy 37signals, và People Ops (Andrea).",
     "gold_source": "bat_dau_lam_viec"},
    {"query": "Mức lương tối thiểu và cách tính lương tại công ty là gì?",
     "gold": "Lương tối thiểu $73,500. Top 10% San Francisco.",
     "gold_source": "phat_trien_nghe_nghiep"},
    {"query": "Công ty sử dụng hệ thống nội bộ nào để theo dõi lỗi?",
     "gold": "Sentry theo dõi lỗi. Grafana giám sát. Dash cho logging.",
     "gold_source": "he_thong_noi_bo"},
]

# Load raw files
raw_files = {}
for entry in handbook_data:
    p = Path(entry["file"])
    if p.exists():
        raw_files[p.stem] = {"content": p.read_text(encoding="utf-8"), **entry}

print(f"Loaded {len(raw_files)} handbook files")

# Initialize OpenAI embedder (used for semantic chunker + retrieval)
openai_embedder = OpenAIEmbedder()


def chunk_to_docs(chunker, raw_files_dict):
    """Chunk all files with a given chunker and return list of Documents."""
    docs = []
    for stem, info in raw_files_dict.items():
        chunks = chunker.chunk(info["content"])
        for idx, chunk_text in enumerate(chunks):
            docs.append(Document(
                id=f"{stem}_chunk{idx}",
                content=chunk_text,
                metadata={
                    "source": info["file"],
                    "category": info["category"],
                    "language": info["language"],
                    "topic": info["topic"],
                    "chunk_index": idx,
                    "parent_doc": stem,
                }
            ))
    return docs


def eval_retrieval(store, queries_list):
    """Run queries against a store, return (hits, details)."""
    hits = 0
    details = []
    for i, q in enumerate(queries_list, 1):
        results = store.search(q["query"], top_k=3)
        hit = False
        top_info = []
        for j, r in enumerate(results, 1):
            parent = r["metadata"].get("parent_doc", "?")
            ok = q["gold_source"] in parent
            if ok:
                hit = True
            top_info.append({
                "rank": j, "ok": ok, "score": r["score"],
                "parent": parent, "preview": r["content"][:70].replace("\n", " "),
            })
        if hit:
            hits += 1
        details.append({"query_idx": i, "hit": hit, "top": top_info})
    return hits, details


# ============================================================
# PART 1: Similarity Predictions (Exercise 3.3)
# ============================================================
print("\n" + "=" * 70)
print("PART 1: SIMILARITY PREDICTIONS — Mock vs OpenAI")
print("=" * 70)

pairs = [
    ("Nhân viên được nghỉ phép 20 ngày mỗi năm.", "Công ty cung cấp 20 ngày nghỉ phép hàng năm cho nhân viên.", "HIGH"),
    ("Bảo hiểm y tế được cung cấp qua Blue Cross Blue Shield.", "Chúng tôi làm việc theo chu kỳ 6 tuần.", "LOW"),
    ("Lương được trả ở mức top 10% theo thị trường San Francisco.", "37signals trả lương theo mức cao nhất ngành tại San Francisco.", "HIGH"),
    ("Mọi người được khuyến khích làm ca hỗ trợ khách hàng.", "Quản lý thiết bị Mac được thực hiện qua Kandji.", "LOW"),
    ("Nghỉ phép dài hạn 6 tuần sau mỗi 3 năm.", "Sabbatical kéo dài 6 tuần được cung cấp cho nhân viên.", "HIGH"),
]

for i, (a, b, expected) in enumerate(pairs, 1):
    mock_score = compute_similarity(_mock_embed(a), _mock_embed(b))
    oai_score = compute_similarity(openai_embedder(a), openai_embedder(b))
    print(f"\n  Pair {i} (expected {expected}):")
    print(f"    A: {a}")
    print(f"    B: {b}")
    print(f"    Mock:   {mock_score:+.4f}  |  OpenAI: {oai_score:+.4f}")

# ============================================================
# PART 2: Chunking Statistics
# ============================================================
print("\n" + "=" * 70)
print("PART 2: CHUNKING STATISTICS — All 7 Strategies")
print("=" * 70)

# Define all strategies
all_strategies = {
    # ── Basic (src/chunking.py) ──
    "1. FixedSize(500)":      FixedSizeChunker(chunk_size=500, overlap=50),
    "2. Sentence(3)":         SentenceChunker(max_sentences_per_chunk=3),
    "3. Recursive(500)":      RecursiveChunker(chunk_size=500),
    # ── Advanced (src/strategies/) ──
    "4. Semantic":            SemanticChunker(embedding_fn=openai_embedder, similarity_threshold=0.5, max_chunk_size=600),
    "5. DocStructure":        DocStructureChunker(max_chunk_size=800),
    "6. Agentic":             AgenticChunker(llm_fn=None, max_chunk_size=800),  # No LLM for stats
    "7. ParentChild":         ParentChildChunker(parent_chunk_size=800, child_chunk_size=200),
}

# Show stats on a sample doc
sample_stem = "phuc_loi_va_quyen_loi"
sample_text = raw_files[sample_stem]["content"]
print(f"\n  Sample: {sample_stem}.md ({len(sample_text)} chars)\n")
print(f"  {'Strategy':<22s} {'Chunks':>6s} {'Avg Len':>8s}")
print(f"  {'─' * 40}")

for name, chunker in all_strategies.items():
    chunks = chunker.chunk(sample_text)
    count = len(chunks)
    avg = sum(len(c) for c in chunks) / count if count else 0
    print(f"  {name:<22s} {count:>6d} {avg:>8.0f}")

# ============================================================
# PART 3: Retrieval Comparison — All strategies × OpenAI
# ============================================================
print("\n" + "=" * 70)
print("PART 3: RETRIEVAL COMPARISON — 7 Strategies × OpenAI Embeddings")
print("=" * 70)

strategy_results = {}

for name, chunker in all_strategies.items():
    print(f"\n  Building: {name}...", end=" ", flush=True)
    docs = chunk_to_docs(chunker, raw_files)
    store = EmbeddingStore(collection_name=f"strat_{name}", embedding_fn=openai_embedder)
    store.add_documents(docs)
    hits, details = eval_retrieval(store, queries)
    strategy_results[name] = {"hits": hits, "chunks": len(docs), "details": details}
    print(f"{len(docs)} chunks → {hits}/5 hit")

# Detailed per-query comparison
print(f"\n{'─' * 70}")
print("  Per-query Top-1 results:")
for i, q in enumerate(queries, 1):
    print(f"\n  Q{i}: {q['query']}")
    print(f"      Gold: {q['gold_source']}")
    for name in all_strategies:
        d = strategy_results[name]["details"][i - 1]
        top1 = d["top"][0]
        marker = "✅" if d["hit"] else "❌"
        print(f"      {name:<22s}: {marker} Top-1={top1['parent']:<28s} ({top1['score']:.4f})")

# ============================================================
# PART 4: Mock vs OpenAI on RecursiveChunker (primary strategy)
# ============================================================
print("\n" + "=" * 70)
print("PART 4: MOCK vs OPENAI — RecursiveChunker (primary strategy)")
print("=" * 70)

recursive_docs = chunk_to_docs(RecursiveChunker(chunk_size=500), raw_files)
print(f"\n  {len(recursive_docs)} chunks")

store_mock = EmbeddingStore(collection_name="mock_rec", embedding_fn=_mock_embed)
store_mock.add_documents(recursive_docs)
mock_hits, mock_details = eval_retrieval(store_mock, queries)

openai_hits = strategy_results["3. Recursive(500)"]["hits"]
openai_details = strategy_results["3. Recursive(500)"]["details"]

for i, q in enumerate(queries, 1):
    md = mock_details[i - 1]
    od = openai_details[i - 1]
    print(f"\n  Q{i}: {q['query']}")
    print(f"    📦 Mock:   {'✅' if md['hit'] else '❌'} Top-1={md['top'][0]['parent']} ({md['top'][0]['score']:.4f})")
    print(f"    🤖 OpenAI: {'✅' if od['hit'] else '❌'} Top-1={od['top'][0]['parent']} ({od['top'][0]['score']:.4f})")

# ============================================================
# PART 5: Metadata Filter
# ============================================================
print(f"\n{'=' * 70}")
print("PART 5: METADATA FILTER — OpenAI + RecursiveChunker")
print("=" * 70)

store_filter = EmbeddingStore(collection_name="filter_oai", embedding_fn=openai_embedder)
store_filter.add_documents(recursive_docs)

filter_query = "Công ty có chính sách gì về làm thêm ngoài giờ?"
print(f"\n  Query: {filter_query}")

print("\n  No filter:")
for j, r in enumerate(store_filter.search(filter_query, top_k=3), 1):
    print(f"    Top-{j}: score={r['score']:.4f} | {r['metadata'].get('parent_doc','')} ({r['metadata'].get('category','')})")

print("\n  Filter: category=policy")
for j, r in enumerate(store_filter.search_with_filter(filter_query, top_k=3, metadata_filter={"category": "policy"}), 1):
    print(f"    Top-{j}: score={r['score']:.4f} | {r['metadata'].get('parent_doc','')} ({r['metadata'].get('topic','')})")

# ============================================================
# FINAL SUMMARY
# ============================================================
print(f"\n{'═' * 70}")
print("FINAL SUMMARY")
print(f"{'═' * 70}")

print("\n  📊 Strategy Comparison (OpenAI embeddings):")
print(f"  {'Strategy':<22s} {'Chunks':>6s} {'Hit':>5s} {'Avg Top-1':>10s}")
print(f"  {'─' * 48}")

for name, res in strategy_results.items():
    avg_top1 = sum(d["top"][0]["score"] for d in res["details"]) / len(res["details"])
    print(f"  {name:<22s} {res['chunks']:>6d} {res['hits']:>3d}/5 {avg_top1:>10.4f}")

print(f"\n  📊 Embedding Comparison (RecursiveChunker):")
print(f"    Mock:   {mock_hits}/5 hit")
print(f"    OpenAI: {openai_hits}/5 hit")

best = max(strategy_results, key=lambda k: (strategy_results[k]["hits"],
    sum(d["top"][0]["score"] for d in strategy_results[k]["details"])))
print(f"\n  🏆 Best: {best} — {strategy_results[best]['hits']}/5 hit")
print("\nDone!")
