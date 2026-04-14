# Skills

Skills are reusable, composable capabilities for the AI Coding Agent Framework.

## Structure

Each skill is a directory containing:

```
skill-name/
├── SKILL.md           # Skill definition
└── skill.json         # Machine-readable metadata
```

## Creating a Skill

Create a `skill.json` file:

```json
{
  "name": "code-review",
  "description": "Automated code review skill",
  "version": "1.0.0",
  "tools": ["reader", "analyzer", "commenter"],
  "steps": [
    "analyze_code",
    "check_style",
    "report_issues"
  ]
}
```

## Built-in Skills

See individual skill directories for details.
