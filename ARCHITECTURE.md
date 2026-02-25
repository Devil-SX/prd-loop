# Architecture

## Bird's Eye View

EVA-01 is an autonomous coding agent framework that converts human specs into working code through a three-stage pipeline: **spec → PRD → implementation → observation**. It ships as both headless CLI tools (for unattended batch execution) and Claude Code plugin commands (for interactive human-AI collaboration).

The core idea: minimize human interaction frequency ($v$) to maximize the compute leverage ($T$) an individual can wield. Specs are refined upfront so that implementation can run autonomously in a loop.

## Code Map

### `src/eva_01/`

The Python package containing all core logic.

| File | Role |
|------|------|
| `spec_to_prd.py` | CLI entry point: reads a spec markdown, invokes Claude to generate PRD JSON |
| `impl_prd.py` | CLI entry point: autonomous loop that implements PRD user stories one by one |
| `observe_impl.py` | CLI entry point: analyzes session logs, generates reports, creates GitHub Issues |
| `prd_schema.py` | `PRD` and `UserStory` dataclasses — the canonical PRD JSON schema |
| `config.py` | `PrdConfig` — runtime configuration (allowed tools, timeouts, thresholds) |
| `claude_cli.py` | Wrapper around the `claude` CLI — spawns Claude processes, streams output |
| `session_logger.py` | Per-session logging: creates session directories, writes loop JSONL files |
| `response_analyzer.py` | Parses Claude's stream-json output for status signals and tool usage |
| `circuit_breaker.py` | Detects consecutive failures and no-progress loops, triggers early exit |
| `rate_limiter.py` | Tracks API call counts, enforces per-hour rate limits |
| `logger.py` | Shared logging configuration |

### `src/eva_01/prompt/`

Prompt templates as Python string constants. Each module exports one main prompt.

| File | Prompt | Used by |
|------|--------|---------|
| `conversion.py` | `CONVERSION_PROMPT` | `spec_to_prd.py` |
| `implementation.py` | `IMPLEMENTATION_PROMPT` | `impl_prd.py` |
| `observe.py` | `OBSERVE_PROMPT` | `observe_impl.py` |

### `commands/`

Claude Code plugin skill definitions (Markdown + YAML frontmatter).

**Design principle**: These commands are **decoupled from EVA-01's PRD pipeline** — they are general-purpose repository tools that can be used standalone in any project.

| File | Skill | Description |
|------|-------|-------------|
| `discuss_spec.md` | `/discuss_spec` | Interactive spec refinement via discriminative questioning — can output spec file or execute via `EnterPlanMode` |
| `structured_repo.md` | `/structured_repo` | Repository structure conventions (init/audit/update CLAUDE.md, ARCHITECTURE.md, CHANGELOG.md, .gitignore, CI) |

These commands deliberately avoid PRD-specific terminology and can be installed as a plugin in any Claude Code project.

### `docs/`

Long-form documentation extracted from README.

| File | Content |
|------|---------|
| `design-philosophy.md` | Compute leverage, human bottleneck, radiation effect |
| `prd-protocol.md` | PRD JSON format, `.prd/` directory structure, configuration, completion signals |

## Entry Points

| Entry | Type | Defined in |
|-------|------|------------|
| `spec-to-prd` | CLI (pyproject.toml) | `src/eva_01/spec_to_prd.py:main` |
| `impl-prd` | CLI (pyproject.toml) | `src/eva_01/impl_prd.py:main` |
| `observe-impl` | Shell wrapper (install.sh) | `src/eva_01/observe_impl.py` |
| `/discuss_spec` | Claude Code plugin | `commands/discuss_spec.md` |
| `/structured_repo` | Claude Code plugin | `commands/structured_repo.md` |

## Cross-Cutting Concerns

- **Claude CLI interaction**: All three headless tools communicate with Claude via `claude_cli.py`, which spawns `claude` as a subprocess with `--output-format stream-json` and streams the output
- **Session logging**: `impl_prd.py` creates a session directory under `.prd/logs/` via `session_logger.py`; each loop iteration writes a raw JSONL file (`loop_001.jsonl`)
- **Safety guardrails**: `circuit_breaker.py` (consecutive failures), `rate_limiter.py` (API call budget), and configurable `allowed_tools` in `config.py` constrain what Claude can do
- **PRD as shared state**: The PRD JSON file (`.prd/prds/*.json`) is the single source of truth — `impl_prd.py` reads it, passes stories to Claude, and Claude updates `passes`/`completed_at` fields directly

## Invariants

- PRD JSON must round-trip through `PRD.from_dict()` → `PRD.to_dict()` without data loss
- `impl_prd.py` never commits code unless all regression tests pass (enforced in prompt, not in Python)
- Loop log files are raw JSONL (Claude stream-json output) — no headers, no footers
- Plugin commands in `commands/` must have `name` and `description` in YAML frontmatter
