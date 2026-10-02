---
name: reflect
description: Consolidates what a whole session taught into verified project notes (shared basic-memory notes and this agent's own memory), skips anything already in rules, CLAUDE.md or git history, and asks before writing. Use when the user asks to reflect on the session, consolidate its learnings, or update the project notes after substantial work.
when_to_use: |
  Trigger phrases: "reflect on the session", "consolidate the session's learnings", "what did we learn this session", "update the project notes from this session". After a conversation that produced architectural decisions, rule changes, discovered gaps, or new codebase patterns, or after a significant refactoring, audit, or rule-authoring session, offer to reflect; start only when the user agrees.

  Not this skill: "make a note of this", "remember this", "add this to the note" — single-fact captures handled by calling the basic-memory MCP directly. Also not "what did we learn from that file" or other mid-task questions.

  Do not create notes for: content already in .claude/rules/ or any CLAUDE.md, git history facts (use git log), or ephemeral task details that will not matter in a future session with no context.
---

# Reflecting Session Learnings

End-of-session knowledge consolidation: extract what is genuinely new, verify it against current state, and write it to the correct knowledge base without duplicating what already exists in rules or CLAUDE.md.

The knowledge base has two tiers: shared notes for all engineers, and internal memory for this user only. Follow the core pattern below so notes are useful, verifiable, and correctly classified. Knowledge that should be in rules, skills, agents or CLAUDE.md is not to be duplicated in memory: suggest the edit to those sources instead (Step 4).

---

## Two-Tier Knowledge Base

| Tier | Location | Audience | What belongs here |
|---|---|---|---|
| **Shared** | basic-memory MCP storage (project-configured) | All engineers on this repo | Architecture facts, topology, known gaps, decisions, codebase patterns |
| **Agent** | Agent-internal memory directory — use the path given in your built-in memory instructions; do not construct it yourself | This agent only | Feedback (corrections/confirmations), user preferences, branch context, external pointers |

**Before using MCP tools:** confirm `mcp__basic-memory__*` tools are in the deferred tool list and loaded — load them with `ToolSearch` if not. If they are unavailable (not in the tool list, or the server failed to connect), do not guess a storage path: tell the user the basic-memory server isn't reachable and ask for a directory, or whether to stop. Never call an MCP tool whose schema has not been loaded: it fails with `InputValidationError`, not a missing-tool error, which is easy to misread as a bad argument.

---

## Core Pattern

### Step 1 — Check Before Writing

- Read `MEMORY.md` (agent-internal index) to see what already exists.
- Spot-check relevant `.claude/rules/` files for content that would make a note redundant. Memory supplements rules (why, context, gaps), never repeats the rule itself.
- Search existing shared notes with `mcp__basic-memory__search_notes`. If the MCP tools are not available, see the note above.
- If a note already covers a topic, plan to update it with `mcp__basic-memory__edit_note` and show what changes, never a second note on the same topic. If something this session learned contradicts an existing note, list that note as "stale" in Step 4.

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
| Ephemeral detail ("today we fixed X") that will not matter in a future session with no context | **Skip** |

### Step 3 — Verify Before Recording

For every claim you are about to write:
- Named file path → confirm it exists (`Bash` / `Glob`)
- Named symbol or function → `Grep` for it
- Rule claim ("the rule says X") → read the current rule file
- "As of today" state → re-read the source of truth, not conversation context

Facts about the state of the code must be verified against the files. Decisions and rationale come from this conversation and cannot be: record them as "decided <date> in session, not verifiable from code", and mark them that way in the Step 4 table.

### Step 4 — Present Findings

Before writing anything, present a summary to the user:

- A table of what will be written: learning, destination tier, and a one-line description of the note
- Items that will be skipped and why (already in rules, ephemeral, etc.)
- Learnings that belong in a rule or CLAUDE.md, listed as "suggest rule edit". Do not edit those files without approval.
- Any uncertainty — flag it rather than silently deciding

Ask the user to confirm, adjust, or drop individual items before proceeding. Do not write a single note, and no `MEMORY.md` pointer, until the user has approved the plan. If the user drops everything, write nothing and do not retry.

### Step 5 — Write

For shared notes, decide the destination once, in this order:

1. If `mcp__basic-memory__write_note` is loaded, use it. The tool owns the storage location and permalinks — do not compute a path yourself.
2. Otherwise ask the user for the storage directory, once, and use `Write` for every note this session.

Before writing the first note, read one existing note in that store to match its format. Place broad knowledge in a general subdirectory; use existing domain subdirectories for specific content.

For internal memory: follow the built-in memory schema. After writing, add a one-line pointer to `MEMORY.md` (skip this if no `MEMORY.md` exists).

---

## Completion Checklist

- [ ] Checked existing notes and rules — nothing to be written is already documented
- [ ] Each learning classified to the correct tier
- [ ] All facts verified against current file state
- [ ] Findings and skips presented to user — user has approved the plan
- [ ] Shared notes written to the project's storage directory with correct frontmatter
- [ ] Internal memory files written with correct frontmatter and type
- [ ] `MEMORY.md` index updated for any new internal memory files
