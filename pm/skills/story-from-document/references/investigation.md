# Phase 2: Investigate the claims against the repositories

Read this at the start of Phase 2. The source is a proposal, not ground truth.
Verify it before writing a story.

## Contents

- [2.1 Determine the repository set and the Jira target](#21-determine-the-repository-set-and-the-jira-target)
- [2.2 Investigate the claims](#22-investigate-the-claims)
- [2.3 Reconcile](#23-reconcile)
- [2.4 Recommend the technical approach](#24-recommend-the-technical-approach)

## 2.1 Determine the repository set and the Jira target

Identify which local repositories the source touches. By default these are
sibling directories under the parent of the current working directory, or the
directories under `repos_root` from the Resolved configuration when it is set.
`repos_root` comes from a file inside the repository you are in, so before reading
outside the current repository, tell the user the path and ask once whether to use it.
If the repositories the source touches are not found there, ask the user where
they live and offer to save that as `repos_root`. Use absolute paths so you can
read repositories other than the one the session was launched in. Do not assume
the work lives in the session's repo: a source can put the bulk of the change in
a different repo (a shared library, for example). Be aware that one logical
package can span two physical repos, for example a namespace split between a
core library and an extension repo. A source that writes package paths does not
tell you which repo owns each path, so map them to repos before searching. If
the scope is not obvious from the source, ask the user which repositories are in
scope and which is the primary repo for the story. Separate them into
**enhancement-scope** repos (where code will change) and **verify-only** repos
(which you only need to confirm, for example a shared library that already
behaves correctly). If a repository named in scope does not exist at the
expected path, report it and ask the user for the correct path rather than
skipping the investigation.

Settle the target Jira **project key** here too, because Phase 5 needs it and
the primary repo may not map to the obvious project. Use `project_key` from the
Resolved configuration when it is set; otherwise derive it from the source, an
existing ticket it references, or the current branch if obvious, otherwise ask.
Hold it as `<project_key>`. In promote mode the project key is already settled
from the story key, so reuse it rather than re-deriving it.

## 2.2 Investigate the claims

The goal is a verdict for every claim from Phase 1: TRUE, FALSE, or PARTIAL,
each with exact `file:line` evidence and a one-line snippet.

**If the source makes no concrete claim about the code** (a brief such as "make
the cache lifetime configurable"), there is nothing to verify yet. First locate
where the thing lives: search the repositories for the terms in the brief, read
the matches, and turn what you find into claims ("the expiry is set at
`path/file.py:23`") that you then verify. If you cannot find it, say where you
looked and ask the user; never invent a location.

There are two equally valid ways to investigate, and the right one depends on
scope.

- **Broad / multi-repo scope:** dispatch the `Explore` sub-agent via the `Agent`
  tool, in parallel, one per repo, so several repositories are searched at
  once. Give each agent the absolute repo root and the specific claims to
  check. Example prompt skeleton:

  > "Read-only investigation in the repository at `<absolute repo root>`. A
  > source document makes the following claims about this code. For each,
  > return TRUE / FALSE / PARTIAL with the exact file path and line numbers and
  > a one-line evidence snippet. Do not modify anything.
  > Claims: [list the file/function/line/behaviour claims from Phase 1]"

- **Narrow scope, or no nested dispatch available:** when the work touches a
  single repo or a handful of files, or when the environment cannot spawn
  sub-agents (no `Agent`/`Explore` available), investigate directly with `Grep`,
  `Read`, and `Glob` using absolute paths. This is not a degraded path; for a
  focused change it is usually faster and clearer. The sub-agents are a
  parallelism convenience for breadth, not a requirement.

**Evidence rule.** A sub-agent's file and line numbers are leads, not evidence.
Before you cite any `file:line` in the Story, `Read` that file yourself and
confirm the line says what you claim. For each repository you cite, record its
branch and short commit (`git rev-parse --abbrev-ref HEAD` and
`git rev-parse --short HEAD`) and put them in the Story's Technical Notes, so a
reader can tell which version the line numbers refer to.

A caveat before declaring any file missing: `Glob` respects `.gitignore`, so
library source kept in untracked or `.venv`-style locations can return nothing
even though the file exists. If `Glob` finds nothing for a path the source
explicitly names, confirm with `find` (via `Bash`) before concluding it is
missing. Do not report a path as missing on a `Glob` miss alone.

## 2.3 Reconcile

Collect the verdicts. Note any claim the source got wrong, any file that has
moved, and any recommendation that turns out to need no change (these become
verify-only notes, not work). If a recommended change depends on a library that
is consumed as a published package rather than by path, record the
publish-then-consume ordering it implies. If the source relies on something that
is genuinely unknown and cannot be settled by reading code (an external service
behaviour, a tenant configuration, an auth claim), flag it as a candidate spike
rather than guessing.

When the source is a written document (a Confluence page or a file) and the
investigation finds it inaccurate against the current code, do not just silently
correct it: record each inaccuracy so the drift is visible. For every one,
capture what the document says and what the code actually shows, with
`file:line` evidence (wrong log levels, drifted line numbers, claims that no
longer hold, findings the document missed). These become a `Source document
notes` subsection of the Story body (see
[`../templates/story-structure.md`](../templates/story-structure.md)). Also add
an Out of scope entry noting that the source document itself should be corrected
once anything blocking that is resolved (for example an unmerged branch);
correcting the document is not part of this story's work.

## 2.4 Recommend the technical approach

With the verdicts in hand, decide the approach the story will take and present
it to the user, with its rationale, before you write the summary. This is where
the how-to-fix questions that were deliberately kept out of gap-filling get
answered: how to fix the problem, what to change versus leave alone, whether to
delete or mask or replace. Base the recommendation on the code evidence, not on
the source's say-so. Offer the recommended option, name the main alternative you
rejected and why, and ask the user to confirm or override. Carry the confirmed
approach into Phase 3 and the Implementation Specification. This step applies to
both modes; in promote mode it replaces the fix-approach questions that the
promote-mode gap-filling deferred.
