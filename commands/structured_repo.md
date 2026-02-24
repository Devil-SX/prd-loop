---
name: structured_repo
description: Apply structured repository conventions — create or update CLAUDE.md, ARCHITECTURE.md, CHANGELOG.md, .gitignore, and CI config so both humans and agents can navigate the codebase without reading all source code.
argument-hint: [init | audit | update <file>]
---

# Structured Repository Convention

A well-structured repository is an **indexed** repository. The goal is that any reader — human or AI agent — can understand the project's purpose, locate any piece of code, and start contributing within minutes, without reading all source files.

---

## Subcommands

| Subcommand | Action |
|------------|--------|
| `init` | Bootstrap all convention files from scratch for the current repo |
| `audit` | Check which convention files exist, flag missing or outdated ones |
| `update <file>` | Update a specific file (e.g., `update ARCHITECTURE.md` after refactoring) |

If no subcommand is given, default to `audit`.

---

## Document Hierarchy

```
Repository Root
├── CLAUDE.md           # Meta-index (for agents & developers)
├── README.md           # User-facing (usage & philosophy)
├── ARCHITECTURE.md     # Code map (structure & modules)
├── CHANGELOG.md        # Version history (Keep a Changelog)
├── .gitignore          # Ignore rules
└── .github/workflows/  # CI configuration (if applicable)
```

### Naming Convention

