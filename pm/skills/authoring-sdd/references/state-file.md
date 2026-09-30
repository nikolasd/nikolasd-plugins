# The state file

Read this when Phase 0 finds a state file, and again before writing it in Phase 5.

`docs/.solution-design.state.json` is the only record of this repo's
Confluence linkage; without it, the skill cannot tell which existing
Confluence page, if any, belongs to this repo's document. Phase 5 commits it
alongside the local markdown file, so every teammate's run targets the same
page. Its shape is fixed:

```json
{
  "confluence_page_id": "1234567890",
  "confluence_space": "DOCS",
  "confluence_parent_id": "1234567891",
  "confluence_version": 7,
  "local_path": "docs/solution-design.md",
  "last_run_version": "1.3",
  "last_run_date": "2026-08-07"
}
```

- `confluence_page_id` — the published page's ID. `null`, or the key
  omitted entirely, if this repo's document has never reached Confluence
  yet (for example, a local-only run because the Atlassian MCP was
  unreachable at publish time).
- `confluence_space` — the space key the page lives in. Set once at first
  publish; this skill never changes it afterward.
- `confluence_parent_id` — the parent page's ID, or `null` if the page has
  no parent.
- `confluence_version` — the page's version number (`version.number`) as of
  the last successful publish. Phase 0 compares it with the live page to tell
  whether Confluence was edited elsewhere. `null` if never published.
- `local_path` — the local file path resolved in Phase 0 (Zensical-aware,
  or the plain fallback), recorded so a later run can tell whether the
  Zensical configuration changed since the document was first created.
- `last_run_version` — the document's `Version` field, from its Document
  Control section, as of the run that last wrote this state file.
- `last_run_date` — `YYYY-MM-DD`, the date of that run.

Phase 0 reads `confluence_page_id` and `confluence_version` from this file for
the divergence check;
Phase 5 writes the whole file after every successful run. If the file
exists but fails to parse as JSON, or is missing an expected key, treat it
the same as "state file missing" (see Error handling) rather than guessing
at the absent fields. The one exception is `confluence_version`: if it is the
only key missing, keep the file and its page ID, and ask the divergence
question once (Phase 0) before recording the version.
