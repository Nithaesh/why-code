
from whycode.ingest.chunker import CodeChunker
from whycode.retrieval.context import ContextBuilder
from whycode.retrieval.lexical import RetrievalResult


def make_result(file_path: str, content: str) -> RetrievalResult:
    chunk = CodeChunker().chunk_text(file_path, content)[0]
    return RetrievalResult(chunk=chunk, score=1.0)


def test_build_includes_source_path_and_line_range():
    result = make_result(
        "src/cache.py",
        "def get_cache():\n    return None",
    )

    context = ContextBuilder().build([result])

    assert "File: src/cache.py" in context
    assert "Lines: 1-2" in context


def test_build_preserves_code_content():
    code = "def get_cache():\n    return None"
    result = make_result("src/cache.py", code)

    context = ContextBuilder().build([result])

    assert code in context


def test_build_preserves_result_order():
    first = make_result("src/first.py", "first_value = 1")
    second = make_result("src/second.py", "second_value = 2")

    context = ContextBuilder().build([first, second])

    assert context.index("src/first.py") < context.index("src/second.py")
    assert "Source 1" in context
    assert "Source 2" in context


def test_build_returns_empty_string_for_no_results():
    assert ContextBuilder().build([]) == ""
