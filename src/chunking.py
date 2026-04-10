from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        # Split on sentence boundaries: ". ", "! ", "? ", or ".\n"
        # We use a regex that splits but keeps the delimiter with the preceding sentence
        sentences = re.split(r'(?<=[.!?])(?:\s|\n)', text)
        # Remove empty strings and strip whitespace
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return []

        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunk = " ".join(group).strip()
            if chunk:
                chunks.append(chunk)

        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        results = self._split(text, self.separators)
        # Filter out empty strings
        return [c for c in results if c.strip()]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case: text fits within chunk_size
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Base case: no more separators — force-split by character
        if not remaining_separators:
            chunks = []
            for i in range(0, len(current_text), self.chunk_size):
                chunks.append(current_text[i : i + self.chunk_size])
            return chunks

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        # If separator is empty string, force character-level split
        if separator == "":
            chunks = []
            for i in range(0, len(current_text), self.chunk_size):
                chunks.append(current_text[i : i + self.chunk_size])
            return chunks

        # Split text by current separator
        parts = current_text.split(separator)

        # Merge small parts together, recurse on oversized ones
        results: list[str] = []
        current_chunk = ""

        for i, part in enumerate(parts):
            # Build candidate by adding separator back (except for last part)
            candidate = part if not current_chunk else current_chunk + separator + part

            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                # Flush current_chunk if it has content
                if current_chunk:
                    results.append(current_chunk)
                    current_chunk = ""

                # If the part itself is oversized, recurse with next separator
                if len(part) > self.chunk_size:
                    sub_chunks = self._split(part, next_separators)
                    results.extend(sub_chunks)
                else:
                    current_chunk = part

        # Don't forget the last accumulated chunk
        if current_chunk:
            results.append(current_chunk)

        return results


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_product = _dot(vec_a, vec_b)
    magnitude_a = math.sqrt(_dot(vec_a, vec_a))
    magnitude_b = math.sqrt(_dot(vec_b, vec_b))

    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=50),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        result = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count > 0 else 0
            result[name] = {
                "count": count,
                "avg_length": round(avg_length, 2),
                "chunks": chunks,
            }

        return result


# ============================================================
# Advanced Chunking Strategies (Exercise 3.1 — Custom Strategies)
# ============================================================