All project-level meta files use **ALL CAPS** names (`CLAUDE.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `README.md`). This is a long-standing open-source convention that visually separates meta files from source code in directory listings. **Never** use lowercase (`architecture.md`) or mixed case (`Architecture.md`).

---

## 1. CLAUDE.md — Meta-Index

**Audience**: AI agents and developers.
**Role**: The single entry point. An agent reads this file first and knows where everything else is.

### Required Sections

```markdown
# CLAUDE.md

## Quick Reference
- Language: [Python/TypeScript/Rust/...]
- Package manager: [uv/npm/cargo/...]
- Test command: `[pytest / npm test / cargo test]`
- Lint command: `[ruff check / eslint / clippy]`
- Build command: `[uv build / npm run build / cargo build]`

## Project Index
- [README.md](README.md) — User guide & design philosophy
- [ARCHITECTURE.md](ARCHITECTURE.md) — Code map & module descriptions
- [CHANGELOG.md](CHANGELOG.md) — Version history

## Commit Conventions
[Project-specific commit rules, e.g., update badges, sync version numbers]

## Development Notes
[Anything an agent or developer needs to know that doesn't belong elsewhere:
 coding style, known gotchas, environment setup, etc.]
```

### Rules
- Every indexed document MUST appear in the `## Project Index` section
- If a new document is created that agents should know about, it MUST be added here
- Keep operational commands (test, lint, build) up to date — agents rely on these

---

## 2. README.md — User Guide

**Audience**: End users and potential contributors browsing the repo.
**Role**: Explain what the project does and how to use it.

### Should Include
- Project name, badges, brief description
- Design philosophy / motivation (if applicable)
- Installation instructions
- Usage examples
- Configuration reference
- License

### Should NOT Include
- Internal architecture details (use ARCHITECTURE.md)
- Developer setup / build commands (use CLAUDE.md)
- Changelog (use CHANGELOG.md)

---

## 3. ARCHITECTURE.md — Code Map

**Audience**: Developers and agents who need to modify the code.
**Role**: A bird's-eye map of the codebase. Following the [matklad ARCHITECTURE.md convention](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html).

### Required Sections

```markdown
# Architecture

## Bird's Eye View
[1-3 paragraphs: what the project does at a high level, major components]

## Code Map
[For each important directory/module, a brief description]

### `src/module_a/`
[What this module does, key files, public API]

### `src/module_b/`
[What this module does, key files, public API]

## Entry Points
[How the program starts, main entry points, CLI commands]

## Cross-Cutting Concerns
[Patterns that span multiple modules: error handling, logging, configuration]

## Invariants
[Important rules that must always hold, e.g., "all public APIs must have tests"]
```

### Rules
- Keep it concise — this is a map, not documentation
- Update when project structure changes (new modules, renamed directories, new entry points)
- Do NOT document individual functions — only module-level and above

---

## 4. CHANGELOG.md — Version History

**Audience**: Users, contributors, and release automation.
**Role**: Track what changed between versions.

### Format: [Keep a Changelog](https://keepachangelog.com/)

```markdown
# Changelog

## [Unreleased]

## [1.2.0] - 2026-02-24

> **Code Stats** | Total: 5,320 lines | Delta: +280 (-45) = **+235 net** | Change: **+4.6%** vs v1.1.0

### Added
- New feature X

### Changed
- Modified behavior of Y

### Fixed
- Bug in Z
```

### Categories
Use exactly these section headers (omit empty ones):
- **Added** — new features
- **Changed** — changes to existing functionality
- **Deprecated** — soon-to-be removed features
- **Removed** — removed features
- **Fixed** — bug fixes
- **Security** — vulnerability fixes

### Semantic Versioning

Follow [Semantic Versioning 2.0.0](https://semver.org/):

| Change Type | Version Bump | Example |
|-------------|-------------|---------|
| Breaking change (incompatible API) | **Major** | 1.0.0 → 2.0.0 |
| New feature (backward compatible) | **Minor** | 1.0.0 → 1.1.0 |
| Bug fix (backward compatible) | **Patch** | 1.0.0 → 1.0.1 |

### Release Process
1. Move entries from `[Unreleased]` to a new version section with today's date
2. Update version in project config (`pyproject.toml`, `package.json`, etc.)
3. Commit: `release: vX.Y.Z — brief summary`
4. Create annotated git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
5. Push commit and tag: `git push && git push origin vX.Y.Z`

---

## 5. .gitignore — Ignore Rules

### Must Ignore
| Category | Patterns |
|----------|----------|
| **Build artifacts** | `dist/`, `build/`, `*.egg-info/`, `__pycache__/` |
| **Dependencies** | `node_modules/`, `.venv/`, `venv/` |
| **IDE** | `.idea/`, `.vscode/`, `*.swp`, `.DS_Store` |
| **Environment** | `.env`, `.env.local`, `*.pem`, `credentials.*` |
| **OS** | `Thumbs.db`, `.DS_Store` |
| **Project-specific** | Runtime caches, generated files |

### Must NOT Ignore
- Lock files (`uv.lock`, `package-lock.json`, `Cargo.lock`)
- CI configuration (`.github/workflows/`)
- Project meta files (`CLAUDE.md`, `ARCHITECTURE.md`, etc.)

---

## 6. CI & Regression Testing

Test management does not need a separate document. Instead:

### Test Commands in CLAUDE.md
The `## Quick Reference` section in CLAUDE.md must list the exact test command. This is the single source of truth for how to run tests.

### CI Configuration
Use the platform's native CI format:
- GitHub: `.github/workflows/ci.yml`
- GitLab: `.gitlab-ci.yml`
- Other: project-appropriate format

### Minimum CI Pipeline
A CI workflow should at minimum:
1. **Install dependencies**
2. **Run linter** (if applicable)
3. **Run full test suite**
4. Trigger on: push to main, pull requests

### Test Organization
- Tests live in a dedicated directory (`tests/`, `__tests__/`, `test/`)
- Mirror the source directory structure where practical
- Name test files to match source files (`src/auth.py` → `tests/test_auth.py`)

---

## Execution Instructions

### `init` — Bootstrap

1. Read existing project files to understand the tech stack
2. For each convention file that does NOT exist, create it with the templates above, filled in from project context
3. For each convention file that DOES exist, check if it follows the conventions and suggest improvements
4. Ensure CLAUDE.md references all other convention files

### `audit` — Check Compliance

1. Check existence of each convention file
2. Verify CLAUDE.md has all required sections and references
3. Verify ARCHITECTURE.md reflects current directory structure
4. Verify CHANGELOG.md has an `[Unreleased]` section
5. Verify .gitignore covers all required categories
6. Report findings as a checklist:
   ```
   [x] CLAUDE.md — exists, has Quick Reference, has Project Index
   [ ] ARCHITECTURE.md — exists but Code Map is outdated (missing src/new_module/)
   [x] CHANGELOG.md — exists, has Unreleased section
   [x] .gitignore — exists, covers all categories
   ```

### `update <file>` — Targeted Update

1. Read the specified file and current project state
2. Update the file to reflect current project reality
3. If updating ARCHITECTURE.md, re-scan the directory structure and reconcile
4. If updating CLAUDE.md, verify all index references are still valid
