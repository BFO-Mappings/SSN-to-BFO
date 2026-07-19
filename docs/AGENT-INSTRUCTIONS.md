# Agent Instructions

Follow the repository branch flow:

```text
feature/* -> dev -> stage -> main
```

When creating branches for routine Codex work:

- Start from the latest `dev`.
- Use a `feature/<short-description>` branch name.
- Target pull requests to `dev`.
- Do not create feature branches from `stage` or `main` unless the user explicitly asks for a release or emergency branch.
- Do not force-push, rewrite history, delete branches, rename branches, or merge unrelated open work unless the user explicitly instructs you to do so.

For promotion work, use pull requests in this order:

- `dev` -> `stage`
- `stage` -> `main`

Avoid modifying release artifacts under `releases/` or generated build artifacts unless the task explicitly requires those files.
