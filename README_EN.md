<h1 align="center">EVA-01</h1>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.5.1-blue" alt="version">
  <img src="https://img.shields.io/badge/Python-1887_lines-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Shell-248_lines-4EAA25?logo=gnubash&logoColor=white" alt="Shell">
  <img src="https://img.shields.io/badge/Markdown-262_lines-000000?logo=markdown&logoColor=white" alt="Markdown">
</p>

<p align="center">
  <a href="./README.md">中文</a> | <b><a href="./README_EN.md">English</a></b>
</p>

<p align="center">
  <img src="./eva.jpg" width="100%" alt="EVA-01">
</p>

A prototype testing platform for automating life. The goal is to explore efficient human-AI collaboration in the age of rapidly advancing AI.

> Design philosophy: [docs/design-philosophy.md](docs/design-philosophy.md)

---

## Tool Overview

EVA-01 provides two types of tools:

| Type | How it runs | Best for | Installation |
|------|-------------|----------|-------------|
| **Headless CLI** | Runs directly in terminal, no human intervention | Batch execution, CI/CD, unattended runs | `./install.sh` |
| **Claude Code Plugin** | Used within Claude Code interactive sessions | Spec discussion, requirement refinement, human-AI collaboration | `claude plugin install eva-01` |

### Headless CLI Tools

Installed to `~/.local/bin/` via `./install.sh`, callable from any project:

| Command | Description |
|---------|-------------|
| `spec-to-prd` | Convert spec to PRD JSON with automatic project analysis |
| `impl-prd` | Autonomous loop to implement PRD user stories |
| `observe-impl` | Analyze execution logs, generate reports, push GitHub Issues |

### Claude Code Plugin (Interactive)

Installed via the Claude Code plugin system, triggered with `/` in sessions:

| Command | Description |
|---------|-------------|
| `/discuss_spec` | Refine spec and plan through discriminative questioning to uncover true user intent |
| `/structured_repo` | Repository structure conventions: create/audit/update index files |

---

## Quick Start

```bash
# Install Headless CLI
./install.sh

# Install Claude Code Plugin
claude plugin marketplace add /path/to/my-ralph/.claude-plugin/marketplace.json
claude plugin install eva-01

# Go to your project
cd your-project

# First, refine requirements with the interactive plugin
# (in a Claude Code session) /discuss_spec my-feature.md

# Then execute headlessly
spec-to-prd my-feature.md
impl-prd
```

Uninstall: CLI via `./uninstall.sh`, Plugin via `claude plugin uninstall eva-01`

---

## Command Reference

### spec-to-prd

Converts spec markdown to PRD JSON. Automatically analyzes the project structure to generate a compatible PRD.

```bash
spec-to-prd <SPEC_FILE> [OPTIONS]
```

| Parameter | Short | Description |
|-----------|-------|-------------|
| `SPEC_FILE` | - | Spec markdown file path (required) |
| `--output FILE` | `-o` | Output path (default: `.prd/prds/<name>.json`) |
| `--project NAME` | `-p` | Project name (default: inferred from filename) |
| `--model MODEL` | `-m` | Claude model: opus/sonnet/haiku (default: opus) |
| `--timeout MINUTES` | - | Timeout in minutes (default: 15) |

### impl-prd

Autonomously implements PRD user stories in a loop.

```bash
impl-prd [OPTIONS]
```

| Parameter | Description |
|-----------|-------------|
| `--prd FILE` | PRD file path (default: latest in `.prd/prds/`) |
| `--max-iterations N` | Max iterations (default: 50) |
| `--timeout MINUTES` | Output timeout in minutes (default: 15) |
| `--model`, `-m` | Claude model (default: opus) |
| `--resume` | Resume from last state (auto-resumes on interrupt) |
| `--status` | Show current state and exit |
| `--reset` | Reset state, start fresh |
| `--no-observe` | Skip auto-running observe-impl on completion |

### observe-impl

Analyzes impl-prd execution logs, generates reports, and optionally pushes GitHub Issues.

```bash
observe-impl [OPTIONS]
```

| Parameter | Short | Description |
|-----------|-------|-------------|
| `--session PATH` | `-s` | Session directory path |
| `--latest` | `-l` | Analyze most recent session |
| `--no-issue` | - | Don't create GitHub Issues |
| `--model MODEL` | `-m` | Claude model (default: haiku) |

---

## More Documentation

| Document | Content |
|----------|---------|
| [docs/design-philosophy.md](docs/design-philosophy.md) | Design philosophy: compute leverage, human bottleneck, radiation effect |
| [docs/prd-protocol.md](docs/prd-protocol.md) | PRD internal protocol: JSON format, directory structure, configuration |
