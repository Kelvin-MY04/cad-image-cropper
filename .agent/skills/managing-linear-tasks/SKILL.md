---
name: managing-linear-tasks
description: A skill for managing tasks in Linear, including creating, updating, and retrieving tasks.
license: MIT
compatibility: Linear MCP Server
metadata:
  author: Kelvin
  version: "1.1"
---

# Managing Linear Tasks Skill

Manage issues in the **MY04 workspace → BIM&CostEst. team → CAD Parsing project** via the Linear MCP server.

## Context

- **Workspace**: MY04
- **Team**: BIM&CostEst.
- **Project**: CAD Parsing
- **Milestone**: CAD parsing Development for Dataset
- **Default assignee**: me (the authenticated user)
- **Task Prefix**: [IMG-CROPPER] (for issue titles, e.g. "[IMG-CROPPER]: Add border detection for floor plans")

---

## Creating Tasks

When creating a new issue, always set:

| Field | Value |
|---|---|
| **Title** | Concise, imperative sentence (e.g. "Add border detection for floor plans") |
| **Description** | See format below |
| **Status** | `Todo` (unless already in progress) |
| **Assignee** | Me |
| **Priority** | `Urgent` / `High` / `Medium` / `Low` — match the actual urgency |
| **Labels** | One or more relevant labels (e.g. `feature`, `bug`, `refactor`) |

### Description format

```
## Goal
One sentence describing what needs to be done and why.

## Acceptance criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Notes
Any context, links, or constraints relevant to implementation.
```

---

## Updating Tasks

### Status transitions

Move the issue to the appropriate status as work progresses:

`Todo` → `In Progress` → `In Review` → `Done`

Mark `Cancelled` only when the work is explicitly abandoned.

### Adding comments

After completing meaningful work (e.g. finishing a subtask, resolving a blocker, or completing the issue), add a comment with:

```
## What was done
Short summary of the changes made.

## Implementation details
- Key decision or approach taken
- Files or modules affected (if relevant)

## Next steps (if not done)
- Remaining work
```

Keep comments factual and scannable — use bullet points, not prose paragraphs.

---

## Retrieving Tasks

When looking up issues:

- Search by issue ID when available (fastest)
- Filter by `assignee: me` + `project: CAD Parsing` for your own work
- Use `status` filters to scope to active work

---

## Rules

- Never leave `Assignee` or `Priority` blank when creating an issue.
- Always update the status before adding a completion comment — status first, then comment.
- Do not duplicate issues — search before creating.
- Titles must be self-explanatory without reading the description.
