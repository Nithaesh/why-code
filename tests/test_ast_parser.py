from whycode.graph.ast_parser import ASTSymbolParser


def test_parse_classes_functions_and_methods() -> None:
    code = (
        "class CacheManager:\n"
        "    def __init__(self, size: int):\n"
        "        self.size = size\n"
        "\n"
        "    def clear(self):\n"
        "        pass\n"
        "\n"
        "def helper_func():\n"
        "    return 42\n"
    )

    parser = ASTSymbolParser()
    info = parser.parse_source("cache.py", code)

    assert info.file_path == "cache.py"
    names = [s.name for s in info.symbols]
    assert "CacheManager" in names
    assert "__init__" in names
    assert "clear" in names
    assert "helper_func" in names

    class_sym = next(s for s in info.symbols if s.name == "CacheManager")
    assert class_sym.kind == "class"
    assert class_sym.start_line == 1
    assert class_sym.end_line == 6

    method_sym = next(s for s in info.symbols if s.name == "clear")
    assert method_sym.kind == "method"
    assert method_sym.qualified_name == "CacheManager.clear"

    func_sym = next(s for s in info.symbols if s.name == "helper_func")
    assert func_sym.kind == "function"
    assert func_sym.qualified_name == "helper_func"


def test_parse_calls_and_imports() -> None:
    code = (
        "import os\n"
        "from pathlib import Path\n"
        "\n"
        "def process_file(path):\n"
        "    content = read_raw(path)\n"
        "    cleaned = sanitize(content)\n"
        "    return cleaned\n"
    )

    parser = ASTSymbolParser()
    info = parser.parse_source("proc.py", code)

    assert "os" in info.imports
    assert "pathlib.Path" in info.imports

    func = info.symbols[0]
    assert "read_raw" in func.calls
    assert "sanitize" in func.calls


def test_parse_syntax_error_handles_gracefully() -> None:
    bad_code = "def broken_syntax(:\n    return"
    parser = ASTSymbolParser()
    info = parser.parse_source("broken.py", bad_code)

    assert info.symbols == ()
    assert info.imports == ()


def test_parse_parameters_and_docstrings() -> None:
    code = (
        "def compute_total(price, tax_rate=0.05):\n"
        "    '''Calculate final price.'''\n"
        "    return price * (1 + tax_rate)\n"
    )

    parser = ASTSymbolParser()
    info = parser.parse_source("calc.py", code)

    assert len(info.symbols) == 1
    sym = info.symbols[0]
    assert sym.parameters == ("price", "tax_rate")
    assert sym.docstring == "Calculate final price."
