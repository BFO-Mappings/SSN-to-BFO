#!/usr/bin/env bash
set -euo pipefail

base="tests"
body_file=""
created_body_file=""

usage() {
  cat <<'USAGE'
Usage:
  tools/create_pr_from_last_commit.sh
  tools/create_pr_from_last_commit.sh /tmp/ssn-to-bfo-pr-body.md
  tools/create_pr_from_last_commit.sh --base tests /tmp/ssn-to-bfo-pr-body.md
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --base)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --base requires a branch name." >&2
        usage >&2
        exit 2
      fi
      base="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "ERROR: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [ -n "$body_file" ]; then
        echo "ERROR: only one PR body file may be supplied." >&2
        usage >&2
        exit 2
      fi
      body_file="$1"
      shift
      ;;
  esac
done

branch="$(git branch --show-current)"
if [ -z "$branch" ]; then
  echo "ERROR: could not determine current branch." >&2
  exit 1
fi

case "$branch" in
  main|tests)
    echo "ERROR: refusing to create a PR from protected branch: $branch" >&2
    exit 1
    ;;
esac

echo "Current branch: $branch"
echo "Base branch: $base"

status="$(git status --short)"
git status --short
if [ -n "$status" ]; then
  echo "ERROR: working tree is dirty. Commit or restore changes before creating a PR." >&2
  exit 1
fi

title="$(git log -1 --pretty=%s)"
if [ -z "$title" ]; then
  echo "ERROR: could not determine last commit subject." >&2
  exit 1
fi

if [ -n "$body_file" ]; then
  if [ ! -f "$body_file" ]; then
    echo "ERROR: PR body file not found: $body_file" >&2
    exit 1
  fi
else
  created_body_file="$(mktemp "${TMPDIR:-/tmp}/ssn-to-bfo-pr-body.XXXXXX.md")"
  body_file="$created_body_file"
  {
    printf '# %s\n\n' "$title"
    printf '## Changed files\n\n'
    if git rev-parse --verify "origin/$base" >/dev/null 2>&1; then
      git diff --name-only "origin/$base...HEAD" | sed 's/^/- /'
    else
      git diff-tree --no-commit-id --name-only -r HEAD | sed 's/^/- /'
    fi
    printf '\n## Validation\n\n'
    printf -- '- Human gate required: confirm validation output before merge.\n'
  } > "$body_file"
fi

cleanup() {
  if [ -n "$created_body_file" ] && [ -f "$created_body_file" ]; then
    rm -f "$created_body_file"
  fi
}
trap cleanup EXIT

git push -u origin "$branch"
gh pr create --base "$base" --head "$branch" --title "$title" --body-file "$body_file"
gh pr diff --name-only

echo "Human gate: review PR diff/name-only before merge."
