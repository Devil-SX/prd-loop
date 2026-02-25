# CLAUDE.md

## Quick Reference
- Language: Python 3.8+
- Package manager: uv
- Build command: `uv build`
- Install (CLI): `./install.sh`
- No test suite yet — EVA-01 is a prompt-driven tool; validation is done via manual runs of `spec-to-prd` and `impl-prd`

## Project Index
- [README.md](README.md) — User guide (Chinese)
- [README_EN.md](README_EN.md) — User guide (English)
- [ARCHITECTURE.md](ARCHITECTURE.md) — Code map & module descriptions
- [CHANGELOG.md](CHANGELOG.md) — Version history
- [docs/design-philosophy.md](docs/design-philosophy.md) — Design philosophy: compute leverage, human bottleneck, radiation effect
- [docs/prd-protocol.md](docs/prd-protocol.md) — PRD internal protocol: JSON format, directory structure, configuration

## Commit Conventions

提交代码时，需要同步更新 README 中的 cloc badges：

1. 运行 `cloc src/ install.sh uninstall.sh commands/ --json` 获取最新代码行数
2. 更新 `README.md` 和 `README_EN.md` 中 shields.io badges 的行数（Python、Shell、Markdown）
3. Badge 格式：`https://img.shields.io/badge/<Language>-<N>_lines-<color>`

更新版本号时，也需要同步 `.claude-plugin/marketplace.json` 中的版本号。

## Development Notes
- Entry points are defined in `pyproject.toml` under `[project.scripts]`: `spec-to-prd` and `impl-prd`
- `observe-impl` is not a pyproject entry point — it is installed as a shell wrapper by `install.sh`
- Prompts live in `src/eva_01/prompt/` as Python string templates with `{placeholders}`
- Claude Code plugin commands live in `commands/` as Markdown files with YAML frontmatter
- The `.prd/` directory is runtime-generated per target project and gitignored
- All Python modules use the `eva_01` namespace under `src/eva_01/`
