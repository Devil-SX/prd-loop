<h1 align="center">EVA-01</h1>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.5.1-blue" alt="version">
  <img src="https://img.shields.io/badge/Python-1887_lines-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Shell-248_lines-4EAA25?logo=gnubash&logoColor=white" alt="Shell">
  <img src="https://img.shields.io/badge/Markdown-262_lines-000000?logo=markdown&logoColor=white" alt="Markdown">
</p>

<p align="center">
  <b><a href="./README.md">中文</a></b> | <a href="./README_EN.md">English</a>
</p>

<p align="center">
  <img src="./eva.jpg" width="100%" alt="EVA-01">
</p>

自动化生活的测试平台原型机。目标是在 AI 快速发展的时代，探索人类与 AI 高效协作的方式。

> 设计哲学详见 [docs/design-philosophy.md](docs/design-philosophy.md)

---

## 工具总览

EVA-01 提供两类工具：

| 类型 | 运行方式 | 适用场景 | 安装方式 |
|------|----------|----------|----------|
| **Headless CLI** | 终端直接运行，无需人工介入 | 批量执行、CI/CD、无人值守 | `./install.sh` |
| **Claude Code Plugin** | Claude Code 交互式会话中使用 | 需求讨论、spec 打磨、人机协作 | `claude plugin install eva-01` |

### Headless CLI 工具

通过 `./install.sh` 安装到 `~/.local/bin/`，可在任意项目中直接调用：

| 命令 | 说明 |
|------|------|
| `spec-to-prd` | 将 spec 转换为 PRD JSON，自动分析项目结构 |
| `impl-prd` | 自主循环实现 PRD 中的 user stories |
| `observe-impl` | 分析执行日志，生成报告并推送 GitHub Issue |

### Claude Code Plugin（交互式）

通过 Claude Code plugin 系统安装，在会话中用 `/` 触发：

| 命令 | 说明 |
|------|------|
| `/discuss_spec` | 通过辨析式提问挖掘用户真实意图，完善 spec 和 plan |
| `/structured_repo` | 仓库结构化规范：创建/审计/更新索引文件 |

---

## 快速开始

```bash
# 安装 Headless CLI
./install.sh

# 安装 Claude Code Plugin
claude plugin marketplace add /path/to/my-ralph/.claude-plugin/marketplace.json
claude plugin install eva-01

# 进入你的项目
cd your-project

# 先用交互式 plugin 打磨需求
# （在 Claude Code 会话中）/discuss_spec my-feature.md

# 再用 headless CLI 批量执行
spec-to-prd my-feature.md
impl-prd
```

卸载：CLI 用 `./uninstall.sh`，Plugin 用 `claude plugin uninstall eva-01`

---

## 命令详解

### spec-to-prd

将 spec markdown 转换为 PRD JSON。会自动分析项目结构，生成与现有代码兼容的 PRD。

```bash
spec-to-prd <SPEC_FILE> [OPTIONS]
```

| 参数 | 简写 | 说明 |
|------|------|------|
| `SPEC_FILE` | - | Spec markdown 文件路径（必需） |
| `--output FILE` | `-o` | 输出路径（默认: `.prd/prds/<name>.json`） |
| `--project NAME` | `-p` | 项目名称（默认: 从文件名推断） |
| `--model MODEL` | `-m` | Claude 模型: opus/sonnet/haiku（默认: opus） |
| `--timeout MINUTES` | - | 超时分钟数（默认: 15） |

### impl-prd

自主循环实现 PRD 中的 user stories。

```bash
impl-prd [OPTIONS]
```

| 参数 | 说明 |
|------|------|
| `--prd FILE` | PRD 文件路径（默认: `.prd/prds/` 下最新） |
| `--max-iterations N` | 最大迭代次数（默认: 50） |
| `--timeout MINUTES` | 输出超时分钟数（默认: 15） |
| `--model`, `-m` | Claude 模型（默认: opus） |
| `--resume` | 从上次状态恢复（中断后自动恢复） |
| `--status` | 显示当前状态后退出 |
| `--reset` | 重置状态，重新开始 |
| `--no-observe` | 结束后不自动运行 observe-impl |

### observe-impl

分析 impl-prd 的执行日志，生成报告并可选推送 GitHub Issue。

```bash
observe-impl [OPTIONS]
```

| 参数 | 简写 | 说明 |
|------|------|------|
| `--session PATH` | `-s` | 指定 session 目录 |
| `--latest` | `-l` | 分析最新 session |
| `--no-issue` | - | 不创建 GitHub Issue |
| `--model MODEL` | `-m` | Claude 模型（默认: haiku） |

---

## 更多文档

| 文档 | 内容 |
|------|------|
| [docs/design-philosophy.md](docs/design-philosophy.md) | 设计哲学：算力杠杆、人类瓶颈、辐射效应 |
| [docs/prd-protocol.md](docs/prd-protocol.md) | PRD 内部协议：JSON 格式、目录结构、配置项 |
