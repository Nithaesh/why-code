
from __future__ import annotations

from whycode.retrieval.lexical import RetrievalResult


class ContextBuilder:
    """Format retrieved code chunks into source-labelled evidence."""

    def build(self, results: list[RetrievalResult]) -> str:
        """Build a context string from ranked retrieval results."""
        if not results:
            return ""

        sections: list[str] = []

        for index, result in enumerate(results, start=1):
            chunk = result.chunk

            section = (
                f"Source {index}\n"
                f"File: {chunk.file_path}\n"
                f"Lines: {chunk.start_line}-{chunk.end_line}\n"
                f"Code:\n"
                f"```text\n{chunk.content}\n```"
            )

            sections.append(section)

        return "\n\n".join(sections)
