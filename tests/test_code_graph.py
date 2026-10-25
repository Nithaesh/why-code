from whycode.graph.ast_parser import ASTSymbolParser
from whycode.graph.dependency import CodebaseGraph


def test_find_symbols_exact_and_case_insensitive() -> None:
    code_a = "class TokenValidator:\n    pass\n"
    code_b = "def validate_token():\n    pass\n"

    parser = ASTSymbolParser()
    mod_a = parser.parse_source("auth/token.py", code_a)
    mod_b = parser.parse_source("auth/handler.py", code_b)

    graph = CodebaseGraph([mod_a, mod_b])

    # Exact match
    res_exact = graph.find_symbols("TokenValidator")
    assert len(res_exact) == 1
    assert res_exact[0].file_path == "auth/token.py"

    # Case-insensitive match
    res_ci = graph.find_symbols("tokenvalidator")
    assert len(res_ci) == 1
    assert res_ci[0].name == "TokenValidator"


def test_find_callers_across_modules() -> None:
    code_provider = (
        "def generate_text():\n"
        "    return 'ok'\n"
    )
    code_consumer_1 = (
        "def run_qa():\n"
        "    ans = generate_text()\n"
        "    return ans\n"
    )
    code_consumer_2 = (
        "class Service:\n"
        "    def execute(self):\n"
        "        generate_text()\n"
    )

    parser = ASTSymbolParser()
    m1 = parser.parse_source("provider.py", code_provider)
    m2 = parser.parse_source("consumer.py", code_consumer_1)
    m3 = parser.parse_source("service.py", code_consumer_2)

    graph = CodebaseGraph([m1, m2, m3])

    callers = graph.get_callers("generate_text")
    caller_names = [c.qualified_name for c in callers]

    assert len(callers) == 2
    assert "run_qa" in caller_names
    assert "Service.execute" in caller_names


def test_find_callees() -> None:
    code = (
        "def main():\n"
        "    setup_logging()\n"
        "    run_server()\n"
    )
    parser = ASTSymbolParser()
    m = parser.parse_source("main.py", code)
    graph = CodebaseGraph([m])

    callees = graph.get_callees("main")
    assert "setup_logging" in callees
    assert "run_server" in callees


def test_get_file_symbols() -> None:
    code = (
        "class A: pass\n"
        "class B: pass\n"
    )
    parser = ASTSymbolParser()
    m = parser.parse_source("src/models.py", code)
    graph = CodebaseGraph([m])

    symbols = graph.get_file_symbols("src/models.py")
    assert len(symbols) == 2
    assert [s.name for s in symbols] == ["A", "B"]
