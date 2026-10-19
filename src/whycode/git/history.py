
from dataclasses import dataclass
from pathlib import Path

from whycode.git.reader import GitCommitReader, GitReaderError


@dataclass(frozen=True)
class CommitRecord:
    """Lightweight metadata for one commit in Git history."""

    commit_hash: str
    author_name: str
    authored_at: str
    subject: str


class GitHistoryReader:
    """Read a bounded list of commits from a Git repository."""

    def __init__(
        self,
        repo_path: str | Path,
        timeout_seconds: int = 10,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive.")

        self._reader = GitCommitReader(
            repo_path,
            timeout_seconds=timeout_seconds,
        )
        self.repo_path = self._reader.repo_path
        self.timeout_seconds = timeout_seconds

    def list_commits(
        self,
        limit: int = 20,
        path: str | None = None,
    ) -> list[CommitRecord]:
        """List newest commits first, optionally restricted to a file path."""
        if limit <= 0:
            raise ValueError("limit must be positive.")

        if path is not None:
            path = path.strip()
            if not path:
                raise ValueError("path cannot be empty.")

            # Git path filters are repository-relative.
            candidate = Path(path)
            if candidate.is_absolute() or ".." in candidate.parts:
                raise ValueError(
                    "path must be a repository-relative path "
                    "without '..' components."
                )

        args = [
            "log",
            f"--max-count={limit}",
            "--format=%H%x00%an%x00%aI%x00%s",
        ]

        if path is not None:
            args.extend(["--", path])

        output = self._run_git(*args)

        if not output:
            return []

        records: list[CommitRecord] = []

        for line in output.splitlines():
            fields = line.split("\x00", 3)
            if len(fields) != 4:
                raise GitReaderError(
                    "Git returned unexpected history data."
                )

            commit_hash, author_name, authored_at, subject = fields

            records.append(
                CommitRecord(
                    commit_hash=commit_hash,
                    author_name=author_name,
                    authored_at=authored_at,
                    subject=subject,
                )
            )

        return records

    def _run_git(self, *args: str) -> str:
        # Reuse the existing reader's Git error handling and timeout.
        return self._reader._run_git(*args)
