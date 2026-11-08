---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commit history since the latest tag, categorizing commits into Added, Fixed, Changed, and Removed sections.
---

# `/generate-changelog` Skill

Automatically builds a Keep a Changelog 1.1.0 compliant `CHANGELOG.md` from a repository's git history since the last git tag (or across the full repository history when no tags exist yet).

## Usage

Run from the root of any git repository:

```bash
bash changelog.sh
```

Or specify a custom repository path, starting tag, version label, or stdout output:

```bash
bash changelog.sh --repo /path/to/repo --version "1.2.0" --output CHANGELOG.md
bash changelog.sh --stdout
```

## Categorization Rules

1. **Added**: `feat`, `feature`, `add`, or subjects starting with `add`/`implement`/`introduce`/`create`.
2. **Fixed**: `fix`, `bugfix`, `hotfix`, `security`, or subjects starting with `fix`/`resolve`/`patch`/`repair`.
3. **Removed**: `remove`, `delete`, `drop`, `deprecate`, `revert`, or subjects starting with `remove`/`delete`/`drop`.
4. **Changed**: `refactor`, `perf`, `docs`, `chore`, `build`, `ci`, `style`, `test`, and all other non-merge updates.
