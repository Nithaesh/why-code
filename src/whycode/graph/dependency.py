"""Codebase dependency graph: maintains cross-file symbol lookups and caller/callee links."""

from __future__ import annotations

from typing import Sequence

from whycode.graph.ast_parser import CodeSymbol, FileModuleInfo


class CodebaseGraph:
    """Relational symbol graph tracking definitions, calls, and file-level imports."""

    def __init__(self, modules: Sequence[FileModuleInfo] = ()) -> None:
        self.modules: dict[str, FileModuleInfo] = {}
        # Map: simple_name -> list of symbols (may have multiple definitions across files)
        self.symbol_index: dict[str, list[CodeSymbol]] = {}
        # Map: qualified_name -> symbol
        self.qualified_index: dict[str, CodeSymbol] = {}
        # Map: called_name -> list of caller symbols
        self.caller_index: dict[str, list[CodeSymbol]] = {}

        for mod in modules:
            self.add_module(mod)

    def add_module(self, mod: FileModuleInfo) -> None:
        """Register or update a module in the dependency graph."""
        self.modules[mod.file_path] = mod

        for sym in mod.symbols:
            # Register in simple symbol index
            if sym.name not in self.symbol_index:
                self.symbol_index[sym.name] = []
            self.symbol_index[sym.name].append(sym)

            # Register in qualified index
            self.qualified_index[sym.qualified_name] = sym

            # Index called functions for caller lookups
            for called in sym.calls:
                if called not in self.caller_index:
                    self.caller_index[called] = []
                self.caller_index[called].append(sym)

    def find_symbols(self, name: str) -> list[CodeSymbol]:
        """Look up symbols by exact name or qualified name."""
        if name in self.qualified_index:
            return [self.qualified_index[name]]
        if name in self.symbol_index:
            return list(self.symbol_index[name])

        # Case-insensitive fallback
        lower_name = name.lower()
        matches: list[CodeSymbol] = []
        for sym_name, syms in self.symbol_index.items():
            if sym_name.lower() == lower_name:
                matches.extend(syms)
        return matches

    def get_callers(self, symbol_name: str) -> list[CodeSymbol]:
        """Find all functions/methods in the repository that call symbol_name."""
        # Simple name lookup
        simple = symbol_name.rsplit(".", 1)[-1]
        callers = self.caller_index.get(simple, [])
        # Deduplicate callers by (file_path, start_line) and filter to callable symbols
        seen = set()
        unique = []
        for c in callers:
            if c.kind not in ("function", "method"):
                continue
            key = (c.file_path, c.start_line)
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    def get_callees(self, symbol_name: str) -> list[str]:
        """Find names of functions called by the given symbol."""
        symbols = self.find_symbols(symbol_name)
        if not symbols:
            return []
        callees: set[str] = set()
        for sym in symbols:
            callees.update(sym.calls)
        return sorted(callees)

    def get_file_symbols(self, file_path: str) -> list[CodeSymbol]:
        """Retrieve all symbols defined in a given file."""
        norm = file_path.replace("\\", "/")
        mod = self.modules.get(norm)
        if mod:
            return list(mod.symbols)
        # Suffix matching for partial paths
        for p, m in self.modules.items():
            if p.endswith("/" + norm) or norm.endswith("/" + p):
                return list(m.symbols)
        return []

    def get_all_symbols(self) -> list[CodeSymbol]:
        """Return all indexed symbols across the repository."""
        all_syms: list[CodeSymbol] = []
        for mod in self.modules.values():
            all_syms.extend(mod.symbols)
        return sorted(all_syms, key=lambda s: (s.file_path, s.start_line))
