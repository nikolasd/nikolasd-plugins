# Phase 4: the interview

Read this at the start of Phase 4. The interview builds shared understanding and shapes
the design. It is driven by the findings from Phase 3, not by a generic list.

## Contents

- 4.1 The opening question
- 4.2 One finding per question
- 4.3 Design questions
- 4.4 Recording answers
- 4.5 When the user cannot decide

## 4.1 The opening question

Ask one question, on its own, before anything else:

> "Who is this for, and what would tell you it worked? One or two sentences is plenty."

Use the answer to judge the value of each spec later (the "Valuable" criterion), and record
it in the header's `Audience and success signal` line in the user's words. On a re-run that
line is already there: show it and ask whether it still holds, instead of asking again. Do
not turn the opening into a questionnaire. End that message with one line offering the
pacing: findings can be taken one at a time (the default) or grouped by theme. Use the
user's pick for the rest of the interview.

## 4.2 One finding per question

Before the first finding question, print the F-nn table (id, category, a one-line finding,
the evidence) so the whole list is on the page and survives a summary of the conversation.
Then ask about the findings in order, one question per message. When the user chose
grouping, findings that share one decision go together in one message with sub-numbered
options (1a, 1b). For each question:

- State the finding in a sentence or two, with its evidence (`path/to/file.py:120`).
- Offer numbered options, always including "(other)".
- Lead with the option you recommend and say why in one sentence.

Example:

> "The PRD says the export endpoint already streams large histories, but
> `app/exports.py:5` builds the whole result in memory. How should the specs treat it?
>
> 1. Add a spec to make the export stream (recommended: the PRD's scaling goal depends on it)
> 2. Leave it as it is and record the scaling goal as a gap
> 3. (other)"

Skip a finding the PRD or an earlier answer already settles, and say you skipped it.

## 4.3 Design questions

After the findings, ask the design questions the specs need, again one at a time:

- **Boundaries:** where one spec should end and the next begin, when the scan found an
  unclear boundary.
- **Components:** which existing module or seam each capability should extend, when the
  code offers more than one.
- **Order:** whether any spec must land before another, so that `Depends on` is right.

Keep to what changes the specs. This is feature-level design, not a design review of the
whole repository.

## 4.4 Recording answers

Every answer that settles a choice becomes a decision `D-01`, `D-02` and so on in the
document. Say `Recorded as D-03: <the decision>` in your acknowledgement, so the user sees
what was captured. A decision records what was decided, `Decided by: the user`, and the
alternatives you showed. An answer that overrides the PRD is recorded as a decision and noted as an override; the PRD
is not edited.

## 4.5 When the user cannot decide

"I don't know", no answer, or "decide for me" all mean the same thing: record
`[GAP: <what is undecided>]` in the spec or specs it affects and list it under Open gaps.
Ask "who can decide this?" once and group the gap under the name the user gives; if the
user does not know, group it under "Unassigned". An owner always comes from the user, never
from you. Do not offer a default value. A recommendation on an option is allowed; a value filled into
the document is not.

If the PRD is so thin that there are few findings, say so, ask the opening question and
the design questions, and record every unanswered point as a gap. Do not pad the
interview.
