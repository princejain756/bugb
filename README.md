# Structured Git Changelog Generator (`/generate-changelog`)

Generates a Keep a Changelog 1.1.0 compliant `CHANGELOG.md` from a repository's git history since the latest git tag, automatically categorizing commits into `Added`, `Fixed`, `Changed`, and `Removed`.

## Quick Setup (3 Steps)

1. **Clone or copy** `changelog.sh`, `changelog_gen.py`, and `.claude/skills/generate-changelog/SKILL.md` into your project root.
2. **Make the script executable**:
   ```bash
   chmod +x changelog.sh
   ```
3. **Run via CLI or Claude Code `/generate-changelog`**:
   ```bash
   bash changelog.sh
   ```

## CLI Options

- `--repo <path>`: Path to target git repository (defaults to `.`).
- `--since <tag>`: Starting tag or ref (defaults to latest reachable git tag via `git describe --tags --abbrev=0`).
- `--version <label>`: Release heading label (defaults to `Unreleased`).
- `--output <file>`: Output file path (defaults to `CHANGELOG.md`).
- `--stdout`: Print generated Markdown to stdout.

## Running Tests

```bash
python3 -m unittest discover -s tests -v
```
