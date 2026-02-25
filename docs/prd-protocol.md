# PRD Internal Protocol

## PRD JSON Format

```json
{
  "project": "ProjectName",
  "branchName": "ralph/feature-name",
  "description": "Feature description",
  "source_spec": "specs/feature-name.md",
  "created_at": "2026-02-02T10:30:00",
  "updated_at": "2026-02-02T11:00:00",
  "userStories": [
    {
      "id": "US-001",
      "title": "Story title",
      "description": "As a [user], I want [feature] so that [benefit]",
      "acceptanceCriteria": ["Criterion 1", "Criterion 2", "All tests pass"],
      "priority": 1,
      "passes": false,
      "notes": "",
      "testPlan": "Unit test for ...; integration test for ...",
      "completed_at": null
    }
  ]
}
```

## .prd/ Directory Structure

First run of `spec-to-prd` auto-creates:

```
your-project/
└── .prd/
    ├── specs/          # Original spec markdowns
    ├── prds/           # Generated PRD JSONs
    ├── logs/           # Execution logs
    │   └── session_YYYYMMDD_HHMMSS/
    │       ├── config.json           # Runtime config snapshot
    │       ├── prd_snapshot.json     # PRD snapshot
    │       ├── args.json             # CLI arguments
    │       ├── session.log           # Main log
    │       ├── loop_001.jsonl        # Raw stream-json per loop
    │       ├── summary.json          # Run summary
    │       └── observation_report.md # Observation report
    ├── config.json     # Project config
    └── state.json      # Run state (for resume)
```

## Configuration

```json
{
  "max_calls_per_hour": 100,
  "max_iterations": 50,
  "timeout_minutes": 15,
  "output_format": "stream",
  "allowed_tools": ["Write", "Read", "Edit", "Glob", "Bash(git *)", "Bash(gh *)", "Bash(npm *)", "Bash(npx *)", "Bash(pytest)", "Bash(python -m pytest *)"],
  "session_expiry_hours": 24,
  "max_consecutive_failures": 3,
  "no_progress_threshold": 3
}
```

| Option | Description | Default |
|--------|-------------|---------|
| `max_calls_per_hour` | Max API calls per hour | 100 |
| `max_iterations` | Max loop iterations | 50 |
| `timeout_minutes` | Claude timeout (minutes) | 15 |
| `output_format` | Output format: stream / json | stream |
| `allowed_tools` | Allowed tool list | see above |
| `session_expiry_hours` | Session expiry (hours) | 24 |
| `max_consecutive_failures` | Max consecutive failures | 3 |
| `no_progress_threshold` | No-progress threshold | 3 |

## Completion Signals

When Claude completes a story:

```
---RALPH_STATUS---
STATUS: COMPLETE
STORY_ID: US-001
STORY_PASSED: true
FILES_MODIFIED: [file1.py, file2.py]
EXIT_SIGNAL: false
---END_RALPH_STATUS---
```

When all stories are complete:

```
<promise>COMPLETE</promise>
```
