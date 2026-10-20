
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
    service = CodebaseSearchService(args.repo)
    results = service.search(
        query=args.query,
        top_k=args.top_k,
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
