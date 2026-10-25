
import argparse
import json
import sys

from whycode.retrieval.service import CodebaseSearchService
from whycode.git import GitCommitReader, GitHistoryReader
from whycode.git.reader import GitReaderError
from whycode.investigation import CommitInvestigationService
from whycode.summarizer import CommitSummaryError, CommitSummaryService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="whycode",
        description="Explore Git history and summarize code changes.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    history_parser = subparsers.add_parser(
        "history",
        help="List recent commits.",
    )
    history_parser.add_argument("repo", help="Path to a Git repository")
    history_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of commits (default: 10)",
    )
    history_parser.add_argument(
        "--path",
        help="Only list commits affecting this repository-relative path",
    )

    show_parser = subparsers.add_parser(
        "show",
        help="Show detailed Git evidence for one commit.",
    )
    show_parser.add_argument("repo", help="Path to a Git repository")
    show_parser.add_argument(
        "--commit",
        default="HEAD",
        help="Commit hash or Git reference (default: HEAD)",
    )

    summarize_parser = subparsers.add_parser(
        "summarize",
        help="Summarize one commit using the configured LLM.",
    )
    summarize_parser.add_argument("repo", help="Path to a Git repository")
    summarize_parser.add_argument(
        "--commit",
        default="HEAD",
        help="Commit hash or Git reference (default: HEAD)",
    )
    summarize_parser.add_argument(
        "--history-limit",
        type=int,
        default=10,
        help="Number of recent commits to include in investigation context",
    )
    summarize_parser.add_argument(
        "--path",
        help="Filter the recent history by repository-relative path",
    )
    search_parser = subparsers.add_parser(
        "search",
        help="Search source code in a repository.",
    )
    search_parser.add_argument(
        "repo",
        help="Path to the repository to search",
    )
    search_parser.add_argument(
        "--query",
        required=True,
        help="Keywords to search for in source code",
    )
    search_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Maximum number of results (default: 5)",
    )
    search_parser.add_argument(
        "--mode",
        choices=["lexical", "hybrid", "semantic"],
        default="lexical",
        help="Retrieval mode: lexical (default), hybrid, or semantic",
    )
    search_parser.add_argument(
        "--reindex",
        action="store_true",
        help="Force a complete re-index of the repository",
    )

    ask_parser = subparsers.add_parser(
        "ask",
        help="Ask a question about a repository using the configured LLM.",
    )
    ask_parser.add_argument(
        "repo",
        help="Path to the repository to investigate",
    )
    ask_parser.add_argument(
        "--question",
        required=True,
        help="Question to answer using repository code",
    )
    ask_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Maximum number of code chunks to retrieve (default: 5)",
    )
    ask_parser.add_argument(
        "--mode",
        choices=["hybrid", "lexical", "semantic"],
        default="hybrid",
        help="Retrieval mode: hybrid (default), lexical, or semantic",
    )

    symbol_parser = subparsers.add_parser(
        "symbol",
        help="Inspect a code symbol's definition, callers, and Git history.",
    )
    symbol_parser.add_argument("repo", help="Path to repository")
    symbol_parser.add_argument(
        "--name",
        required=True,
        help="Name of class, function, or method",
    )

    churn_parser = subparsers.add_parser(
        "churn",
        help="Identify code churn hotspots across Git history.",
    )
    churn_parser.add_argument("repo", help="Path to repository")
    churn_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of hotspots to display (default: 10)",
    )

    investigate_parser = subparsers.add_parser(
        "investigate",
        help="Run an autonomous, multi-step code investigation agent across AST, Git, and search.",
    )
    investigate_parser.add_argument("repo", help="Path to repository")
    investigate_parser.add_argument(
        "--query",
        "-q",
        required=True,
        help="Diagnostic or archaeological question to investigate",
    )
    investigate_parser.add_argument(
        "--max-steps",
        type=int,
        default=3,
        help="Maximum agentic reasoning/tool-execution iterations (default: 3)",
    )

    return parser


def run_history(args: argparse.Namespace) -> int:
    reader = GitHistoryReader(args.repo)
    records = reader.list_commits(limit=args.limit, path=args.path)

    if not records:
        print("No commits found.")
        return 0

    for record in records:
        print(f"{record.commit_hash[:12]}  {record.authored_at}")
        print(f"  {record.author_name}: {record.subject}")

    return 0


def run_show(args: argparse.Namespace) -> int:
    evidence = GitCommitReader(args.repo).read_commit(args.commit)

    print(f"Commit:  {evidence.commit_hash}")
    print(f"Author:  {evidence.author_name} <{evidence.author_email}>")
    print(f"Date:    {evidence.authored_at}")
    print(f"Subject: {evidence.subject}")

    if evidence.body:
        print(f"\nMessage:\n{evidence.body}")

    print("\nChanged files:")
    if evidence.changed_files:
        for file in evidence.changed_files:
            print(f"  {file.status}  {file.path}")
    else:
        print("  (no changed files reported)")

    print("\nDiff:")
    print(evidence.diff or "(empty diff)")

    if evidence.diff_truncated:
        print("\nWARNING: Diff was truncated by the configured character limit.")

    return 0


