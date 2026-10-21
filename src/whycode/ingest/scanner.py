
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


SUPPORTED_EXTENSIONS = frozenset(
    {
        # Programming languages
        ".py", ".js", ".jsx", ".ts", ".tsx",
        ".java", ".c", ".h", ".cpp", ".hpp",
        ".go", ".rs",

        # Web files
        ".html", ".css",

        # Configuration and documentation
        ".json", ".yaml", ".yml", ".toml", ".md",
        ".xml", ".sql", ".sh", ".bat", ".ps1",
    }
)

EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".whycode_cache",
    }
)

# These names are excluded regardless of their file extension.
EXCLUDED_FILENAMES = frozenset(
    {
        ".env",
        ".env.local",
        ".env.development",
        ".env.production",
        "id_rsa",
        "id_ed25519",
        "credentials.json",
        "secrets.json",
    }
)

MAX_FILE_SIZE_BYTES = 1_000_000


class RepositoryScanError(Exception):
    """Raised when the repository cannot be scanned safely."""


@dataclass(frozen=True, slots=True)
class SourceFile:
    """Metadata for a source file discovered in a repository."""

    path: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class ScanConfig:
    """Configurable scanner limits and supported file types."""
    supported_filenames: frozenset[str] = frozenset(
    {".gitignore", ".env.example", ".env.sample"}
    )
    supported_extensions: frozenset[str] = SUPPORTED_EXTENSIONS
    excluded_directories: frozenset[str] = EXCLUDED_DIRECTORIES
    excluded_filenames: frozenset[str] = EXCLUDED_FILENAMES
    max_file_size_bytes: int = MAX_FILE_SIZE_BYTES


class RepositoryScanner:
    """Discover relevant, reasonably sized files inside a repository."""

    def __init__(
        self,
        repo_path: str | Path,
        config: ScanConfig | None = None,
    ) -> None:
        self.repo_path = Path(repo_path).expanduser()
        self.config = config or ScanConfig()

    def scan(self) -> list[SourceFile]:
        """Return supported files in deterministic relative-path order."""
        root = self.repo_path.resolve()

        if not root.exists():
            raise RepositoryScanError(
                f"Repository path does not exist: {self.repo_path}"
            )

        if not root.is_dir():
            raise RepositoryScanError(
                f"Repository path is not a directory: {self.repo_path}"
            )

        if self.config.max_file_size_bytes < 0:
            raise RepositoryScanError(
                "Maximum file size cannot be negative."
            )

        results: list[SourceFile] = []

        for current_dir, dirs, filenames in os.walk(
            root,
            topdown=True,
            followlinks=False,
        ):
            current_path = Path(current_dir)

            # Avoid traversing generated/dependency directories and symlinked
            # directories. Sorting makes discovery deterministic.
            dirs[:] = sorted(
                dirname
                for dirname in dirs
                if dirname not in self.config.excluded_directories
                and not (current_path / dirname).is_symlink()
            )

            for filename in sorted(filenames):
                if filename in self.config.excluded_filenames:
                    continue

                # Skip environment files by default, allowing only explicitly
                # supported example templates.
                if filename.startswith(".env") and (filename not in self.config.supported_filenames):
                    continue

                path = current_path / filename

                if path.is_symlink() or not path.is_file():
                    continue
                if (path.suffix.lower() not in self.config.supported_extensions and filename not in self.config.supported_filenames):
                    continue

                try:
                    resolved_path = path.resolve(strict=True)
                    resolved_path.relative_to(root)
                    size = resolved_path.stat().st_size

                    if size > self.config.max_file_size_bytes:
                        continue

                    # Skip binary content and files that aren't valid UTF-8.
                    with resolved_path.open("rb") as file:
                        content = file.read(
                            self.config.max_file_size_bytes + 1
                        )

                    if b"\x00" in content:
                        continue

                    content.decode("utf-8")

                except (
                    OSError,
                    UnicodeDecodeError,
                    ValueError,
                ):
                    # A single unreadable or invalid file shouldn't abort
                    # scanning the rest of the repository.
                    continue

                results.append(
                    SourceFile(
                        path=resolved_path.relative_to(root).as_posix(),
                        size_bytes=size,
                    )
                )

        return sorted(results, key=lambda item: item.path)
