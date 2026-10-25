"""Context distillation: merges overlapping chunks and enforces token/character budgets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from whycode.ingest.chunker import CodeChunk
from whycode.retrieval.lexical import RetrievalResult


@dataclass(frozen=True, slots=True)
class DistilledSource:
    """A contiguous, deduplicated block of source code for context building."""

    source_id: int
    file_path: str
    start_line: int
    end_line: int
    content: str


@dataclass(frozen=True, slots=True)
class DistilledContext:
    """Formatted text context and list of distilled sources within budget."""

    text: str
    sources: tuple[DistilledSource, ...]
    total_chars: int
    truncated: bool


class ContextDistiller:
    """Consolidate overlapping code chunks into contiguous spans and enforce size budgets."""

    def __init__(self, max_context_chars: int = 15_000) -> None:
        if max_context_chars <= 0:
            raise ValueError("max_context_chars must be positive.")
        self.max_context_chars = max_context_chars

    def distill(self, results: Sequence[RetrievalResult]) -> DistilledContext:
        """Merge overlapping results per file and construct formatted LLM context."""
        if not results:
            return DistilledContext(
                text="",
                sources=(),
                total_chars=0,
                truncated=False,
            )

        # Group chunks by file path preserving first-seen file order
        file_order: list[str] = []
        chunks_by_file: dict[str, list[CodeChunk]] = {}

        for res in results:
            path = res.chunk.file_path
            if path not in chunks_by_file:
                chunks_by_file[path] = []
                file_order.append(path)
            chunks_by_file[path].append(res.chunk)

        distilled_sources: list[DistilledSource] = []
        source_counter = 1

        for path in file_order:
            file_chunks = chunks_by_file[path]
            # Sort chunks by start_line
            sorted_chunks = sorted(file_chunks, key=lambda c: (c.start_line, c.end_line))
            merged = self._merge_file_chunks(sorted_chunks)

            for span_start, span_end, span_content in merged:
                distilled_sources.append(
                    DistilledSource(
                        source_id=source_counter,
                        file_path=path,
                        start_line=span_start,
                        end_line=span_end,
                        content=span_content,
                    )
                )
                source_counter += 1

        # Format sources into context blocks while respecting character budget
        formatted_blocks: list[str] = []
        included_sources: list[DistilledSource] = []
        current_chars = 0
        truncated = False

        for ds in distilled_sources:
            block = (
                f"Source {ds.source_id}\n"
                f"File: {ds.file_path}\n"
                f"Lines: {ds.start_line}-{ds.end_line}\n"
                f"Code:\n"
                f"```text\n{ds.content}\n```"
            )
            block_len = len(block) + (2 if formatted_blocks else 0)

            if current_chars + block_len <= self.max_context_chars:
                formatted_blocks.append(block)
                included_sources.append(ds)
                current_chars += block_len
            else:
                # If budget exceeded, stop adding more blocks
                truncated = True
                break

        full_text = "\n\n".join(formatted_blocks)
        return DistilledContext(
            text=full_text,
            sources=tuple(included_sources),
            total_chars=len(full_text),
            truncated=truncated,
        )

    @staticmethod
    def _merge_file_chunks(
        sorted_chunks: list[CodeChunk],
    ) -> list[tuple[int, int, str]]:
        """Merge overlapping or adjacent chunks from the same file into contiguous line spans."""
        if not sorted_chunks:
            return []

        merged_spans: list[tuple[int, int, str]] = []
        curr_start = sorted_chunks[0].start_line
        curr_end = sorted_chunks[0].end_line
        curr_lines = sorted_chunks[0].content.splitlines()

        for chunk in sorted_chunks[1:]:
            # If chunk overlaps or is immediately adjacent
            if chunk.start_line <= curr_end + 1:
                # If chunk extends beyond current end
                if chunk.end_line > curr_end:
                    chunk_lines = chunk.content.splitlines()
                    # Calculate how many new lines to append
                    offset = curr_end - chunk.start_line + 1
                    new_lines = chunk_lines[offset:]
                    curr_lines.extend(new_lines)
                    curr_end = chunk.end_line
            else:
                # Disjoint span: record current and start new
                merged_spans.append((curr_start, curr_end, "\n".join(curr_lines)))
                curr_start = chunk.start_line
                curr_end = chunk.end_line
                curr_lines = chunk.content.splitlines()

        merged_spans.append((curr_start, curr_end, "\n".join(curr_lines)))
        return merged_spans