def run_summarize(args):
    from whycode.config import Settings
    from whycode.llm.cache import DiskCache
    from whycode.llm.client import CachedLLM
    from whycode.llm.gemini import GeminiProvider

    settings = Settings()

    provider = GeminiProvider(
        api_key=settings.require_gemini_key(),
        model=settings.gemini_model,
    )

    cache = DiskCache(settings.whycode_cache_dir)

    llm = CachedLLM(
        provider=provider,
        cache=cache,
        provider_name=settings.whycode_provider,
        model=settings.gemini_model,
    )

    summary_service = CommitSummaryService(llm)

    investigation = CommitInvestigationService(
        repo_path=args.repo,
        summary_service=summary_service,
        history_limit=args.history_limit,
    ).investigate(
        commit_ref=args.commit,
        path=args.path,
    )

    print(
        json.dumps(
            {
                "commit_hash": investigation.evidence.commit_hash,
                "subject": investigation.evidence.subject,
                "summary": investigation.summary.model_dump(),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def run_search(args: argparse.Namespace) -> int:
    mode = getattr(args, "mode", "lexical")
    embedder = None

    if mode in ("hybrid", "semantic"):
        from whycode.config import Settings
        from whycode.llm.embedding import CachedEmbedder, GeminiEmbedder

        settings = Settings()
        api_key = settings.gemini_api_key.get_secret_value().strip()
        if api_key:
            try:
                raw_embedder = GeminiEmbedder(
                    api_key=api_key,
                    model=settings.gemini_embedding_model,
                )
                embedder = CachedEmbedder(
                    embedder=raw_embedder,
                    cache_dir=settings.whycode_cache_dir,
                    provider_name=settings.whycode_provider,
                    model_name=settings.gemini_embedding_model,
                )
            except Exception:
                embedder = None

        if embedder is None:
            # Fall back to lexical if no embedder is available
            mode = "lexical"

    service = CodebaseSearchService(args.repo, embedder=embedder)
    results = service.search(
        query=args.query,
        top_k=args.top_k,
        mode=mode,
        force_sync=getattr(args, "reindex", False),
    )

    if not results:
        print("No matching code found.")
        return 0

    for index, result in enumerate(results, start=1):
        chunk = result.chunk

        print(
            f"\n{index}. {chunk.file_path}:"
            f"{chunk.start_line}-{chunk.end_line}"
        )
        print(f"   Score: {result.score:.3f}")
        print("   " + "-" * 50)

        for line in chunk.content.splitlines():
            print(f"   {line}")

    return 0


def run_ask(args: argparse.Namespace) -> int:
    from whycode.config import Settings
    from whycode.llm.cache import DiskCache
    from whycode.llm.client import CachedLLM
    from whycode.llm.embedding import CachedEmbedder, GeminiEmbedder
    from whycode.llm.gemini import GeminiProvider
    from whycode.retrieval.qa import QuestionAnsweringService

    settings = Settings()

    provider = GeminiProvider(
        api_key=settings.require_gemini_key(),
        model=settings.gemini_model,
    )

    cache = DiskCache(settings.whycode_cache_dir)

    llm = CachedLLM(
        provider=provider,
        cache=cache,
        provider_name=settings.whycode_provider,
        model=settings.gemini_model,
    )

    mode = getattr(args, "mode", "hybrid")
    embedder = None
    if mode in ("hybrid", "semantic"):
        api_key = settings.gemini_api_key.get_secret_value().strip()
        if api_key:
            try:
                raw_embedder = GeminiEmbedder(
                    api_key=api_key,
                    model=settings.gemini_embedding_model,
                )
                embedder = CachedEmbedder(
                    embedder=raw_embedder,
                    cache_dir=settings.whycode_cache_dir,
                    provider_name=settings.whycode_provider,
                    model_name=settings.gemini_embedding_model,
                )
            except Exception:
                embedder = None

    service = QuestionAnsweringService(
        repo_path=args.repo,
        llm=llm,
        embedder=embedder,
    )

    result = service.ask(
        question=args.question,
        top_k=args.top_k,
        mode=mode,
    )

    print(f"Question: {result.question}")
    print(f"\nAnswer:\n{result.answer}")

    if result.sources:
        print("\nSources:")
        for source in result.sources:
            print(
                f"  - {source.file_path}:"
                f"{source.start_line}-{source.end_line}"
            )

    if result.verified_citations:
        print(f"\nGrounding Confidence: {result.grounding_confidence * 100:.1f}%")
        for cit in result.verified_citations:
            status = "VERIFIED" if cit.is_verified else "UNVERIFIED"
            print(f"  [{status}] {cit.raw_citation} -> {cit.reason}")

    return 0


def run_symbol(args: argparse.Namespace) -> int:
    from whycode.graph.service import CodeGraphService

    service = CodeGraphService(args.repo)
    result = service.inspect_symbol(args.name)

    if not result.definitions:
        print(f"Symbol '{args.name}' was not found in the codebase.")
        return 0

    print(f"=== Symbol: {args.name} ===\n")
    print("Definitions:")
    for d in result.definitions:
        print(f"  - [{d.kind}] {d.qualified_name} in {d.file_path}:{d.start_line}-{d.end_line}")
        if d.parameters:
            print(f"    Parameters: ({', '.join(d.parameters)})")
        if d.docstring:
            print(f"    Docstring: {d.docstring.strip()}")

    print("\nCallers (referenced by):")
    if result.callers:
        for c in result.callers:
            print(f"  - [{c.kind}] {c.qualified_name} ({c.file_path}:{c.start_line})")
    else:
        print("  (no direct callers found)")

    print("\nCallees (calls out to):")
    if result.callees:
        print(f"  {', '.join(result.callees)}")
    else:
        print("  (no calls out)")

    print("\nGit History & Churn:")
    for h in result.histories:
        print(f"  Total commits modifying {h.symbol.name}: {h.churn_count}")
        if h.commits:
            for c in h.commits[:5]:
                print(f"    - {c.commit_hash[:10]} ({c.authored_at[:10]}) by {c.author_name}: {c.subject}")

    return 0


def run_churn(args: argparse.Namespace) -> int:
    from whycode.graph.service import CodeGraphService

    service = CodeGraphService(args.repo)
    hotspots = service.get_churn_hotspots(top_n=args.limit)

    if not hotspots:
        print("No churn data found.")
        return 0

    print(f"=== Top {len(hotspots)} Code Churn Hotspots ===\n")
    print(f"{'Rank':<5} | {'Symbol':<28} | {'Kind':<10} | {'Churn':<6} | {'File':<30}")
    print("-" * 88)
    for rank, h in enumerate(hotspots, start=1):
        sym = h.symbol
        print(f"{rank:<5} | {sym.name:<28} | {sym.kind:<10} | {h.churn_count:<6} | {sym.file_path}:{sym.start_line}")

    return 0


def run_investigate(args: argparse.Namespace) -> int:
    from whycode.agent import InvestigationAgent, InvestigationToolbox
    from whycode.config import Settings
    from whycode.llm.cache import DiskCache
    from whycode.llm.client import CachedLLM
    from whycode.llm.gemini import GeminiProvider

    settings = Settings()
    provider = GeminiProvider(
        api_key=settings.require_gemini_key(),
        model=settings.gemini_model,
    )
    cache = DiskCache(settings.whycode_cache_dir)
    llm = CachedLLM(
        provider=provider,
        cache=cache,
        provider_name=settings.whycode_provider,
        model=settings.gemini_model,
    )

    toolbox = InvestigationToolbox(repo_path=args.repo)
    agent = InvestigationAgent(llm=llm, toolbox=toolbox, max_iterations=args.max_steps)

    def on_step(step_name: str, state):
        if step_name == "plan":
            hypo_count = len(state.plan.hypotheses) if state.plan else 0
            sym_count = len(state.plan.target_symbols) if state.plan else 0
            query_count = len(state.plan.target_queries) if state.plan else 0
            print(
                f"[Plan Formulated] {hypo_count} hypotheses, "
                f"{sym_count} target symbols, {query_count} initial queries."
            )
        elif step_name == "execute_tools":
            print(
                f"[Step {state.iteration + 1}/{state.max_iterations} - Tools Executed] "
                f"{len(state.evidence)} evidence items collected."
            )
        elif step_name == "evaluate":
            suff = "Sufficient" if (state.sufficiency and state.sufficiency.is_sufficient) else "Insufficient (iterating)"
            print(f"[Step {state.iteration}/{state.max_iterations} - Reflection] {suff}.")
        elif step_name == "synthesize":
            print("Synthesizing final diagnostic report...\n")

    report = agent.investigate(query=args.query, on_step=on_step)
    print(report.raw_markdown)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "history":
            return run_history(args)
        if args.command == "show":
            return run_show(args)
        if args.command == "summarize":
            return run_summarize(args)
        if args.command == "search":
            return run_search(args)
        if args.command == "ask":
            return run_ask(args)
        if args.command == "symbol":
            return run_symbol(args)
        if args.command == "churn":
            return run_churn(args)
        if args.command == "investigate":
            return run_investigate(args)

        parser.error("Unknown command.")
    except (GitReaderError, CommitSummaryError, ValueError) as exc:
        print(f"WhyCode error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        # Avoid dumping a traceback for routine CLI failures.
        print(
            f"WhyCode failed: {exc}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
