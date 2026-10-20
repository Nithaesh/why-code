
import argparse
import json

from whycode.git.reader import GitCommitReader
from whycode.llm.client import CachedLLM
from whycode.llm.gemini import GeminiProvider
from whycode.summarizer import CommitSummaryService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize a Git commit using WhyCode."
    )
    parser.add_argument("repo", help="Path to the Git repository")
    parser.add_argument(
        "--commit",
        default="HEAD",
        help="Commit hash or Git reference (default: HEAD)",
    )
    args = parser.parse_args()

    evidence = GitCommitReader(args.repo).read_commit(args.commit)

    # Reuse WhyCode's existing provider and response cache.
    llm = CachedLLM(GeminiProvider())
    service = CommitSummaryService(llm)
    summary = service.summarize(evidence)

    print(f"\nCommit: {evidence.commit_hash}")
    print(f"Subject: {evidence.subject}\n")
    print(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