def _cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    dot_val = _dot(a, b)
    mag_a = math.sqrt(_dot(a, a))
    mag_b = math.sqrt(_dot(b, b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot_val / (mag_a * mag_b)


class SemanticChunker:
    """Chunk text by detecting semantic breakpoints between sentences.

    How it works:
      1. Split text into sentences
      2. Embed each sentence (OpenAI or any embedding function)
      3. Compute similarity between consecutive sentences
      4. Split at points where similarity drops below threshold
      5. Merge short segments together

    Best for: unstructured text without clear headers.
    """

    def __init__(
        self,
        embedding_fn=None,
        similarity_threshold: float = 0.5,
        min_chunk_size: int = 100,
        max_chunk_size: int = 800,
    ) -> None:
        self.embedding_fn = embedding_fn
        self.similarity_threshold = similarity_threshold
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        if self.embedding_fn is None:
            return [text] if len(text) <= self.max_chunk_size else self._force_split(text)

        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 1:
            return [text.strip()]

        embeddings = [self.embedding_fn(s) for s in sentences]

        similarities = []
        for i in range(len(embeddings) - 1):
            similarities.append(_cosine(embeddings[i], embeddings[i + 1]))

        breakpoints = [i + 1 for i, sim in enumerate(similarities) if sim < self.similarity_threshold]

        chunks: list[str] = []
        start = 0
        for bp in breakpoints:
            segment = " ".join(sentences[start:bp]).strip()
            if segment:
                chunks.append(segment)
            start = bp

        last = " ".join(sentences[start:]).strip()
        if last:
            chunks.append(last)

        return self._merge_small(chunks)

    def _merge_small(self, chunks: list[str]) -> list[str]:
        if not chunks:
            return []
        merged = [chunks[0]]
        for chunk in chunks[1:]:
            if len(merged[-1]) < self.min_chunk_size:
                merged[-1] = merged[-1] + " " + chunk
            elif len(chunk) < self.min_chunk_size and len(merged[-1]) + len(chunk) <= self.max_chunk_size:
                merged[-1] = merged[-1] + " " + chunk
            else:
                merged.append(chunk)
        return merged

    def _force_split(self, text: str) -> list[str]:
        return [text[i:i + self.max_chunk_size] for i in range(0, len(text), self.max_chunk_size)]


class DocStructureChunker:
    """Chunk markdown text by its heading structure.

    How it works:
      1. Detect markdown headers (##, ###, etc.)
      2. Split text into sections at header boundaries
      3. If a section is too large, split paragraphs within it
      4. Each chunk preserves its header for context

    Best for: structured documents like handbooks, documentation.
    """

    def __init__(self, max_chunk_size: int = 800, min_header_level: int = 2) -> None:
        self.max_chunk_size = max_chunk_size
        self.min_header_level = min_header_level

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        if len(text) <= self.max_chunk_size:
            return [text.strip()]

        sections = self._split_by_headers(text)
        chunks: list[str] = []
        for header, body in sections:
            section_text = f"{header}\n\n{body}".strip() if header else body.strip()
            if len(section_text) <= self.max_chunk_size:
                if section_text:
                    chunks.append(section_text)
            else:
                chunks.extend(self._split_section(header, body))

        return [c for c in chunks if c.strip()]

    def _split_by_headers(self, text: str) -> list[tuple[str, str]]:
        pattern = r'^(#{' + str(self.min_header_level) + r',}\s+.+)$'
        lines = text.split('\n')
        sections: list[tuple[str, str]] = []
        current_header = ""
        current_body_lines: list[str] = []

        for line in lines:
            if re.match(pattern, line.strip()):
                if current_header or current_body_lines:
                    sections.append((current_header, '\n'.join(current_body_lines).strip()))
                current_header = line.strip()
                current_body_lines = []
            else:
                current_body_lines.append(line)

        if current_header or current_body_lines:
            sections.append((current_header, '\n'.join(current_body_lines).strip()))
        return sections

    def _split_section(self, header: str, body: str) -> list[str]:
        paragraphs = [p.strip() for p in body.split('\n\n') if p.strip()]
        chunks: list[str] = []
        current_chunk = header if header else ""

        for para in paragraphs:
            candidate = f"{current_chunk}\n\n{para}".strip() if current_chunk else para
            if len(candidate) <= self.max_chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                if header and len(f"{header}\n\n{para}") <= self.max_chunk_size:
                    current_chunk = f"{header}\n\n{para}"
                else:
                    current_chunk = ""
                    for i in range(0, len(para), self.max_chunk_size):
                        chunk = para[i:i + self.max_chunk_size]
                        chunks.append(f"{header}\n\n{chunk}" if header else chunk)

        if current_chunk:
            chunks.append(current_chunk)
        return chunks


_AGENTIC_PROMPT = """Bạn là trợ lý phân tích văn bản. Nhiệm vụ: quyết định đoạn mới có nên gộp vào cùng chunk với đoạn trước hay không.

Trả lời CHỈ MỘT từ:
- "SAME" nếu đoạn mới cùng chủ đề với chunk hiện tại
- "NEW" nếu đoạn mới là chủ đề khác, nên tách thành chunk mới

Không giải thích."""


class AgenticChunker:
    """Let an LLM decide chunk boundaries based on topic coherence.

    How it works:
      1. Split text into paragraphs
      2. For each paragraph, ask LLM: "SAME topic or NEW topic?"
      3. Merge paragraphs according to LLM decisions

    Best for: highest semantic accuracy, accepts API cost trade-off.
    """

    def __init__(self, llm_fn=None, max_chunk_size: int = 800) -> None:
        self.llm_fn = llm_fn
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        if len(text) <= self.max_chunk_size:
            return [text.strip()]

        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if not paragraphs:
            return [text.strip()]

        if self.llm_fn is None:
            return self._merge_by_size(paragraphs)

        chunks: list[str] = []
        current_chunk = paragraphs[0]

        for para in paragraphs[1:]:
            if len(current_chunk) + len(para) + 2 > self.max_chunk_size:
                chunks.append(current_chunk)
                current_chunk = para
                continue

            decision = self._ask_llm(current_chunk, para)
            if decision == "SAME":
                current_chunk = current_chunk + "\n\n" + para
            else:
                chunks.append(current_chunk)
                current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)
        return [c for c in chunks if c.strip()]

    def _ask_llm(self, current_chunk: str, new_paragraph: str) -> str:
        chunk_preview = current_chunk[-300:] if len(current_chunk) > 300 else current_chunk
        prompt = (
            f"{_AGENTIC_PROMPT}\n\n"
            f"--- CHUNK HIỆN TẠI (cuối) ---\n{chunk_preview}\n\n"
            f"--- ĐOẠN MỚI ---\n{new_paragraph}\n\n"
            f"Quyết định (SAME hoặc NEW):"
        )
        try:
            response = self.llm_fn(prompt).strip().upper()
            return "NEW" if "NEW" in response else "SAME"
        except Exception:
            return "SAME"

    def _merge_by_size(self, paragraphs: list[str]) -> list[str]:
        chunks: list[str] = []
        current = paragraphs[0]
        for para in paragraphs[1:]:
            if len(current) + len(para) + 2 <= self.max_chunk_size:
                current = current + "\n\n" + para
            else:
                chunks.append(current)
                current = para
        if current:
            chunks.append(current)
        return chunks


class ParentChildChunker:
    """Two-level hierarchical chunker: parents for context, children for search.

    How it works:
      1. Create PARENT chunks (large, ~800 chars) — used for LLM context
      2. Split each parent into CHILD chunks (small, ~200 chars) — used for search
      3. Each child stores reference to its parent

    Best for: precise search (child) + full context (parent) for LLM.
    """

    def __init__(
        self,
        parent_chunk_size: int = 800,
        child_chunk_size: int = 200,
        child_overlap: int = 30,
    ) -> None:
        self.parent_chunk_size = parent_chunk_size
        self.child_chunk_size = child_chunk_size
        self.child_overlap = child_overlap

    def chunk(self, text: str) -> list[str]:
        """Return child chunks (for compatibility with other chunkers)."""
        results = self.chunk_hierarchy(text)
        return [child["content"] for child in results["children"]]

    def chunk_hierarchy(self, text: str) -> dict:
        """Return full hierarchy with parents and children."""
        if not text or not text.strip():
            return {"parents": [], "children": []}

        parents = self._create_parents(text)
        all_children: list[dict] = []
        for parent in parents:
            all_children.extend(self._create_children(parent["content"], parent["id"]))

        return {"parents": parents, "children": all_children}

    def _create_parents(self, text: str) -> list[dict]:
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if not paragraphs:
            return [{"id": "p0", "content": text.strip()}]

        parents: list[dict] = []
        current = paragraphs[0]
        p_idx = 0

        for para in paragraphs[1:]:
            if len(current) + len(para) + 2 <= self.parent_chunk_size:
                current = current + "\n\n" + para
            else:
                parents.append({"id": f"p{p_idx}", "content": current})
                p_idx += 1
                current = para

        if current:
            parents.append({"id": f"p{p_idx}", "content": current})
        return parents

    def _create_children(self, parent_content: str, parent_id: str) -> list[dict]:
        if len(parent_content) <= self.child_chunk_size:
            return [{"id": f"{parent_id}_c0", "content": parent_content,
                      "parent_id": parent_id, "parent_content": parent_content}]

        children: list[dict] = []
        step = self.child_chunk_size - self.child_overlap
        c_idx = 0

        for start in range(0, len(parent_content), step):
            child_text = parent_content[start:start + self.child_chunk_size].strip()
            if child_text:
                children.append({"id": f"{parent_id}_c{c_idx}", "content": child_text,
                                  "parent_id": parent_id, "parent_content": parent_content})
                c_idx += 1
            if start + self.child_chunk_size >= len(parent_content):
                break

        return children
