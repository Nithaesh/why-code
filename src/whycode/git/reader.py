
from dataclasses import dataclass
from pathlib import Path
import subprocess


class GitReaderError(RuntimeError):
    """Raised when Git evidence cannot be extracted."""


@dataclass(frozen=True)
class ChangedFile:
    path: str
    status: str


@dataclass(frozen=True)
class CommitEvidence:
    repo_root: str
    commit_hash: str
    author_name: str
    author_email: str
    authored_at: str
    subject: str
    body: str
    changed_files: tuple[ChangedFile, ...]
    diff: str
    diff_truncated: bool


class GitCommitReader:
    """Extract evidence about one commit using Git's command-line interface."""

    def __init__(
        self,
        repo_path: str | Path,
        timeout_seconds: int = 10,
        max_diff_chars: int = 30_000,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive.")
        if max_diff_chars <= 0:
            raise ValueError("max_diff_chars must be positive.")

        self.repo_path = Path(repo_path).expanduser().resolve()
        self.timeout_seconds = timeout_seconds
        self.max_diff_chars = max_diff_chars

    def _run_git(self, *args: str) -> str:
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), *args],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise GitReaderError(
                "Git was not found. Install Git and ensure it is on PATH."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise GitReaderError(
                f"Git command timed out after {self.timeout_seconds} seconds."
            ) from exc

        if result.returncode != 0:
            message = result.stderr.strip() or "Unknown Git error."
            raise GitReaderError(f"Git command failed: {message}")

        return result.stdout

    def read_commit(self, commit_ref: str = "HEAD") -> CommitEvidence:
        if not commit_ref or not commit_ref.strip():
            raise GitReaderError("A commit reference is required.")

        # Resolve the reference to a real commit hash first.
        commit_hash = self._run_git(
            "rev-parse",
            "--verify",
            "--end-of-options",
            f"{commit_ref}^{{commit}}",
        ).strip()

        repo_root = self._run_git(
            "rev-parse", "--show-toplevel"
        ).strip()

        # NUL separators avoid ambiguity if metadata contains punctuation.
        metadata = self._run_git(
            "show",
            "-s",
            "--format=%H%x00%an%x00%ae%x00%aI%x00%s%x00%b",
            commit_hash,
        )
        fields = metadata.split("\x00", 5)

        if len(fields) != 6:
            raise GitReaderError("Git returned unexpected commit metadata.")

        (
            returned_hash,
            author_name,
            author_email,
            authored_at,
            subject,
            body,
        ) = fields

        # NUL-separated file records are safer for unusual file names.
        file_output = self._run_git(
            "diff-tree",
            "--no-commit-id",
            "--name-status",
            "-r",
            "--root",
            "-z",
            "--no-renames",
            commit_hash,
        )
        file_parts = file_output.split("\x00")
        if file_parts and file_parts[-1] == "":
            file_parts.pop()

        if len(file_parts) % 2 != 0:
            raise GitReaderError("Git returned unexpected changed-file data.")

        changed_files = tuple(
            ChangedFile(path=file_parts[i + 1], status=file_parts[i])
            for i in range(0, len(file_parts), 2)
        )

        full_diff = self._run_git(
            "show",
            "--format=",
            "--no-ext-diff",
            "--no-textconv",
            "--no-color",
            "--no-renames",
            commit_hash,
            "--",
        )

        truncated = len(full_diff) > self.max_diff_chars
        diff = full_diff[: self.max_diff_chars]

        return CommitEvidence(
            repo_root=str(Path(repo_root).resolve()),
            commit_hash=returned_hash,
            author_name=author_name,
            author_email=author_email,
            authored_at=authored_at,
            subject=subject,
            body=body.strip(),
            changed_files=changed_files,
            diff=diff,
            diff_truncated=truncated,
        )
