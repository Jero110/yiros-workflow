# Security policy

## Scope

Yiros Workflow contains executable shell hooks, TypeScript extensions, Python utilities, agent instructions, and package lockfiles. A malicious change to any of these files may execute with the privileges of the person who installs it.

## Supported version

Only the latest commit on `main` is supported. Review the commit hash and the complete diff before installing or updating.

## Reporting a vulnerability

Do not open a public issue containing credentials, exploit payloads, or sensitive machine details. Use GitHub's private vulnerability reporting feature for this repository. Include:

- affected file and line;
- impact and required preconditions;
- a minimal reproduction with secrets removed;
- a proposed mitigation, if available.

If private reporting is unavailable, open a public issue that requests a private contact channel without disclosing the vulnerability.

## Security guarantees and limits

The automated checks detect common credential formats, malformed configuration, shell syntax errors, Python syntax errors, and known npm advisories. They cannot prove that the repository contains no secrets or vulnerabilities.

Before installation:

- inspect the full diff;
- run `./scripts/check-public.sh --online`;
- verify symlink targets;
- review all permission and hook configuration;
- authenticate locally after files are installed.

The repository intentionally excludes local permission files and defaults to normal Claude Code permission prompts. Setting `CC_DANGEROUS_SKIP_PERMISSIONS=1` disables those prompts for the `cc` wrapper and should be limited to isolated, explicitly trusted workspaces.

