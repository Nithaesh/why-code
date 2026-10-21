
from pathlib import Path

import pytest

from whycode.ingest.scanner import (
    RepositoryScanError,
    RepositoryScanner,
    ScanConfig,
)


def write_file(root: Path, relative_path: str, content: bytes) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_scanner_finds_supported_files_with_relative_paths(
    tmp_path: Path,
) -> None:
    write_file(tmp_path, "src/main.py", b"print('hello')\n")
    write_file(tmp_path, "docs/guide.md", b"# Guide\n")
    write_file(tmp_path, "notes.txt", b"not supported")

    results = RepositoryScanner(tmp_path).scan()

    assert [item.path for item in results] == [
        "docs/guide.md",
        "src/main.py",
    ]
    assert results[1].size_bytes == len(b"print('hello')\n")


def test_scanner_excludes_generated_directories(
    tmp_path: Path,
) -> None:
    write_file(tmp_path, "main.py", b"print('ok')\n")
    write_file(tmp_path, ".git/config.py", b"not source")
    write_file(tmp_path, "node_modules/pkg/index.js", b"not source")
    write_file(tmp_path, ".venv/lib/site.py", b"not source")

    results = RepositoryScanner(tmp_path).scan()

    assert [item.path for item in results] == ["main.py"]


def test_scanner_skips_oversized_files(tmp_path: Path) -> None:
    write_file(tmp_path, "large.py", b"x" * 101)

    config = ScanConfig(max_file_size_bytes=100)
    results = RepositoryScanner(tmp_path, config).scan()

    assert results == []


def test_scanner_skips_binary_and_invalid_utf8_files(
    tmp_path: Path,
) -> None:
    write_file(tmp_path, "binary.py", b"print('x')\x00")
    write_file(tmp_path, "invalid.py", b"\xff\xfe\xfa")
    write_file(tmp_path, "valid.py", b"print('valid')\n")

    results = RepositoryScanner(tmp_path).scan()

    assert [item.path for item in results] == ["valid.py"]


def test_scanner_excludes_sensitive_filenames(
    tmp_path: Path,
) -> None:
    write_file(tmp_path, ".env", b"API_KEY=secret\n")
    write_file(tmp_path, "credentials.json", b'{"key": "secret"}')
    write_file(tmp_path, "settings.toml", b"debug = true\n")

    results = RepositoryScanner(tmp_path).scan()

    assert [item.path for item in results] == ["settings.toml"]


def test_scanner_results_are_sorted(tmp_path: Path) -> None:
    write_file(tmp_path, "z.py", b"z")
    write_file(tmp_path, "a.py", b"a")
    write_file(tmp_path, "nested/m.py", b"m")

    results = RepositoryScanner(tmp_path).scan()

    assert [item.path for item in results] == [
        "a.py",
        "nested/m.py",
        "z.py",
    ]


def test_scanner_rejects_nonexistent_root(tmp_path: Path) -> None:
    with pytest.raises(RepositoryScanError, match="does not exist"):
        RepositoryScanner(tmp_path / "missing").scan()


def test_scanner_rejects_file_as_root(tmp_path: Path) -> None:
    file_path = tmp_path / "not-a-directory"
    file_path.write_text("hello", encoding="utf-8")

    with pytest.raises(RepositoryScanError, match="not a directory"):
        RepositoryScanner(file_path).scan()


def test_scanner_rejects_negative_size_limit(
    tmp_path: Path,
) -> None:
    with pytest.raises(RepositoryScanError, match="cannot be negative"):
        RepositoryScanner(
            tmp_path,
            ScanConfig(max_file_size_bytes=-1),
        ).scan()
def test_scanner_supports_safe_special_filenames(
    tmp_path: Path,
) -> None:
    write_file(tmp_path, ".gitignore", b".venv/\n")
    write_file(tmp_path, ".env.example", b"API_KEY=replace-me\n")
    write_file(tmp_path, ".env.sample", b"API_KEY=replace-me\n")
    write_file(tmp_path, ".env.local", b"API_KEY=real-secret\n")

    results = RepositoryScanner(tmp_path).scan()

    assert [item.path for item in results] == [
        ".env.example",
        ".env.sample",
        ".gitignore",
    ]