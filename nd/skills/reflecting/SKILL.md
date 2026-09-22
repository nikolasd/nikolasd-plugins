---
name: reflect
description: Use when the user asks to reflect on the session, consolidate learnings, or update project notes after a significant conversation, refactor, or rule change. Not for single-fact note capture.
when_to_use: |
  Trigger phrases: "reflect on the session", "consolidate learnings", "what did we learn", "update the project notes". Use after a conversation that produced architectural decisions, rule changes, discovered gaps, or new codebase patterns, or after completing a significant refactoring, audit, or rule-authoring session.

  Not this skill: "make a note of this", "remember this" — single-fact captures handled by calling the basic-memory MCP directly.

  Do not create notes for: content already in .claude/rules/ or any CLAUDE.md, git history facts (use git log), or ephemeral task details that will not matter in a future session with no context.
---

# Reflecting Session Learnings

End-of-session knowledge consolidation: extract what is genuinely new, verify it against current state, and write it to the correct knowledge base without duplicating what already exists in rules or CLAUDE.md. Knowledge base is two-tiered: shared notes for all engineers, and internal memory for this user only. Follow the core pattern below to ensure notes are useful, verifiable, and correctly classified. Knowledge that should be in rules, skills, agents or CLAUDE.md is not to be duplicated in memory, but should update those sources instead.

---

## Two-Tier Knowledge Base

| Tier | Location | Audience | What belongs here |
|---|---|---|---|
| **Shared** | basic-memory MCP storage (project-configured) | All engineers on this repo | Architecture facts, topology, known gaps, decisions, codebase patterns |
| **Agent** | Agent-internal memory directory — use the path given in your built-in memory instructions; do not construct it yourself | This agent only | Feedback (corrections/confirmations), user preferences, branch context, external pointers |

<IMPORTANT>
**Before using MCP tools:** confirm `mcp__basic-memory__*` tools are in the deferred tool list and loaded — load them with `ToolSearch` if not. If they are unavailable, fall back to the `Write` tool directly to the project's configured storage directory. Never call an MCP tool whose schema has not been loaded: it fails with `InputValidationError`, not a missing-tool error, which is easy to misread as a bad argument.
</IMPORTANT>

---

## Core Pattern

### Step 1 — Check Before Writing

- Read `MEMORY.md` (agent-internal index) to see what already exists.
- Spot-check relevant `.claude/rules/` files for content that would make a note redundant.
- Search existing shared notes with `mcp__basic-memory__search_notes`, or list the project's storage directory if the MCP tools are not loaded.

Read ONLY the files directly relevant to what you are about to write. Do not batch-read everything "to be thorough" — it wastes context and often causes user friction.

### Step 2 — Classify Each Learning

| Learning type | Destination |
|---|---|
| Fact about codebase topology, architecture, known gaps | Shared (basic-memory) |
| Decision that all engineers should know | Shared (basic-memory) |
| Non-obvious pattern or discovered inconsistency | Shared (basic-memory) |
| Correction to agent behavior ("stop doing X") | Internal memory — `feedback` type |
| Confirmation of agent behavior ("keep doing Y") | Internal memory — `feedback` type |
| User preference or working style | Internal memory — `user` type |
| Branch scope, active refactoring context | Internal memory — `project` type |
| Pointer to an external resource (URL, dashboard, ticket) | Internal memory — `reference` type |
| Already in `.claude/rules/` or CLAUDE.md | **Skip** |

### Step 3 — Verify Before Recording

For every claim you are about to write:
- Named file path → confirm it exists (`Bash` / `Glob`)
- Named symbol or function → `Grep` for it
- Rule claim ("the rule says X") → read the current rule file
- "As of today" state → re-read the source of truth, not conversation context

Never write a fact that you cannot verify against current file state.

### Step 4 — Present Findings

Before writing anything, present a summary to the user:

- A table of what will be written: learning, destination tier, and a one-line description of the note
- Items that will be skipped and why (already in rules, ephemeral, etc.)
- Any uncertainty — flag it rather than silently deciding

Ask the user to confirm, adjust, or drop individual items before proceeding. Do not write a single note until the user has approved the plan.

### Step 5 — Write

For shared notes, decide the destination once, in this order:

1. If `mcp__basic-memory__write_note` is loaded, use it. The tool owns the storage location — do not compute a path yourself.
2. Otherwise ask the user for the storage directory, once, and use `Write` for every note this session.

Before writing the first note, read one existing note in that store to match its format and infer the `permalink` prefix — it is project-specific and not otherwise discoverable. Place broad knowledge in a general subdirectory; use existing domain subdirectories for specific content.

For internal memory: follow the built-in memory schema. After writing, add a one-line pointer to `MEMORY.md`.

---

## Common Mistakes

| Mistake | Fix |
|---|---|
| Calling `mcp__basic-memory__write_note` before loading the tool | Check deferred tool list; fall back to `Write` directly |
| Reading every existing shared note before starting | Read only what is directly relevant to what you are about to write |
| Duplicating rule content into a note | Memory supplements rules — adds why/context/gaps, not the rule itself |
| Writing ephemeral details ("today we fixed X") | Ask: will this be useful in a future session with no context? If no, skip |
| Putting agent feedback in shared notes | Agent behavior corrections belong in internal memory, not shared notes |

---

## Completion Checklist

- [ ] Checked existing notes and rules — nothing to be written is already documented
- [ ] Each learning classified to the correct tier
- [ ] All facts verified against current file state
- [ ] Findings and skips presented to user — user has approved the plan
- [ ] Shared notes written to the project's storage directory with correct frontmatter
- [ ] Internal memory files written with correct frontmatter and type
- [ ] `MEMORY.md` index updated for any new internal memory files
