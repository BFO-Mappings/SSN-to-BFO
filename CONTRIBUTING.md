# Contributing

Thank you for contributing to SSN-to-BFO. This repository follows the branch policy described in [BRANCHING.md](BRANCHING.md).

## Branch Flow

Use this flow for all routine work:

```text
feature/* -> dev -> stage -> main
```

Create feature branches from the latest `dev` branch:

```bash
git fetch origin
git switch dev
git pull --ff-only origin dev
git switch -c feature/<short-description>
```

Open pull requests from `feature/*` into `dev`. After feature work is integrated, maintainers promote `dev` to `stage` and `stage` to `main` with pull requests.

Do not force-push shared branches, rewrite public history, delete branches, rename branches, or merge unrelated open work unless a maintainer explicitly instructs you to do so.

## Validation

Run the repository validation described in [Validation and Release Engineering](docs/VALIDATION-AND-RELEASES.md) or in the relevant task instructions before opening a pull request.

Do not add validation commands unless the corresponding files and Make targets are present on the target branch.

## Release Files and Generated Files

The release files under `releases/` are protected project outputs. Do not edit them in routine feature work unless the pull request is specifically about release artifact content.

Generated reports and build artifacts should stay out of Git unless maintainers explicitly request a generated artifact to be committed.
