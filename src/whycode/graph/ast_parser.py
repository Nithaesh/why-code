"""AST-based Python code symbol and dependency extraction using Python's standard ast module."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True, slots=True)
class CodeSymbol:
    """A semantic code symbol extracted from an Abstract Syntax Tree."""

    name: str
    qualified_name: str
    kind: str  # "class", "function", "method"
    file_path: str
    start_line: int
    end_line: int
    docstring: str | None
    calls: tuple[str, ...]
    parameters: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FileModuleInfo:
    """Module-level import and symbol metadata for a single file."""

    file_path: str
    imports: tuple[str, ...]
    symbols: tuple[CodeSymbol, ...]


class _SymbolVisitor(ast.NodeVisitor):
    """Walk an AST to collect definitions, calls, and line boundaries."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.symbols: list[CodeSymbol] = []
        self.imports: list[str] = []
        self._class_stack: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            full = f"{module}.{alias.name}" if module else alias.name
            self.imports.append(full)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qual_name = (
            f"{'.'.join(self._class_stack)}.{node.name}"
            if self._class_stack
            else node.name
        )
        docstring = ast.get_docstring(node)
        calls = self._extract_calls(node)

        self.symbols.append(
            CodeSymbol(
                name=node.name,
                kind="class",
                qualified_name=qual_name,
                file_path=self.file_path,
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                docstring=docstring,
                calls=tuple(calls),
                parameters=(),
            )
        )

        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self._record_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record_function(node)

    def _record_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        is_method = bool(self._class_stack)
        kind = "method" if is_method else "function"
        qual_name = (
            f"{'.'.join(self._class_stack)}.{node.name}"
            if self._class_stack
            else node.name
        )
        docstring = ast.get_docstring(node)
        calls = self._extract_calls(node)
        params = [arg.arg for arg in node.args.args]

        self.symbols.append(
            CodeSymbol(
                name=node.name,
                kind=kind,
                qualified_name=qual_name,
                file_path=self.file_path,
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                docstring=docstring,
                calls=tuple(calls),
                parameters=tuple(params),
            )
        )
        self.generic_visit(node)

    @staticmethod
    def _extract_calls(parent_node: ast.AST) -> list[str]:
        """Extract called function/method names directly within this node's scope."""
        calls: list[str] = []
        for child in ast.iter_child_nodes(parent_node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Do not recurse into nested function or class definitions
                continue
            for subnode in ast.walk(child):
                if isinstance(subnode, ast.Call):
                    func = subnode.func
                    if isinstance(func, ast.Name):
                        calls.append(func.id)
                    elif isinstance(func, ast.Attribute):
                        calls.append(func.attr)

        seen = set()
        deduped = []
        for c in calls:
            if c not in seen:
                seen.add(c)
                deduped.append(c)
        return deduped


class ASTSymbolParser:
    """Extract semantic symbols and import relationships from Python source code."""

    def parse_source(self, file_path: str, content: str) -> FileModuleInfo:
        """Parse source code string into structured symbol and import metadata."""
        normalized_path = file_path.replace("\\", "/")
        try:
            tree = ast.parse(content, filename=normalized_path)
        except (SyntaxError, ValueError):
            return FileModuleInfo(
                file_path=normalized_path,
                imports=(),
                symbols=(),
            )

        visitor = _SymbolVisitor(file_path=normalized_path)
        visitor.visit(tree)

        return FileModuleInfo(
            file_path=normalized_path,
            imports=tuple(sorted(set(visitor.imports))),
            symbols=tuple(visitor.symbols),
        )

    def parse_file(self, file_path: str | Path, repo_root: str | Path | None = None) -> FileModuleInfo:
        """Read and parse a file from disk."""
        path = Path(file_path).resolve()
        rel_path = (
            path.relative_to(Path(repo_root).resolve()).as_posix()
            if repo_root
            else path.name
        )
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return FileModuleInfo(file_path=rel_path, imports=(), symbols=())

        return self.parse_source(file_path=rel_path, content=content)
