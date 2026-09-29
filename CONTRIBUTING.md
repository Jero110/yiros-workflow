# Contributing

Changes should keep the repository portable, reviewable, and safe to publish.

## Before opening a pull request

1. Remove machine-specific absolute paths and private hostnames.
2. Do not add credentials, auth files, local permission files, sessions, histories, logs, databases, caches, telemetry, or editor backups.
3. Preserve symlinks when updating shared skills.
4. Avoid broad command allowlists and dangerous-mode defaults.
5. Pin runtime dependencies in the relevant lockfile.
6. Run `./scripts/check-public.sh --online`.
7. Review `git diff --check` and the full diff.

Pull requests should explain the user-facing behavior, security impact, migration steps, and validation performed.

