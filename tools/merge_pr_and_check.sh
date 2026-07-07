#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: tools/merge_pr_and_check.sh <PR_NUMBER>" >&2
}

if [[ "$#" -ne 1 ]]; then
  usage
  exit 2
fi

pr="$1"

if [[ ! "$pr" =~ ^[0-9]+$ ]]; then
  echo "Error: PR number must be numeric." >&2
  usage
  exit 2
fi

echo "PR #$pr file list:"
gh pr diff "$pr" --name-only

echo
echo "Human gate: review the file list above before merge."
printf "Merge PR #%s? Type 'yes' to continue: " "$pr"
read -r confirmation

if [[ "$confirmation" != "yes" ]]; then
  echo "Merge cancelled."
  exit 1
fi

gh pr merge "$pr" --merge --delete-branch

git checkout tests
git pull origin tests

make post-merge-check

git branch --show-current
git status --short
