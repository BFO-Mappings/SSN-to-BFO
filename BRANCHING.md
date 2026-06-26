# Branching Policy

This repository uses the following branch flow:

```text
feature/* -> dev -> stage -> main
```

## Branch Roles

- `feature/*`: short-lived work branches for focused changes.
- `dev`: integration branch for reviewed feature work.
- `stage`: stabilization branch for release candidates and final validation.
- `main`: production and public release branch.

The current GitHub default branch remains `main`. Changing the default branch, renaming branches, deleting branches, force-pushing, or rewriting history is outside this policy and requires explicit maintainer approval.

## Pull Request Targets

- Open feature pull requests from `feature/*` into `dev`.
- Promote integrated work from `dev` into `stage` with a pull request.
- Promote validated release candidates from `stage` into `main` with a pull request.
- Do not target `main` directly from a feature branch unless a maintainer explicitly requests an emergency change.

## Legacy Branches

Branches outside this flow, such as `tests`, are legacy branches. They should not receive new work unless a maintainer explicitly asks for that branch to be used. Do not delete or rename legacy branches as part of routine development.

## Release and Generated Artifacts

Release artifacts under `releases/` are protected project outputs. Do not modify them in routine feature work unless the pull request is specifically scoped to release artifact changes.

Generated reports and build artifacts should remain untracked unless the repository explicitly asks for a generated file to be committed.
