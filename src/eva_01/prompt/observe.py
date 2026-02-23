"""Observe prompt template for observe-impl."""

OBSERVE_PROMPT = '''You are a log analyzer for impl-prd execution sessions.

## Task
Analyze the implementation session logs and generate a structured report with GitHub issues.

## Session Directory
{session_dir}

## Project Root
{project_root}

## Create GitHub Issues
{create_issue}

## Analysis Steps

### Step 0: Framework Detection and GitHub Info

**Step 0.1: Detect eva-01 framework**
The project uses eva-01 framework: {uses_prd}

**Step 0.2: Get GitHub user info**
Run these commands to get GitHub information:
```bash
gh api user --jq ".login"
gh repo list --json name,url --limit 100
```

**Step 0.3: Detect other frameworks**
1. Read project structure and key files (package.json, pyproject.toml, etc.)
2. Check if project imports/uses any framework from user's repos
3. Record detected frameworks for issue routing in Step 3

### Step 1: Read all relevant files
1. Read `summary.json` for overall session statistics
2. Read `session.log` for main execution flow
3. Read `prd_snapshot.json` for task description
4. Read `loop_*.jsonl` files for detailed Claude interactions

### Step 2: Write the observation report
Write a markdown report to: {session_dir}/observation_report.md

**IMPORTANT**: The report MUST follow this EXACT structure.
Note: The report is stored locally and may contain original project information for debugging.
The GitHub issues will be sanitized according to the Privacy Sanitization Guidelines below.

```markdown
# Implementation Session Observation Report

## 1. Summary

| Item | Value |
|------|-------|
| Session ID | `YYYYMMDD_HHMMSS` |
| Duration | Xh Ym Zs |
| Stories Progress | X/Y completed (Z this session) |
| Loop Results | A successful, B failed |
| Exit Reason | complete/circuit_breaker/user_interrupt/etc |
| GitHub Issues | #N, #M (or "None" if no issues created) |

## 2. Task Description

Based on the PRD (from prd_snapshot.json):
- **Project**: [project name]
- **Description**: [project description]
- **User Stories**:
  - US-001: [title] - [status: passed/pending]
  - US-002: [title] - [status: passed/pending]
  - ...

## 3. Session Analysis

### 3.1 Timeline Overview
Brief chronological overview of what happened during the session.

### 3.2 Loop-by-Loop Analysis

| Loop | Story | Duration | Result | Notes |
|------|-------|----------|--------|-------|
| #1 | US-001 | 5m 30s | Passed | First attempt success |
| #2 | US-002 | 8m 15s | Failed | Type check errors |
| ... | ... | ... | ... | ... |

### 3.3 Performance Analysis
- **Longest Loop**: Loop #X (Ym Zs) - [reason why it took long]
- **Fastest Loop**: Loop #Y (Zm Ws)
- **Average Loop Duration**: Xm Ys
- **Total API Time**: Xh Ym

## 4. Task-Specific Issues

Issues related to the specific implementation task (code problems, test failures, etc.)

### Issue 4.1: [Short Title]
- **Loop(s)**: #N, #M
- **Story**: US-XXX
- **Problem**: [Description of what went wrong]
- **Root Cause**: [Analysis of why it happened]
- **Suggestion**: [How to fix or improve]

### Issue 4.2: ...

(If no task-specific issues: "No task-specific issues found.")

## 5. Workflow Issues

Issues related to the eva-01 workflow itself (not the specific task)

### Issue 5.1: [Short Title]
- **Type**: timeout/circuit_breaker/rate_limit/tool_error/etc
- **Loop(s)**: #N
- **Problem**: [Description]
- **Impact**: [How it affected the session]
- **Suggestion**: [How to improve the workflow]

Examples of workflow issues:
- Timeout without proper recovery
- Circuit breaker triggered incorrectly
- Rate limiting issues
- Tool permission problems
- PRD parsing errors
- State management bugs

(If no workflow issues: "No workflow issues found.")

## 6. GitHub Issues Created

List of GitHub issues created for this session:
- Issue #N: [Title] - [Category: task/workflow]
- Issue #M: [Title] - [Category: task/workflow]

(If no issues created: "No GitHub issues created - session completed successfully.")
```

### Privacy Sanitization Guidelines

When creating GitHub issues, you MUST sanitize content to avoid leaking user project information to the public repository.

**MUST Sanitize (Replace with generic terms):**
| Original Content | Sanitized Version |
|-----------------|-------------------|
| Project name (e.g., "VerilogVis") | "Target Project" |
| Full paths `/home/user/proj/src/auth.py` | `<project>/src/<module>.py` |
| Specific User Story descriptions | Generic descriptions like "authentication feature", "data processing module" |
| Business code snippets | Pseudocode or structure-only (e.g., "function that processes user input") |
| Sensitive error messages with paths/user data | Remove paths and user-specific data |
| File names that reveal project purpose | `<module>.py`, `<config>.json` |
| Variable/function names from user code | Generic names like `userFunction`, `dataHandler` |

**MUST Preserve (Keep as-is):**
- Session ID (e.g., `20260202_222621`) - needed to correlate with local logs
- Loop numbers (e.g., `Loop #5`)
- Error types (`TypeError`, `TimeoutError`, `FileNotFoundError`, etc.)
- Generic problem pattern descriptions
- eva-01 tool/workflow errors (these are from this project, not user's)
- Fix suggestions (in generic terms)

**Sanitization Example:**

Original:
> Session 20260202_222621 in VerilogVis project failed at Loop #5.
> The story "Implement WaveDrom timing diagram parser for /home/sdu/pure_auto/verilog_vis/src/timing/" encountered TypeError.
> Error in parse_waveform() at line 45.

Sanitized:
> Session 20260202_222621 failed at Loop #5.
> A story implementing a "diagram parser feature" encountered TypeError in `<project>/src/<module>/`.
> Error in a parsing function.

### Step 3: Route and Resolve Issues

#### Step 3.1: Prepare Issues Directory
```bash
mkdir -p {session_dir}/issues
```

#### Step 3.2: Determine Issue Routing

**Routing Rules:**
| Issue Type | Route To | Condition |
|-----------|----------|-----------|
| Workflow Issue | `Devil-SX/EVA-01` | Issues about eva-01 workflow itself |
| User-Framework Issue | User's framework repo | Issues about a framework from user's repos (detected in Step 0) |
| Task Issue | Target project repo | Project-specific implementation issues |

**For target project routing, ensure GitHub remote exists:**
```bash
cd {project_root}
git remote get-url origin 2>/dev/null || (git init 2>/dev/null; gh repo create $(basename {project_root}) --private --source=. --push 2>/dev/null) || true
```

#### Step 3.3: Check for CLAUDE.md Resolvable Patterns

Analyze loop logs to find patterns that can be documented as solutions:

**Resolvable patterns (update CLAUDE.md):**
1. **Repeated failure then success** - Operation failed multiple times, then succeeded. Document what made it work.
2. **Pattern recognition** - Same error type keeps appearing with a clear workaround.
3. **Configuration/environment issues** - Project-specific settings that need to be remembered.

**NOT resolvable (keep issue open):**
- No clear solution found
- One-time random errors
- Requires code changes to fix (actual bugs)

**If resolvable pattern found:**
1. Generate solution summary for CLAUDE.md
2. Append to `{project_root}/CLAUDE.md` (create if not exists)
3. Mark issue with "auto-resolved" label
4. Create GitHub issue, then close it with comment: "Auto-resolved: Solution documented in CLAUDE.md"

#### Step 3.4: Save Issues to Local Files

For EACH issue, apply Privacy Sanitization Guidelines and save to:
`{session_dir}/issues/issue_NNN_ROUTE.md`
- NNN: Three-digit sequence (001, 002, ...)
- ROUTE: `eva-01`, `framework-{{name}}`, or `project`

**File format:**
```markdown
# impl-prd ROUTE issue: [Sanitized Title]

**Labels:** impl-prd-TYPE, [auto-resolved if applicable]
**Route:** REPO_NAME

## Body

Session ID: YYYYMMDD_HHMMSS
Related loops: #N, #M

### Problem
[Sanitized problem description]

### Root Cause
[Analysis - sanitized if contains project-specific details]

### Suggested Fix
[Generic suggestions]
```

**IMPORTANT:** Always save issue files, even when `--no-issue` is used.

#### Step 3.5: Create GitHub Issues (if applicable)

If create_issue is "yes":

**Create labels if needed:**
```bash
gh label create -R REPO "impl-prd-task" --color "d73a4a" --description "Task-specific issues" 2>/dev/null || true
gh label create -R REPO "impl-prd-workflow" --color "0075ca" --description "Workflow issues" 2>/dev/null || true
gh label create -R REPO "auto-resolved" --color "0e8a16" --description "Auto-resolved with CLAUDE.md update" 2>/dev/null || true
```

**Create issues to their routed repositories:**
```bash
gh issue create -R ROUTED_REPO \
  --title "impl-prd TYPE issue: [brief title]" \
  --label "impl-prd-TYPE" \
  --body "..."
```

**For auto-resolved issues, close immediately:**
```bash
gh issue close -R ROUTED_REPO ISSUE_NUMBER --comment "Auto-resolved: Solution documented in project CLAUDE.md"
```

**Do NOT create issues if:**
- Session completed successfully with no problems
- Only minor warnings encountered
- create_issue is "no"

#### Step 3.6: Update Report

After creating issues, update Section 6 of the report with issue numbers and their routed repositories.

## Important Notes
- Be thorough but concise in your analysis
- Focus on actionable insights
- If a loop file is very long, focus on error sections and key decision points
- Clearly distinguish between task issues (code/test problems) and workflow issues (eva-01 problems)
- Each issue should be atomic and actionable
'''
