---
name: orient
description: Orients from Basic Memory like bm-orient, and also runs the extra searches a project lists in basicMemory.orientQueries, so notes of your own types (ticket journals, runbooks, any type you configure) count as active work. Use when resuming work or asking where things stand in a project that uses Basic Memory; use it instead of bm-orient, since it covers everything bm-orient does.
when_to_use: |
  Trigger phrases: "where do things stand", "where did we leave off", "orient me", "catch me up on this repo", "resume the <ticket> work", "what's active right now".

  Not this skill: looking up one note or one fact ("what does the AGENTIC-601 journal say", "find the decision about X"): search Basic Memory directly. Not a checkpoint, handoff or reflection either: those write notes, this skill only reads.

  Needs the Basic Memory MCP tools; the Basic Memory plugin itself is optional. Without `orientQueries` in the settings it does exactly what bm-orient does.
---

# Orient, including your own note types

Basic Memory's own orientation (the `bm-orient` skill and the SessionStart brief) searches only four built-in note types: active `task`, open `decision`, `session` and `coding_session`. A project that tracks its work in notes of its own type, such as `type: ticket_journal`, gets an empty orientation. This skill runs the same orientation and adds the searches the project declares.

## Steps

1. **Resolve the settings.** Read the `basicMemory` block from the user-level `settings.json`, then the project's `.claude/settings.json` and `.claude/settings.local.json`; a later file overrides an earlier one per key. For the user-level file, append `settings.json` to the literal value of `CLAUDE_CONFIG_DIR` when that variable is present (do not trim it, expand `~`, or treat an empty value as unset); use `~/.claude/settings.json` only when it is absent. `orientQueries` is one key, so a later file's list replaces an earlier one's; the lists are not merged. Scope searches to `primaryProject` (pass it as `project_id` if it is an `external_id` UUID, else as `project`). With no config, use the default project and report that setup has not been run.
2. **Check the tools.** If no Basic Memory search tool (`search_notes`) is available, stop here. Say Basic Memory is unreachable, and list the searches you would have run: the built-in ones from step 3, then each `orientQueries` entry with its label, type, statuses and project.
3. **Run the built-in orientation** (bm-orient's searches) against the primary project with `search_notes`:
   - active tasks: `{"type": "task", "status": "active"}`
   - open decisions: `{"type": "decision", "status": "open"}`
   - recent sessions: `{"type": "session"}`, after `recallTimeframe`
   - when `sessionProfile` is `coding`: `{"type": "coding_session", "repository": <repository>}`, after `recallTimeframe`. Never run it without the `repository` filter; if `repository` is missing, report setup as incomplete.
   - each project in `secondaryProjects`, read-only: open decisions only.

   If bm-orient's SKILL.md is already loaded in this conversation and differs from this list, follow it. Merge and deduplicate the session hits, newest first.
4. **Run every entry in `basicMemory.orientQueries`** with `search_notes`:

   ```json
   "orientQueries": [
     { "label": "Open ticket journals", "type": "ticket_journal",
       "status": ["design", "in_progress"], "query": "journal" }
   ]
   ```

   - `metadata_filters` = `{"type": <type>}`. Add `"status": {"$in": <status>}` when `status` is a list, or `"status": <status>` when it is a single string.
   - `query` is optional and defaults to the entry's `type`.
   - Optional `after` (for example `"7d"`) becomes `after_date`.
   - Optional `project` replaces the primary project for that entry only. Search it read-only.
   - An entry that is not a JSON object with a `type` is a setup problem: report it and skip it, and run the rest.

   Always pass `query` text, here and in step 3: a `metadata_filters` search with an empty query can return nothing even when notes match. If a search comes back empty, retry it once with different text (the type name, the repository name, a ticket key). If the entry has a `status` and both tries are empty, search once more without the `status` filter. If that search finds notes, the type exists and none of them is in those statuses: report "none" under the label. Report a setup problem only when no note of that type exists at all, which usually means the type is misspelled.
5. **Read the hits that matter** before summarising. Read first the ones that name the current repository, branch, ticket or pull request, then the most recently updated. When a hit points to an index or hub note (for example a journal index), read that too.
6. **Present the orientation** in bm-orient's sections, adding one section per `orientQueries` entry under its `label`:
   - active work (built-in tasks and each configured section)
   - decisions that constrain the next move
   - recent checkpoint cursor
   - likely next action
   - missing setup or an ambiguous project mapping, including skipped entries and configured types with no notes at all

Cite the permalink of every note you rely on.
