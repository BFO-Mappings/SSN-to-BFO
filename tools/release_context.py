#!/usr/bin/env python3
"""Validate explicit immutable formal-release identity inputs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Iterable


RELEASE_IDENTIFIER_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
SOURCE_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
CONTEXT_FIELDS = (
    "release_identifier",
    "release_date",
    "git_tag",
    "source_commit",
)


@dataclass(frozen=True)
class FormalReleaseValidationIssue:
    code: str
    field: str
    message: str


@dataclass(frozen=True)
class FormalReleaseContext:
    release_identifier: str
    release_date: str
    git_tag: str
    source_commit: str


class FormalReleaseContextError(ValueError):
    """One or more deterministic formal-release context failures."""

    def __init__(self, issues: Iterable[FormalReleaseValidationIssue]):
        self.issues = tuple(issues)
        super().__init__("; ".join(format_issue(issue) for issue in self.issues))


def format_issue(issue: FormalReleaseValidationIssue) -> str:
    return f"ERROR [{issue.code}] {issue.field}: {issue.message}"


def _issue(code: str, field: str, message: str) -> FormalReleaseValidationIssue:
    return FormalReleaseValidationIssue(code=code, field=field, message=message)


def _canonical_date_issue(value: object, field: str) -> FormalReleaseValidationIssue | None:
    if not isinstance(value, str) or RELEASE_IDENTIFIER_PATTERN.fullmatch(value) is None:
        return _issue(
            "RELEASE_DATE_FORMAT" if field == "release_date" else "RELEASE_ID_FORMAT",
            field,
            "expected exactly YYYY-MM-DD",
        )
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return _issue(
            "RELEASE_DATE_INVALID",
            field,
            f"invalid Gregorian calendar date: {value}",
        )
    if parsed.isoformat() != value:
        return _issue(
            "RELEASE_DATE_FORMAT" if field == "release_date" else "RELEASE_ID_FORMAT",
            field,
            "expected a zero-padded Gregorian date in YYYY-MM-DD form",
        )
    return None


def validate_release_identifier(value: object) -> str:
    """Return one canonical date release identifier or raise deterministic issues."""

    problem = _canonical_date_issue(value, "release_identifier")
    if problem is not None:
        raise FormalReleaseContextError((problem,))
    assert isinstance(value, str)
    return value


def expected_git_tag(release_identifier: object) -> str:
    return "v" + validate_release_identifier(release_identifier)


def formal_release_context_issues(
    release_identifier: object,
    release_date: object,
    git_tag: object,
    source_commit: object,
) -> tuple[FormalReleaseValidationIssue, ...]:
    """Return all context issues in stable field and policy order."""

    issues: list[FormalReleaseValidationIssue] = []
    identifier_problem = _canonical_date_issue(release_identifier, "release_identifier")
    if identifier_problem is not None:
        issues.append(identifier_problem)

    date_problem = _canonical_date_issue(release_date, "release_date")
    if date_problem is not None:
        issues.append(date_problem)

    if identifier_problem is None and date_problem is None and release_date != release_identifier:
        issues.append(
            _issue(
                "RELEASE_DATE_MISMATCH",
                "release_date",
                f"expected {release_identifier}, got {release_date}",
            )
        )

    if not isinstance(git_tag, str) or re.fullmatch(r"v[0-9]{4}-[0-9]{2}-[0-9]{2}", git_tag) is None:
        issues.append(_issue("GIT_TAG_FORMAT", "git_tag", "expected exactly vYYYY-MM-DD"))
    elif identifier_problem is None and git_tag != f"v{release_identifier}":
        issues.append(
            _issue(
                "RELEASE_TAG_MISMATCH",
                "git_tag",
                f"expected v{release_identifier}, got {git_tag}",
            )
        )

    if not isinstance(source_commit, str) or SOURCE_COMMIT_PATTERN.fullmatch(source_commit) is None:
        issues.append(
            _issue(
                "SOURCE_COMMIT_FORMAT",
                "source_commit",
                "expected exactly 40 lowercase hexadecimal characters",
            )
        )
    return tuple(issues)


def parse_formal_release_context(
    release_identifier: object = None,
    release_date: object = None,
    git_tag: object = None,
    source_commit: object = None,
) -> FormalReleaseContext:
    """Validate explicit values and return one frozen formal-release context."""

    issues = formal_release_context_issues(
        release_identifier,
        release_date,
        git_tag,
        source_commit,
    )
    if issues:
        raise FormalReleaseContextError(issues)
    assert isinstance(release_identifier, str)
    assert isinstance(release_date, str)
    assert isinstance(git_tag, str)
    assert isinstance(source_commit, str)
    return FormalReleaseContext(
        release_identifier=release_identifier,
        release_date=release_date,
        git_tag=git_tag,
        source_commit=source_commit,
    )


def validate_formal_release_context(context: object) -> FormalReleaseContext:
    if not isinstance(context, FormalReleaseContext):
        raise FormalReleaseContextError(
            (_issue("RELEASE_CONTEXT_TYPE", "release_context", "expected FormalReleaseContext"),)
        )
    return parse_formal_release_context(
        context.release_identifier,
        context.release_date,
        context.git_tag,
        context.source_commit,
    )
