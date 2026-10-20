
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import PurePosixPath, PureWindowsPath


@dataclass(frozen=True, slots=True)
class CodeChunk:
    """A traceable section of source code from a repository file."""

    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    content: str

    def __post_init__(self) -> None:
        if not self.chunk_id:
            raise ValueError("chunk_id cannot be empty.")
        if not self.file_path:
            raise ValueError("file_path cannot be empty.")
        if self.start_line < 1:
            raise ValueError("start_line must be at least 1.")
        if self.end_line < self.start_line:
            raise ValueError("end_line cannot be before start_line.")
        if not self.content:
            raise ValueError("content cannot be empty.")


def make_chunk_id(
    file_path: str,
    start_line: int,
    end_line: int,
    content: str,
) -> str:
    """Create a deterministic identifier for a chunk."""
    identity = (
        f"{file_path}\0{start_line}\0{end_line}\0{content}"
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ChunkerConfig:
    """Controls how source text is split into chunks."""

    max_lines: int = 80
    overlap_lines: int = 10

    def __post_init__(self) -> None:
        if self.max_lines < 1:
            raise ValueError("max_lines must be at least 1.")
        if self.overlap_lines < 0:
            raise ValueError("overlap_lines cannot be negative.")
        if self.overlap_lines >= self.max_lines:
            raise ValueError(
                "overlap_lines must be smaller than max_lines."
            )


class CodeChunker:
    """Split source text into overlapping, line-numbered chunks."""

    def __init__(
        self,
        config: ChunkerConfig | None = None,
    ) -> None:
        self.config = config or ChunkerConfig()

    def chunk_text(
        self,
        file_path: str,
        content: str,
    ) -> list[CodeChunk]:
        """Split text while preserving original one-based line numbers."""
        if not file_path or not file_path.strip():
            raise ValueError("file_path cannot be empty.")

        # Normalize Windows separators for consistent repository paths.
        normalized_path = file_path.replace("\\", "/")

        # Reject absolute paths on both Windows and POSIX systems.
        if (
            PurePosixPath(normalized_path).is_absolute()
            or PureWindowsPath(file_path).is_absolute()
            or PureWindowsPath(file_path).drive
        ):
            raise ValueError("file_path must be repository-relative.")

        if any(part == ".." for part in normalized_path.split("/")):
            raise ValueError(
                "file_path cannot traverse parent directories."
            )

        if not content or not content.strip():
            return []

        # splitlines() handles LF, CRLF and missing final newlines.
        lines = content.splitlines()
        if not lines or not any(line.strip() for line in lines):
            return []

        chunks: list[CodeChunk] = []
        start_index = 0

        while start_index < len(lines):
            end_index = min(
                start_index + self.config.max_lines,
                len(lines),
            )
            chunk_lines = lines[start_index:end_index]
            chunk_content = "\n".join(chunk_lines)

            # Never create chunks containing only whitespace.
            if chunk_content.strip():
                start_line = start_index + 1
                end_line = end_index

                chunks.append(
                    CodeChunk(
                        chunk_id=make_chunk_id(
                            normalized_path,
                            start_line,
                            end_line,
                            chunk_content,
                        ),
                        file_path=normalized_path,
                        start_line=start_line,
                        end_line=end_line,
                        content=chunk_content,
                    )
                )

            if end_index == len(lines):
                break

            start_index = end_index - self.config.overlap_lines

        return chunks
