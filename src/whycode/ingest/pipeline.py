from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from whycode.ingest.chunker import CodeChunk, CodeChunker
from whycode.ingest.scanner import (
    RepositoryScanner,
    SourceFile,
)


class IngestionError(Exception):
    """Raised when repository ingestion cannot complete safely."""


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Summary of the files and chunks produced from a repository."""

    repository_path: str
    files_scanned: int
    chunks_created: int
    chunks: tuple[CodeChunk, ...]


class RepositoryIngestionPipeline:
    """Scan a repository, read source files, and split them into chunks."""

    def __init__(
        self,
        repo_path: str | Path,
        scanner: RepositoryScanner | None = None,
        chunker: CodeChunker | None = None,
    ) -> None:
        self.repo_path = Path(repo_path).expanduser().resolve()
        self.scanner = scanner or RepositoryScanner(self.repo_path)
        self.chunker = chunker or CodeChunker()

    def ingest(self) -> IngestionResult:
        """Return chunks for readable files discovered by the scanner."""
        try:
            source_files: list[SourceFile] = self.scanner.scan()
        except Exception as exc:
            raise IngestionError(
                f"Could not scan repository: {exc}"
            ) from exc

        all_chunks: list[CodeChunk] = []

        for source_file in source_files:
            file_path = self.repo_path / source_file.path

            try:
                # Resolve again immediately before reading, so a path that
                # now points outside the repository is rejected.
                resolved_path = file_path.resolve(strict=True)
                resolved_path.relative_to(self.repo_path)

                if resolved_path.is_symlink() or not resolved_path.is_file():
                    continue

                if resolved_path.stat().st_size > source_file.size_bytes:
                    # The file grew after scanning; don't read unexpected data.
                    continue

                content = resolved_path.read_text(encoding="utf-8")

            except (OSError, UnicodeDecodeError, ValueError):
                # One file changing or becoming unreadable shouldn't stop
                # ingestion of the remaining files.
                continue

            all_chunks.extend(
                self.chunker.chunk_text(
                    file_path=source_file.path,
                    content=content,
                )
            )

        chunks = tuple(all_chunks)

        return IngestionResult(
            repository_path=str(self.repo_path),
            files_scanned=len(source_files),
            chunks_created=len(chunks),
            chunks=chunks,
        )
