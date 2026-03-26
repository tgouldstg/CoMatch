from __future__ import annotations

import re
from difflib import SequenceMatcher

try:
    from rapidfuzz import fuzz
except Exception:  # pragma: no cover
    fuzz = None

from .schemas import CompanyRecord, MatchCandidate, MatchOptions, MatchResult


LEGAL_SUFFIXES = {
    "inc",
    "inc.",
    "llc",
    "l.l.c",
    "ltd",
    "ltd.",
    "limited",
    "corp",
    "corp.",
    "corporation",
    "co",
    "co.",
    "company",
    "gmbh",
    "sa",
    "s.a.",
    "bv",
    "ag",
    "plc",
    "pte",
    "pty",
}


def normalize_company_name(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    tokens = [t for t in s.split() if t and t not in LEGAL_SUFFIXES]
    return " ".join(tokens).strip()


def _fuzzy_ratio(a: str, b: str) -> float:
    if fuzz is not None:
        return float(fuzz.token_set_ratio(a, b)) / 100.0
    return SequenceMatcher(None, a, b).ratio()


def _website_score(left: CompanyRecord, right: CompanyRecord) -> float:
    if not left.website or not right.website:
        return 0.0
    lw = left.website.lower().replace("https://", "").replace("http://", "").strip("/")
    rw = right.website.lower().replace("https://", "").replace("http://", "").strip("/")
    return 1.0 if lw == rw else 0.0


def _country_score(left: CompanyRecord, right: CompanyRecord) -> float:
    if not left.country or not right.country:
        return 0.0
    return 1.0 if left.country.strip().lower() == right.country.strip().lower() else 0.0


def score_pair(left: CompanyRecord, right: CompanyRecord) -> tuple[float, dict[str, float]]:
    left_norm = normalize_company_name(left.name)
    right_norm = normalize_company_name(right.name)

    name_score = _fuzzy_ratio(left_norm, right_norm)
    website_score = _website_score(left, right)
    country_score = _country_score(left, right)

    # Weighted blend; tune later with labeled data
    score = (0.82 * name_score) + (0.15 * website_score) + (0.03 * country_score)

    breakdown = {
        "name": round(name_score, 4),
        "website": round(website_score, 4),
        "country": round(country_score, 4),
        "final": round(score, 4),
    }
    return score, breakdown


def decide(score: float, options: MatchOptions) -> str:
    if score >= options.auto_accept_threshold:
        return "auto_accept"
    if score >= options.review_threshold:
        return "review"
    return "reject"


def match_records(
    left_records: list[CompanyRecord],
    right_records: list[CompanyRecord],
    options: MatchOptions,
) -> list[MatchResult]:
    results: list[MatchResult] = []

    for left in left_records:
        candidates: list[MatchCandidate] = []

        for right in right_records:
            score, breakdown = score_pair(left, right)
            candidates.append(
                MatchCandidate(
                    id=right.id,
                    name=right.name,
                    confidence=round(score, 4),
                    score_breakdown=breakdown,
                )
            )

        candidates.sort(key=lambda c: c.confidence, reverse=True)

        best = candidates[0] if candidates else None
        decision = decide(best.confidence if best else 0.0, options)
        alternatives = candidates[1 : options.top_k] if options.include_alternatives else []

        results.append(
            MatchResult(
                left_id=left.id,
                left_name=left.name,
                best_match=best,
                alternatives=alternatives,
                decision=decision,
            )
        )

    return results
