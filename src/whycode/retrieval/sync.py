"""Incremental, change-aware synchronizer between repository files and persistent vector index."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import time

from whycode.ingest.chunker import CodeChunk, CodeChunker
from whycode.ingest.scanner import RepositoryScanner, SourceFile
from whycode.llm.embedding import BaseEmbedder
from whycode.retrieval.index import VectorIndex


@dataclass(frozen=True, slots=True)
class SyncStats:
    """Summary of operations performed during index synchronization."""

    added_files: int
    modified_files: int
    deleted_files: int
    unchanged_files: int
    total_chunks: int
    duration_seconds: float


class IndexSynchronizer:
    """Synchronize a repository's source code with a persistent VectorIndex.

    Only modified or newly added files are re-chunked and re-embedded.
    Deleted files are removed from the index.
    """

    def __init__(
        self,
        repo_path: str | Path,
        index: VectorIndex,
        embedder: BaseEmbedder,
        scanner: RepositoryScanner | None = None,
        chunker: CodeChunker | None = None,
    ) -> None:
        self.repo_path = Path(repo_path).expanduser().resolve()
        self.index = index
        self.embedder = embedder
        self.scanner = scanner or RepositoryScanner(self.repo_path)
        self.chunker = chunker or CodeChunker()

    @staticmethod
    def _hash_content(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def sync(self, force: bool = False) -> SyncStats:
        """Run change-aware sync. When force=True, rebuild index from scratch."""
        start_time = time.perf_counter()

        if force:
            self.index.clear()

        existing_indexed = self.index.get_indexed_files()
        scanned_files: list[SourceFile] = self.scanner.scan()
        scanned_paths: set[str] = {sf.path for sf in scanned_files}

        added = 0
        modified = 0
        unchanged = 0
        deleted = 0

        # Handle scanned files (additions, modifications, unchanged)
        for source_file in scanned_files:
            file_abs_path = self.repo_path / source_file.path

            try:
                resolved = file_abs_path.resolve(strict=True)
                resolved.relative_to(self.repo_path)
                if resolved.is_symlink() or not resolved.is_file():
                    continue
                content = resolved.read_text(encoding="utf-8")
                mtime = resolved.stat().st_mtime
            except (OSError, UnicodeDecodeError, ValueError):
                continue

            current_hash = self._hash_content(content)
            prev_hash = existing_indexed.get(source_file.path)

            if prev_hash == current_hash and not force:
                unchanged += 1
                continue

            # File is either new or modified
            chunks: list[CodeChunk] = self.chunker.chunk_text(
                file_path=source_file.path,
                content=content,
            )

            if chunks:
                texts = [c.content for c in chunks]
                embeddings = self.embedder.embed_texts(texts)
            else:
                embeddings = []

            self.index.save_file_chunks(
                file_path=source_file.path,
                content_hash=current_hash,
                mtime=mtime,
                chunks=chunks,
                embeddings=embeddings,
            )

            if prev_hash is None:
                added += 1
            else:
                modified += 1

        # Handle deletions (files in index that no longer exist on disk)
        for indexed_path in list(existing_indexed.keys()):
            if indexed_path not in scanned_paths:
                self.index.delete_file(indexed_path)
                deleted += 1

        duration = time.perf_counter() - start_time
        total_chunks = self.index.count_chunks()

        return SyncStats(
            added_files=added,
            modified_files=modified,
            deleted_files=deleted,
            unchanged_files=unchanged,
            total_chunks=total_chunks,
            duration_seconds=duration,
        )
