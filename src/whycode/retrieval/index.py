"""Persistent vector and chunk indexing using SQLite and NumPy."""

from __future__ import annotations

import contextlib
from pathlib import Path
import sqlite3
from typing import Iterator

import numpy as np

from whycode.ingest.chunker import CodeChunk
from whycode.retrieval.lexical import RetrievalResult


class VectorIndex:
    """Store repository code chunks and dense vector embeddings in SQLite."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextlib.contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS indexed_files (
                    file_path TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL,
                    mtime REAL NOT NULL,
                    chunk_count INTEGER NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    start_line INTEGER NOT NULL,
                    end_line INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    FOREIGN KEY (file_path) REFERENCES indexed_files(file_path) ON DELETE CASCADE
                );
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chunks_file_path ON chunks(file_path);
                """
            )

    def get_indexed_files(self) -> dict[str, str]:
        """Return mapping of file_path -> content_hash for all indexed files."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT file_path, content_hash FROM indexed_files;"
            ).fetchall()
            return {row["file_path"]: row["content_hash"] for row in rows}

    def save_file_chunks(
        self,
        file_path: str,
        content_hash: str,
        mtime: float,
        chunks: list[CodeChunk],
        embeddings: list[list[float]],
    ) -> None:
        """Atomically persist or replace chunks and embeddings for one file."""
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings."
            )

        with self._connection() as conn:
            # Delete existing chunks for this file
            conn.execute(
                "DELETE FROM chunks WHERE file_path = ?;",
                (file_path,),
            )
            # Upsert file record
            conn.execute(
                """
                INSERT INTO indexed_files (file_path, content_hash, mtime, chunk_count)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    content_hash = excluded.content_hash,
                    mtime = excluded.mtime,
                    chunk_count = excluded.chunk_count;
                """,
                (file_path, content_hash, mtime, len(chunks)),
            )

            chunk_records = []
            for chunk, emb in zip(chunks, embeddings):
                arr = np.array(emb, dtype=np.float32)
                # Store normalized float32 bytes
                blob = arr.tobytes()
                chunk_records.append(
                    (
                        chunk.chunk_id,
                        chunk.file_path,
                        chunk.start_line,
                        chunk.end_line,
                        chunk.content,
                        blob,
                    )
                )

            if chunk_records:
                conn.executemany(
                    """
                    INSERT INTO chunks (chunk_id, file_path, start_line, end_line, content, embedding)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    chunk_records,
                )

    def delete_file(self, file_path: str) -> None:
        """Remove a deleted file and its chunks from the index."""
        with self._connection() as conn:
            conn.execute(
                "DELETE FROM chunks WHERE file_path = ?;",
                (file_path,),
            )
            conn.execute(
                "DELETE FROM indexed_files WHERE file_path = ?;",
                (file_path,),
            )

    def count_chunks(self) -> int:
        """Total number of indexed chunks."""
        with self._connection() as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM chunks;").fetchone()
            return int(row["count"]) if row else 0

    def get_all_chunks(self) -> list[CodeChunk]:
        """Retrieve all stored chunks in deterministic order."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT chunk_id, file_path, start_line, end_line, content
                FROM chunks
                ORDER BY file_path, start_line;
                """
            ).fetchall()
            return [
                CodeChunk(
                    chunk_id=row["chunk_id"],
                    file_path=row["file_path"],
                    start_line=row["start_line"],
                    end_line=row["end_line"],
                    content=row["content"],
                )
                for row in rows
            ]

    def get_all_vectors(self) -> tuple[list[CodeChunk], np.ndarray]:
        """Load all chunks and a 2D matrix (N, D) of their float32 embeddings."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT chunk_id, file_path, start_line, end_line, content, embedding
                FROM chunks
                ORDER BY file_path, start_line;
                """
            ).fetchall()

        if not rows:
            return [], np.empty((0, 0), dtype=np.float32)

        chunks: list[CodeChunk] = []
        vec_list: list[np.ndarray] = []

        for row in rows:
            chunk = CodeChunk(
                chunk_id=row["chunk_id"],
                file_path=row["file_path"],
                start_line=row["start_line"],
                end_line=row["end_line"],
                content=row["content"],
            )
            chunks.append(chunk)
            blob = row["embedding"]
            arr = np.frombuffer(blob, dtype=np.float32)
            vec_list.append(arr)

        matrix = np.stack(vec_list, axis=0)
        return chunks, matrix

    def vector_search(
        self,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Search chunks by cosine similarity to a normalized query vector."""
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        chunks, matrix = self.get_all_vectors()
        if not chunks or matrix.size == 0:
            return []

        q = np.array(query_vector, dtype=np.float32)
        q_norm = float(np.linalg.norm(q))
        if q_norm > 1e-9:
            q = q / q_norm
        else:
            return []

        # Cosine similarity for unit vectors is simply dot product
        scores = np.dot(matrix, q)

        results: list[RetrievalResult] = []
        for chunk, score in zip(chunks, scores):
            score_val = float(score)
            if score_val > 0.0:
                results.append(RetrievalResult(chunk=chunk, score=score_val))

        # Sort descending by score, deterministic tie breaking
        results.sort(
            key=lambda r: (-r.score, r.chunk.file_path, r.chunk.start_line)
        )
        return results[:top_k]

    def clear(self) -> None:
        """Drop all indexed data for a clean rebuild."""
        with self._connection() as conn:
            conn.execute("DELETE FROM chunks;")
            conn.execute("DELETE FROM indexed_files;")
