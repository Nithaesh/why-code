"""Post-generation citation verification: validates LLM citations against retrieved context."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Sequence

from whycode.retrieval.distiller import DistilledSource


@dataclass(frozen=True, slots=True)
class CitationVerification:
    """Verification outcome for a single citation extracted from LLM text."""

    raw_citation: str
    file_path: str
    start_line: int | None
    end_line: int | None
    is_verified: bool
    reason: str


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Overall outcome of citation verification across an answer."""

    citations: tuple[CitationVerification, ...]
    grounding_confidence: float
    all_verified: bool
    summary: str


class CitationVerifier:
    """Inspect generated text and verify file and line references against retrieved sources."""

    def verify(
        self,
        answer_text: str,
        sources: Sequence[DistilledSource],
    ) -> VerificationResult:
        """Parse citations from answer text and check them against provided sources."""
        if not answer_text or not answer_text.strip():
            return VerificationResult(
                citations=(),
                grounding_confidence=0.0,
                all_verified=True,
                summary="Empty answer text.",
            )

        if not sources:
            # If no sources were provided, check if the answer appropriately states this
            return VerificationResult(
                citations=(),
                grounding_confidence=1.0,
                all_verified=True,
                summary="No sources were available.",
            )

        extracted_citations = self._extract_citations(answer_text, sources)
        if not extracted_citations:
            # Answer made no explicit citations
            return VerificationResult(
                citations=(),
                grounding_confidence=1.0,
                all_verified=True,
                summary="No explicit citations found in answer.",
            )

        verifications: list[CitationVerification] = []
        for raw, file_path, start_line, end_line in extracted_citations:
            is_valid, reason = self._verify_single(file_path, start_line, end_line, sources)
            verifications.append(
                CitationVerification(
                    raw_citation=raw,
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    is_verified=is_valid,
                    reason=reason,
                )
            )

        verified_count = sum(1 for v in verifications if v.is_verified)
        confidence = verified_count / len(verifications) if verifications else 1.0
        all_verified = verified_count == len(verifications)

        summary = (
            f"Verified {verified_count}/{len(verifications)} citations "
            f"({confidence * 100:.1f}% grounding confidence)."
        )

        return VerificationResult(
            citations=tuple(verifications),
            grounding_confidence=confidence,
            all_verified=all_verified,
            summary=summary,
        )

    def _extract_citations(
        self,
        text: str,
        sources: Sequence[DistilledSource],
    ) -> list[tuple[str, str, int | None, int | None]]:
        """Extract citations in formats: Source N, file.py:10-20, or path/to/file.py."""
        citations: list[tuple[str, str, int | None, int | None]] = []
        seen: set[str] = set()

        # 1. Match "Source N" or "[Source N]"
        source_pattern = re.compile(r"\[?\bSource\s+(\d+)\b\]?", re.IGNORECASE)
        source_map = {s.source_id: s for s in sources}

        for match in source_pattern.finditer(text):
            raw = match.group(0)
            if raw in seen:
                continue
            seen.add(raw)
            sid = int(match.group(1))
            if sid in source_map:
                src = source_map[sid]
                citations.append((raw, src.file_path, src.start_line, src.end_line))
            else:
                citations.append((raw, f"NonexistentSource-{sid}", None, None))

        # 2. Match "path/file.ext:start-end" or "file.ext:start"
        file_line_pattern = re.compile(
            r"([a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9]+):(\d+)(?:-(\d+))?"
        )
        for match in file_line_pattern.finditer(text):
            raw = match.group(0)
            if raw in seen:
                continue
            seen.add(raw)
            file_path = match.group(1).replace("\\", "/")
            start_l = int(match.group(2))
            end_l = int(match.group(3)) if match.group(3) else start_l
            citations.append((raw, file_path, start_l, end_l))

        return citations

    @staticmethod
    def _verify_single(
        file_path: str,
        start_line: int | None,
        end_line: int | None,
        sources: Sequence[DistilledSource],
    ) -> tuple[bool, str]:
        """Check if file and line span match any distilled source block."""
        norm_file = file_path.replace("\\", "/").lower()

        # Find matching source file(s)
        matching_sources = [
            s for s in sources
            if s.file_path.lower() == norm_file
            or s.file_path.lower().endswith("/" + norm_file)
            or norm_file.endswith("/" + s.file_path.lower())
            or norm_file.rsplit("/", 1)[-1] == s.file_path.rsplit("/", 1)[-1].lower()
        ]

        if not matching_sources:
            return False, f"File '{file_path}' was not in the retrieved sources."

        # If no specific line range was cited, file match is sufficient
        if start_line is None:
            return True, f"File '{file_path}' verified in retrieved sources."

        end = end_line or start_line
        # Check if line range overlaps or is within any matching source span
        for s in matching_sources:
            # Overlap condition: max(start1, start2) <= min(end1, end2)
            if max(start_line, s.start_line) <= min(end, s.end_line):
                return True, (
                    f"Lines {start_line}-{end} verified in {s.file_path} "
                    f"({s.start_line}-{s.end_line})."
                )

        spans_str = ", ".join(f"{s.start_line}-{s.end_line}" for s in matching_sources)
        return False, (
            f"Lines {start_line}-{end} for '{file_path}' are outside "
            f"retrieved line span(s): {spans_str}."
        )
