# Phase 4: the interview

Read this at the start of Phase 4. The interview builds shared understanding and shapes the design. It is driven by the findings from Phase 3, not by a generic list.

Assume the user is a tech lead or solution architect. They know the systems in general, but not every detail this PRD touches, and they need each question to settle one decision quickly. Use plain words, keep the background to what the decision needs, and always name the system and the part. Every message must make sense without the code open.

## Contents

- 4.1 The opening message
- 4.2 One finding per question
- 4.3 How to write a question
- 4.4 Design questions
- 4.5 Recording answers
- 4.6 When the user cannot decide

## 4.1 The opening message

Open with the part of the systems map from Phase 3 that this PRD touches, framed as what you found, for the user to correct: which systems take part, their role in this feature in one line each, and how one item moves through them. Use a small table or a short list, not file paths. Then list the defects you found (findings that need a fix, not a decision) in one or two lines each. A PRD claim the code shows to be FALSE is not a defect: what to do about it is the user's decision, so it waits for its turn among the findings.

End the message with one question, on its own:

> "Who is this for, and what would tell you it worked? One or two sentences is plenty."

If the PRD already states who it is for and how success is measured, quote that instead and ask the user to confirm or correct it.

Use the answer to judge the value of each spec later (the "Valuable" criterion), and record it in the header's `Audience and success signal` line in the user's words. On a re-run that line is already there: show it and ask whether it still holds, instead of asking again. Do not turn the opening into a questionnaire. After the question, add one line that states the pacing as a plan, not as a second question: "I'll take the findings one at a time unless you'd rather have them grouped by theme." When there are more than about ten findings, plan to group them by system or product area instead, and say which group comes first. If the user asks for the other pacing, use it for the rest of the interview.

## 4.2 One finding per question

Before the first finding question, print the F-nn table (id, category, the system it concerns, a one-line finding in plain words, the evidence) so the whole list is on the page and survives a summary of the conversation. Then ask about the findings in order, one question per message. When the user chose grouping, findings that share one decision go together in one message with sub-numbered options (1a, 1b), and each message says which group it belongs to and how many are left.

Skip a finding that the PRD, an earlier answer or a decision recorded elsewhere (Phase 3, 3.3) already settles, and a defect, which needs no decision. Say that you skipped it and why, naming the source of the decision.

When existing specs or tickets already cover an area (Phase 3, 3.3), ask once per area whether this document refers to them or writes the specs out in full, before asking about the area's other findings.

## 4.3 How to write a question

Each question has these parts, in this order:

1. **What it is about:** the system, and the part of it, by name. Never "the agent" or "the service" when there is more than one.
2. **Background:** what happens today and what the PRD asks for, in plain words and only as much as this decision needs. Say why the difference matters to the people who use the product.
3. **An example:** one concrete case that shows the difference, for instance a single alert, order or user going through the system.
4. **The question:** one sentence that the user can answer without reading code.
5. **Options:** numbered, always including "(other)". Lead with the option you recommend and say why in one sentence. Say what each option means for the user of the product, not only for the code.
6. **Evidence:** the `path/to/file.py:120` references, after the options, for readers who want to check. They support the explanation; they never replace it.

Keep each question short enough to read in under a minute. If the user says a question is unclear, rewrite it from the background up; do not repeat it with more detail.

Example:

> "**Order exports in the web account (the `web-app` repository).**
>
> Today, when a customer exports their order history, the server builds the whole file in
> memory before sending it. The PRD says customers with very long histories must still be
> able to export.
>
> For example, a customer with 200,000 orders clicks Export: the server may run out of
> memory and the download fails.
>
> Should the specs include changing the export so it sends the file in pieces?
>
> 1. Yes, add a spec for it (recommended: the PRD's promise to long-history customers
>    depends on it)
> 2. No, keep the export as it is and record the long-history case as an open gap
> 3. (other)
>
> Evidence: `app/exports.py:5`"

## 4.4 Design questions

After the findings, ask the design questions the specs need, one at a time and written the same way:

- **Boundaries:** where one spec should end and the next begin, when the scan found an unclear boundary.
- **Components:** which existing system or part of it each capability should extend, when the code offers more than one.
- **Order:** whether any spec must land before another, so that `Depends on` is right.

Keep to what changes the specs. This is feature-level design, not a design review of the whole repository.

## 4.5 Recording answers

Every answer that settles a choice becomes a decision `D-01`, `D-02` and so on in the document. Say `Recorded as D-03: <the decision>` in your acknowledgement, so the user sees what was captured. A decision records what was decided, `Decided by: the user`, and the alternatives you showed. An answer that overrides the PRD is recorded as a decision and noted as an override; the PRD is not edited.

A decision needs an answer from the user or a source document that states it (Phase 3, 3.3), named in `Decided by`. When the user answers ahead of time and asks not to be interviewed, each answer they gave is recorded; every other finding that needs a choice becomes a gap, even when their success signal seems to settle it. Put your recommendation for it in the review gate, where the user can turn it into a decision.

If an answer shows that a fact you relied on was wrong, say so, correct the finding, and check whether an earlier decision rested on it. Re-ask that decision before going on.

## 4.6 When the user cannot decide

"I don't know", no answer, or "decide for me" all mean the same thing: record `[GAP: <what is undecided>]` in the spec or specs it affects and list it under Open gaps.
Ask "who can decide this?" once and group the gap under the name the user gives; if the user does not know, group it under "Unassigned". An owner always comes from the user, never from you. Do not offer a default value. A recommendation on an option is allowed; a value filled into the document is not.

If the PRD is so thin that there are few findings, say so, ask the opening question and the design questions, and record every unanswered point as a gap. Do not pad the interview.
