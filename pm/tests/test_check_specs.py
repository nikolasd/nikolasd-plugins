#!/usr/bin/env python3
"""Deterministic tests for skills/specs-from-prd/scripts/check_specs.py.

No model, no network, no Jira.

    python3 pm/tests/test_check_specs.py -v
"""
import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent / "skills" / "specs-from-prd"
SCRIPT = SKILL / "scripts" / "check_specs.py"

_spec = importlib.util.spec_from_file_location("check_specs", SCRIPT)
cs = importlib.util.module_from_spec(_spec)
sys.modules["check_specs"] = cs
_spec.loader.exec_module(cs)


HEADER = [
    "- **Source PRD:** prd/exports.md",
    "- **Date:** 2026-10-02",
    "- **Repositories:** orders-service",
    "- **Audience and success signal:** Customers on the account page; fewer support tickets.",
]


def spec_block(sid="S-01", title="Export orders as CSV", status="Ready", story="",
               repo="orders-service", depends="none", criteria=None, invest=None,
               gaps=(), drop=(), drop_labels=(), approach="Reuse `app/exports.py:5`."):
    """One spec block in the document format. `drop` names field lines to omit,
    `drop_labels` names bold labels (User story, Scope, ...) to omit."""
    if criteria is None:
        criteria = ["A customer can download a CSV file of their orders."]
    if invest is None:
        invest = {name: ("Pass", "fine") for name in cs.INVEST}
    fields = [("Status", status), ("Story", story), ("Repo", repo), ("Depends on", depends)]
    out = [f"### {sid} {title}", ""]
    out += [f"- **{name}:** {value}".rstrip() for name, value in fields if name not in drop]
    labelled = {
        "User story": ["**User story:** As a customer, I want a CSV, so that I can keep my records.", ""],
        "Scope": ["**Scope:**", "", "- In: a CSV download.", "- Out: other formats.", ""],
        "Acceptance criteria": ["**Acceptance criteria:**", ""] + [f"{i}. {text}" for i, text in enumerate(criteria, start=1)] + [""],
        "Technical approach": [f"**Technical approach:** {approach}", ""],
    }
    out.append("")
    for label in ("User story", "Scope", "Acceptance criteria", "Technical approach"):
        if label not in drop_labels:
            out += labelled[label]
    out += ["**INVEST:**", "", "| Criterion | Result | Reason |", "|---|---|---|"]
    out += [f"| {name} | {verdict} | {reason} |" for name, (verdict, reason) in invest.items()]
    if "Gaps" not in drop_labels:
        out += ["", "**Gaps:**", ""] + ([f"- {gap}" for gap in gaps] or ["- None."])
    if "PRD trace" not in drop_labels:
        out += ["", "**PRD trace:** Requirement 1"]
    out.append("")
    return "\n".join(out)


def document(*blocks, specs_heading="## Specs", before="", crlf=False, header=None,
             repositories=None, open_gaps=None, components=None):
    joined = "\n".join(blocks)
    if repositories is None:
        names = []
        for match in re.finditer(r"^- \*\*Repo:\*\*[ \t]*(.*)$", joined, re.M):
            for part in re.split(r"[,;&]|\s+and\s+", match.group(1)):
                if part.strip() and part.strip() not in names:
                    names.append(part.strip())
        repositories = ", ".join(names) or "orders-service"
    if open_gaps is None:
        lines = []
        for match in re.finditer(r"^### (S-\d+) .*?(?=^### |\Z)", joined, re.M | re.S):
            count = len(re.findall(r"\[gap\b", match.group(0), re.I))
            if count:
                lines.append(f"- {match.group(1)}: {count} open")
        open_gaps = "\n".join(lines) or "None."
    if header is None:
        header = [line.replace("orders-service", repositories) if "**Repositories:**" in line else line
                  for line in HEADER]
    if components is None:
        components = ["| Export function | Stays the CSV source | `app/exports.py:5` |"]
    text = "\n".join([
        "# Exports Specs", "", *header, "",
        "## Open gaps", "", open_gaps, "",
        "## Feature design", "", "### Components touched", "",
        "| Component | What changes | Evidence |", "|---|---|---|", *components, "",
        "### Decisions", "",
        "#### D-01 Reuse the export function", "", "- **Decided by:** the user", "",
        before,
        specs_heading, "",
        joined,
        "## PRD findings", "", "None.", "",
        "## Change log", "", "None.", "",
    ])
    return text.replace("\n", "\r\n") if crlf else text


def codes(text):
    return [finding.code for finding in cs.check_text(text)[1]]


def run_cli(*args, stdin=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin,
                          capture_output=True, text=True)


class RuleTests(unittest.TestCase):
    def test_a_good_document_passes(self):
        text = document(spec_block("S-01"), spec_block("S-02", depends="S-01"))
        self.assertEqual(codes(text), [])

    def test_duplicate_spec_id(self):
        self.assertIn("DUP_ID", codes(document(spec_block("S-01"), spec_block("S-01"))))

    def test_duplicate_decision_id(self):
        text = document(spec_block(), before="#### D-01 Again\n")
        self.assertIn("DUP_ID", codes(text))

    def test_a_withdrawn_id_cannot_be_reused(self):
        text = document(spec_block("S-03", status="Withdrawn"), spec_block("S-03", title="New work"))
        self.assertIn("DUP_ID", codes(text))

    def test_heading_without_an_id(self):
        text = document(spec_block().replace("### S-01 Export", "### Export"))
        self.assertIn("BAD_HEADING", codes(text))

    def test_bad_status(self):
        self.assertIn("BAD_STATUS", codes(document(spec_block(status="Done"))))

    def test_missing_field_lines(self):
        for name in cs.FIELDS:
            with self.subTest(field=name):
                self.assertIn("MISSING_FIELD", codes(document(spec_block(drop=(name,)))))

    def test_empty_depends_on_is_an_error_but_none_is_not(self):
        self.assertIn("MISSING_FIELD", codes(document(spec_block(depends=""))))
        self.assertEqual(codes(document(spec_block(depends="none"))), [])

    def test_a_story_may_be_blank_or_filled(self):
        self.assertEqual(codes(document(spec_block(story=""))), [])
        self.assertEqual(codes(document(spec_block(story="DEMO-12"))), [])

    def test_unresolved_and_malformed_dependencies(self):
        self.assertIn("DEP_UNRESOLVED", codes(document(spec_block(depends="S-09"))))
        self.assertIn("DEP_UNRESOLVED", codes(document(spec_block(depends="the schema work"))))

    def test_dependency_ids_are_compared_as_written(self):
        text = document(spec_block("S-01"), spec_block("S-02", depends="S-1"))
        self.assertIn("DEP_UNRESOLVED", codes(text))

    def test_two_spec_cycle(self):
        text = document(spec_block("S-01", depends="S-02"), spec_block("S-02", depends="S-01"))
        finding = [f for f in cs.check_text(text)[1] if f.code == "DEP_CYCLE"]
        self.assertEqual(len(finding), 1)
        self.assertIn("S-01 -> S-02 -> S-01", finding[0].message)

    def test_a_spec_cannot_depend_on_itself(self):
        self.assertIn("DEP_CYCLE", codes(document(spec_block("S-01", depends="S-01"))))

    def test_live_spec_depending_on_a_withdrawn_spec(self):
        text = document(spec_block("S-01", status="Withdrawn", criteria=[], invest={}),
                        spec_block("S-02", depends="S-01"))
        self.assertIn("DEP_ON_WITHDRAWN", codes(text))

    def test_withdrawn_spec_is_exempt_from_content_checks(self):
        text = document(spec_block("S-01"), spec_block("S-02", status="Withdrawn", repo="",
                                                       criteria=[], invest={}, depends="S-01"))
        self.assertEqual(codes(text), [])

    def test_no_acceptance_criteria(self):
        self.assertIn("NO_AC", codes(document(spec_block(criteria=[]))))

    def test_repo_must_be_exactly_one(self):
        self.assertIn("REPO_COUNT", codes(document(spec_block(repo="orders-service, billing"))))
        self.assertIn("REPO_COUNT", codes(document(spec_block(repo="orders and billing"))))
        self.assertIn("REPO_COUNT", codes(document(spec_block(repo=""))))
        self.assertEqual(codes(document(spec_block(repo="acme/orders-service"))), [])

    def test_missing_invest_rows(self):
        invest = {name: ("Pass", "fine") for name in cs.INVEST if name != "Small"}
        self.assertIn("INVEST_MISSING", codes(document(spec_block(invest=invest))))

    def test_invest_result_must_be_pass_or_fail(self):
        invest = {name: ("Pass", "fine") for name in cs.INVEST}
        invest["Valuable"] = ("Maybe", "unsure")
        self.assertIn("INVEST_RESULT", codes(document(spec_block(invest=invest))))

    def test_a_failing_invest_row_is_an_error(self):
        invest = {name: ("Pass", "fine") for name in cs.INVEST}
        invest["Small"] = ("Fail", "spans two repos")
        self.assertIn("INVEST_FAIL", codes(document(spec_block(invest=invest))))

    def test_ready_with_a_gap_is_a_mismatch(self):
        text = document(spec_block(status="Ready", gaps=["[GAP: the export format]"]))
        self.assertIn("STATUS_GAP_MISMATCH", codes(text))

    def test_needs_decision_without_a_gap_is_a_mismatch(self):
        self.assertIn("STATUS_GAP_MISMATCH", codes(document(spec_block(status="Needs decision"))))

    def test_gap_markers_are_matched_case_insensitively(self):
        for marker in ("[Gap: export format]", "[gap: export format]", "[GAP export format]"):
            with self.subTest(marker=marker):
                text = document(spec_block(status="Ready", gaps=[marker]))
                self.assertIn("STATUS_GAP_MISMATCH", codes(text))
        text = document(spec_block(status="Needs decision", gaps=["[Gap: export format]"]))
        self.assertEqual(codes(text), [])

    def test_none_or_a_bare_gap_is_not_an_acceptance_criterion(self):
        for text in ("None.", "none", "[GAP: no criteria yet]"):
            with self.subTest(text=text):
                self.assertIn("NO_AC", codes(document(spec_block(criteria=[text]))))

    def test_a_criterion_that_ends_in_a_gap_still_counts(self):
        criteria = ["The export has a header row. [GAP: the column names]"]
        text = document(spec_block(status="Needs decision", criteria=criteria,
                                   gaps=["[GAP: the column names]"]))
        self.assertEqual(codes(text), [])

    def test_a_gap_in_the_spec_heading_counts(self):
        block = spec_block(status="Ready").replace(
            "### S-01 Export orders as CSV", "### S-01 Export orders as CSV [GAP: final title]")
        self.assertIn("STATUS_GAP_MISMATCH", codes(document(block)))

    def test_needs_decision_with_a_gap_passes(self):
        text = document(spec_block(status="Needs decision", gaps=["[GAP: the export format]"]))
        self.assertEqual(codes(text), [])


class ShapeTests(unittest.TestCase):
    def test_headings_and_ids_inside_a_fence_are_ignored(self):
        fenced = "```mermaid\n### S-99 not a spec\n## Specs\n#### D-01 not a decision\n```\n"
        text = document(spec_block("S-01"), before=fenced)
        specs, findings = cs.check_text(text)
        self.assertEqual([spec.id for spec in specs], ["S-01"])
        self.assertEqual(findings, [])

    def test_an_unclosed_fence_is_reported_as_such(self):
        text = document(spec_block(), before="```mermaid\nflowchart LR\n")
        self.assertIn("UNCLOSED_FENCE", codes(text))

    def test_a_crlf_document_passes(self):
        text = document(spec_block("S-01"), spec_block("S-02", depends="S-01"), crlf=True)
        self.assertEqual(codes(text), [])

    def test_a_document_without_a_specs_section(self):
        self.assertEqual(codes(document(spec_block(), specs_heading="## Stories")), ["NO_SPECS"])

    def test_an_empty_specs_section(self):
        self.assertEqual(codes(document()), ["NO_SPECS"])

    def test_the_specs_section_stops_at_the_next_h2(self):
        text = document(spec_block("S-01")) + "\n### S-02 Looks like a spec but sits under the change log\n"
        specs, findings = cs.check_text(text)
        self.assertEqual([spec.id for spec in specs], ["S-01"])
        self.assertIn("SPEC_OUTSIDE_SECTION", [f.code for f in findings])

    def test_a_second_specs_section_is_an_error(self):
        text = document(spec_block("S-01")) + "\n## Specs\n\n" + spec_block("S-02")
        self.assertIn("DUP_SECTION", codes(text))

    def test_a_second_specs_section_right_after_the_first_is_an_error(self):
        text = document(spec_block("S-01")).replace(
            "## PRD findings", "## Specs\n\n" + spec_block("S-02") + "\n## PRD findings", 1)
        self.assertIn("DUP_SECTION", codes(text))

    def test_a_repeated_field_line_is_an_error(self):
        block = spec_block().replace("- **Status:** Ready", "- **Status:** Ready\n- **Status:** Withdrawn")
        self.assertIn("DUP_FIELD", codes(document(block)))

    def test_a_repository_name_may_contain_the_word_and(self):
        self.assertEqual(codes(document(spec_block(repo="search-and-indexing"))), [])


class CliTests(unittest.TestCase):
    def test_pass_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "exports.md"
            path.write_text(document(spec_block()), encoding="utf-8")
            result = run_cli(str(path))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("RESULT: PASS", result.stdout)
        self.assertIn("S-01: Ready, 1 criteria, 0 gaps, depends on none", result.stdout)

    def test_fail_exits_one_and_names_the_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "exports.md"
            path.write_text(document(spec_block(criteria=[])), encoding="utf-8")
            result = run_cli(str(path))
        self.assertEqual(result.returncode, 1)
        self.assertIn("NO_AC", result.stdout)
        self.assertIn("RESULT: FAIL", result.stdout)

    def test_unreadable_file_exits_two(self):
        result = run_cli("/nonexistent/specs.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot read", result.stderr)

    def test_reads_stdin(self):
        result = run_cli("-", stdin=document(spec_block()))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_a_byte_order_mark_is_tolerated(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "exports.md"
            path.write_bytes(b"\xef\xbb\xbf" + document(spec_block()).encode("utf-8"))
            result = run_cli(str(path))
        self.assertEqual(result.returncode, 0, result.stdout)


class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.template = (SKILL / "templates" / "specs-document.md").read_text(encoding="utf-8")

    def test_template_has_the_specs_heading_and_every_field_line(self):
        self.assertIn("\n## Specs\n", self.template)
        for name in cs.FIELDS:
            self.assertIn(f"- **{name}:**", self.template)

    def test_template_has_every_invest_row(self):
        for name in cs.INVEST:
            self.assertIn(f"| {name} | Pass |", self.template)

    def test_template_header_has_the_audience_field_and_no_document_status(self):
        self.assertIn("- **Audience and success signal:**", self.template)
        self.assertNotIn("Document status", self.template)

    def test_template_defines_repo_as_the_root_folder_name(self):
        self.assertIn("root folder name", self.template)

    def test_the_template_spec_block_parses(self):
        specs, _ = cs.check_text(self.template)
        self.assertEqual([spec.id for spec in specs], ["S-01"])
        self.assertEqual(specs[0].criteria, 1)
        self.assertEqual(sorted(specs[0].invest), sorted(cs.INVEST))


class SkillFileTests(unittest.TestCase):
    def setUp(self):
        self.skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    def test_skill_md_is_under_500_lines(self):
        self.assertLess(len(self.skill_md.splitlines()), 500)

    def test_no_em_dash_in_any_skill_file(self):
        for path in SKILL.rglob("*"):
            if path.is_file() and path.suffix in (".md", ".py"):
                with self.subTest(file=str(path.relative_to(SKILL))):
                    self.assertNotIn("—", path.read_text(encoding="utf-8"))

    def test_every_reference_named_in_skill_md_exists(self):
        for name in ("analysis", "interview", "invest", "rerun"):
            with self.subTest(reference=name):
                self.assertIn(f"references/{name}.md", self.skill_md)
                self.assertTrue((SKILL / "references" / f"{name}.md").is_file())

    def test_config_injection_and_tool_rules_ci_checks(self):
        inject = "!`sh ${CLAUDE_PLUGIN_ROOT}/scripts/config.sh '${user_config.site}'`"
        self.assertIn(inject, self.skill_md.splitlines())
        self.assertIn('"Bash(sh ${CLAUDE_PLUGIN_ROOT}/scripts/config.sh *)"', self.skill_md)
        self.assertNotIn("points_scale", self.skill_md)

    def test_no_jira_tool_is_allowed(self):
        frontmatter = self.skill_md.split("---")[1]
        self.assertNotIn("mcp__atlassian__createJiraIssue", frontmatter)
        self.assertNotIn("mcp__atlassian__editJiraIssue", frontmatter)
        self.assertNotIn("mcp__atlassian__addCommentToJiraIssue", frontmatter)

    def test_the_analysis_reference_names_a_read_only_agent_type(self):
        text = (SKILL / "references" / "analysis.md").read_text(encoding="utf-8")
        self.assertIn("`Explore`", text)

    def test_spec_source_asks_for_a_path_when_the_repo_is_not_the_current_one(self):
        path = HERE.parent / "skills" / "story-from-document" / "references" / "spec-source.md"
        self.assertIn("ask the user for its path", path.read_text(encoding="utf-8"))

    def test_readmes_do_not_count_six_skills(self):
        for path in (HERE.parent / "README.md", HERE.parent / "evals" / "README.md"):
            with self.subTest(file=path.name):
                self.assertNotIn("All six skills", path.read_text(encoding="utf-8"))

    def test_the_checker_and_the_template_are_named_in_skill_md(self):
        self.assertIn("scripts/check_specs.py", self.skill_md)
        self.assertIn("templates/specs-document.md", self.skill_md)
        for status in cs.STATUSES:
            self.assertIn(status, self.skill_md)
        for name in cs.INVEST:
            self.assertIn(name, (SKILL / "references" / "invest.md").read_text(encoding="utf-8"))


def allowed_tools(skill_md_text):
    """The entries of the one-line `allowed-tools: [...]` frontmatter list."""
    line = next(l for l in skill_md_text.split("---")[1].splitlines() if l.startswith("allowed-tools:"))
    body = line[line.index("[") + 1:line.rindex("]")]
    entries, current, quote = [], "", None
    for char in body:
        if quote:
            if char == quote:
                quote = None
            else:
                current += char
        elif char in "\"'":
            quote = char
        elif char == ",":
            entries.append(current.strip())
            current = ""
        else:
            current += char
    entries.append(current.strip())
    return [e for e in entries if e]


class GrantTests(unittest.TestCase):
    """Only read-only tools are pre-approved. Anything that writes must ask the user.

    allowed-tools pre-approves without restricting, and the grant ends at the user's next
    message, so a write grant would only ever cover the first turn, the one in which
    untrusted text is read. The config rule is the one exception that must stay: an injected
    command that is not pre-approved aborts the whole skill.
    """

    SKILLS = ("specs-from-prd", "story-from-document")
    WRITERS = ("Write", "Edit", "NotebookEdit", "Bash")
    JIRA_WRITES = ("createJiraIssue", "editJiraIssue", "createIssueLink", "addCommentToJiraIssue",
                   "createConfluencePage", "updateConfluencePage", "createConfluenceFooterComment",
                   "createConfluenceInlineComment")
    ALLOWED_BASH = ("Bash(sh ${CLAUDE_PLUGIN_ROOT}/scripts/config.sh *)",
                    "Bash(git rev-parse *)",
                    "Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/specs-from-prd/scripts/check_specs.py *)")

    def entries(self, skill):
        path = HERE.parent / "skills" / skill / "SKILL.md"
        return allowed_tools(path.read_text(encoding="utf-8"))

    def test_no_write_capable_tool_is_pre_approved(self):
        for skill in self.SKILLS:
            for entry in self.entries(skill):
                with self.subTest(skill=skill, entry=entry):
                    self.assertNotIn(entry, self.WRITERS)
                    self.assertFalse(entry.startswith(("Write(", "Edit(", "NotebookEdit(")), entry)
                    self.assertFalse(any(entry.endswith("__" + name) for name in self.JIRA_WRITES), entry)

    def test_the_only_bash_rules_are_the_known_read_only_ones(self):
        for skill in self.SKILLS:
            for entry in self.entries(skill):
                if entry.startswith("Bash("):
                    with self.subTest(skill=skill, entry=entry):
                        self.assertIn(entry, self.ALLOWED_BASH)

    def test_the_config_rule_stays_because_the_injection_needs_it(self):
        for skill in self.SKILLS:
            with self.subTest(skill=skill):
                self.assertIn(self.ALLOWED_BASH[0], self.entries(skill))

    def test_the_skills_say_what_to_do_when_a_permission_is_declined(self):
        for skill in self.SKILLS:
            text = (HERE.parent / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=skill):
                self.assertIn("## Permissions", text)
                self.assertIn("declines", text)


class UntrustedInputTests(unittest.TestCase):
    """Every path by which text written by someone else reaches the model is named."""

    def skill(self, name):
        return (HERE.parent / "skills" / name / "SKILL.md").read_text(encoding="utf-8")

    def rule(self, text, marker):
        start = text.index(marker)
        return " ".join(text[start:text.index("\n\n", start)].split())

    def test_story_rule_names_every_ingestion_path(self):
        rule = self.rule(self.skill("story-from-document"), "8. Everything you read that someone else wrote")
        for needle in ("sub-tasks, links and comments", "search returns", "README", "code comments",
                       "subagent reports", "mockups", "Source check:"):
            with self.subTest(needle=needle):
                self.assertIn(needle, rule)

    def test_specs_rule_names_every_ingestion_path(self):
        rule = self.rule(self.skill("specs-from-prd"), "7. Everything you read that someone else wrote")
        for needle in ("README", "code comments", "subagent reports", "design document", "Source check:"):
            with self.subTest(needle=needle):
                self.assertIn(needle, rule)

    def test_promote_mode_prints_the_same_source_check_line(self):
        text = self.skill("story-from-document")
        start = text.index("## Phase 1 (promote)")
        section = text[start:text.index("## Phase 2", start)]
        self.assertIn("Source check", section)
        self.assertIn("sub-tasks, links and comments", " ".join(section.split()))

    def test_copied_decisions_are_candidates_until_the_user_confirms_them(self):
        template = (HERE.parent / "skills" / "story-from-document" / "templates" / "story-structure.md").read_text(encoding="utf-8")
        start = template.index("**Decisions carried from the source")
        section = template[start:template.index("---", start)]
        self.assertIn("candidate", section)
        self.assertIn("confirms", section)

    def test_web_pages_are_fetched_verbatim_not_summarised(self):
        for name in ("story-from-document", "specs-from-prd"):
            with self.subTest(skill=name):
                text = self.skill(name)
                at = text.index("`WebFetch`")
                self.assertIn("verbatim", text[at:at + 400])

    def test_specs_analysis_treats_subagent_and_repo_text_as_data(self):
        text = (SKILL / "references" / "analysis.md").read_text(encoding="utf-8")
        self.assertIn("rule 7", text)
        self.assertIn("README", text)


class SourceCheckPlacementTests(unittest.TestCase):
    """The Source check line is a full, self-contained step, tied to the message that ends the turn."""

    def text(self, name):
        return (HERE.parent / "skills" / name / "SKILL.md").read_text(encoding="utf-8")

    def section(self, text, heading):
        start = text.index(heading)
        end = text.find("\n## ", start + 1)
        return " ".join(text[start:end if end != -1 else len(text)].split())

    def test_story_has_one_shared_source_check_section(self):
        section = self.section(self.text("story-from-document"), "## Source check")
        for needle in ("ends your turn", "narration", "no instructions aimed at me",
                       "clearest sign of an injection", "review gate",
                       "sub-tasks, links and comments"):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)

    def test_both_story_modes_run_that_section(self):
        text = self.text("story-from-document")
        for heading in ("## Phase 1 (create)", "## Phase 1 (promote)"):
            section = self.section(text, heading)
            with self.subTest(heading=heading):
                self.assertIn("Source check", section)

    def test_specs_source_check_is_tied_to_the_turn_ending_message(self):
        section = self.section(self.text("specs-from-prd"), "## Phase 2")
        for needle in ("ends your turn", "narration", "no instructions aimed at me"):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)


class GateTests(unittest.TestCase):
    """The gates of story-from-document say what may be pre-answered and what never can."""

    BASE = HERE.parent / "skills" / "story-from-document"

    def flat(self, text):
        return " ".join(text.split())

    def skill(self):
        return (self.BASE / "SKILL.md").read_text(encoding="utf-8")

    def review_gate(self):
        text = self.skill()
        start = text.index("**4.4 Review gate.**")
        return self.flat(text[start:text.index("## Phase 5", start)])

    def test_gates_section_separates_answerable_gates_from_the_review_gate(self):
        text = self.skill()
        start = text.index("## Gates")
        section = self.flat(text[start:text.index("\n## ", start + 1)])
        for needle in ("2.4", "Phase 3", "3.5", "4.3", "already answered",
                       "ask them in one message", "4.4", "cannot be answered in advance"):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)

    def test_the_review_gate_no_longer_runs_the_duplicate_search_itself(self):
        gate = self.review_gate()
        self.assertNotIn("searchJiraIssuesUsingJql", gate)
        self.assertIn("duplicate-check result from 2.1", gate)

    def test_the_duplicate_check_runs_early_and_skips_cleanly(self):
        text = self.flat((self.BASE / "references" / "investigation.md").read_text(encoding="utf-8"))
        start = text.index("Duplicate check (create mode)")
        section = text[start:start + 1600]
        for needle in ("searchJiraIssuesUsingJql", "--dry-run", "Jira tools are unavailable",
                       "one line", "5.0"):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)

    def test_open_gaps_are_asked_once_and_may_stay_open(self):
        self.assertIn("once", self.review_gate())
        self.assertIn("leaves open", self.review_gate())
        template = self.flat((self.BASE / "templates" / "story-structure.md").read_text(encoding="utf-8"))
        self.assertIn("leaves open", template)
        self.assertNotIn("Gaps must be resolved by the user during the Phase 4 review", template)

    def test_an_amended_draft_needs_a_fresh_confirmation_and_a_decline_is_handled(self):
        gate = self.review_gate()
        self.assertIn("fresh confirmation", gate)
        self.assertIn("declines", gate)


class ContractTests(unittest.TestCase):
    """What the consumer (story-from-document) relies on is checked, not just the structure."""

    def codes_in(self, text, root=None):
        return [finding.code for finding in cs.check_text(text, root=root)[1]]

    def test_every_required_label_is_checked(self):
        for label in cs.REQUIRED_LABELS:
            with self.subTest(label=label):
                self.assertIn("MISSING_LABEL", codes(document(spec_block(drop_labels=(label,)))))

    def test_a_withdrawn_spec_needs_no_labels(self):
        withdrawn = spec_block("S-02", status="Withdrawn", criteria=[], invest={},
                               drop_labels=cs.REQUIRED_LABELS)
        self.assertEqual(codes(document(spec_block("S-01"), withdrawn)), [])

    def test_the_technical_approach_must_cite_a_path_and_line(self):
        self.assertIn("NO_EVIDENCE", codes(document(spec_block(approach="Reuse the export function."))))

    def test_the_components_table_must_cite_a_path_and_line(self):
        text = document(spec_block(), components=["| Export function | Stays | none |"])
        self.assertIn("NO_EVIDENCE", codes(text))

    def test_cited_evidence_must_exist_when_a_root_is_given(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app").mkdir()
            (root / "app" / "exports.py").write_text("a\nb\nc\n")
            good = document(spec_block(approach="Uses `app/exports.py:2-3`."),
                            components=["| X | y | `app/exports.py:1` |"])
            self.assertEqual(self.codes_in(good, root), [])
            for cite in ("`app/exports.py:9`", "`app/exports.py:2-9`", "`app/missing.py:1`",
                         "`../outside.py:1`", "`/etc/passwd:1`"):
                with self.subTest(cite=cite):
                    text = document(spec_block(approach=f"Uses {cite}."),
                                    components=["| X | y | `app/exports.py:1` |"])
                    self.assertIn("DANGLING_EVIDENCE", self.codes_in(text, root))

    def test_without_a_root_evidence_is_not_looked_up(self):
        self.assertEqual(codes(document(spec_block(approach="Uses `app/nowhere.py:99`."))), [])

    def test_open_gaps_must_list_every_spec_that_has_a_gap(self):
        block = spec_block(status="Needs decision", gaps=["[GAP: format]"])
        self.assertIn("GAPS_SUMMARY_MISMATCH", codes(document(block, open_gaps="None.")))

    def test_open_gaps_may_not_name_a_spec_without_a_gap_or_an_unknown_spec(self):
        self.assertIn("GAPS_SUMMARY_MISMATCH", codes(document(spec_block("S-01"), open_gaps="- S-01: something")))
        self.assertIn("GAPS_SUMMARY_MISMATCH", codes(document(spec_block("S-01"), open_gaps="- S-09: something")))

    def test_open_gaps_may_hold_entries_with_no_spec_id(self):
        text = document(spec_block(), open_gaps="- Document level: [GAP: the success measure]")
        self.assertEqual(codes(text), [])

    def test_an_em_dash_is_an_error(self):
        text = document(spec_block(criteria=["A customer can export \u2014 as CSV."]))
        self.assertIn("EM_DASH", codes(text))

    def test_header_fields_are_required(self):
        for name in ("Source PRD", "Date", "Repositories", "Audience and success signal"):
            with self.subTest(field=name):
                header = [line for line in HEADER if f"**{name}:**" not in line]
                self.assertIn("MISSING_HEADER", codes(document(spec_block(), header=header)))

    def test_an_empty_header_value_is_missing(self):
        header = [line if "Audience" not in line else "- **Audience and success signal:**" for line in HEADER]
        self.assertIn("MISSING_HEADER", codes(document(spec_block(), header=header)))

    def test_the_date_must_be_iso(self):
        header = [line if "**Date:**" not in line else "- **Date:** Oct 2" for line in HEADER]
        self.assertIn("BAD_DATE", codes(document(spec_block(), header=header)))

    def test_a_spec_repo_must_be_listed_in_the_header(self):
        text = document(spec_block(repo="orders-service"), repositories="billing")
        self.assertIn("REPO_NOT_LISTED", codes(text))

    def test_cli_root_option_checks_evidence_on_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app").mkdir()
            (root / "app" / "exports.py").write_text("a\nb\nc\n")
            doc = root / "specs.md"
            doc.write_text(document(spec_block(approach="Uses `app/exports.py:9`.")), encoding="utf-8")
            result = run_cli("--root", str(root), str(doc))
        self.assertEqual(result.returncode, 1)
        self.assertIn("DANGLING_EVIDENCE", result.stdout)


class ContractProseTests(unittest.TestCase):
    """The prose on both sides of the document says what the checker enforces."""

    SPECS = HERE.parent / "skills" / "specs-from-prd"
    STORY = HERE.parent / "skills" / "story-from-document"

    def flat(self, path):
        return " ".join(path.read_text(encoding="utf-8").split())

    def test_phase_5_states_the_exact_formats_the_checker_enforces(self):
        text = self.flat(self.SPECS / "SKILL.md")
        start = text.index("## Phase 5")
        section = text[start:text.index("## Phase 6", start)]
        for needle in ("no colon", "exactly `Pass` or `Fail`", "root folder name",
                       "session context", "`path:line`", "Audience and success signal"):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)

    def test_the_checker_is_run_with_a_root_for_the_current_repository(self):
        text = (self.SPECS / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("check_specs.py --root . -", text)
        self.assertIn("check_specs.py --root . <specs path>", text)

    def test_invest_no_longer_contradicts_the_checker(self):
        text = self.flat(self.SPECS / "references" / "invest.md")
        self.assertNotIn("only if the gap is not recorded", text)
        self.assertIn("gap recorded", text)

    def test_the_audience_answer_is_recorded_and_kept(self):
        interview = self.flat(self.SPECS / "references" / "interview.md")
        rerun = self.flat(self.SPECS / "references" / "rerun.md")
        self.assertIn("Audience and success signal", interview)
        self.assertIn("still holds", interview)
        self.assertIn("Audience and success signal", rerun)

    def test_spec_source_matches_the_producer_side(self):
        text = self.flat(self.STORY / "references" / "spec-source.md")
        for needle in ("git rev-parse --show-toplevel", "root folder name", "under Scope",
                       "inwardIssue", "Audience and success signal", "check_specs.py",
                       "does not pass the specs-from-prd format", "technical gaps", "2.4",
                       "stays part of the claim set"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)


class FixtureTests(unittest.TestCase):
    """The shared eval fixture writes a document the checker accepts, with evidence on disk."""

    LIB = HERE.parent / "evals" / "_lib" / "exports-repo.sh"

    def run_fixture(self, story_key=""):
        with tempfile.TemporaryDirectory() as tmp:
            script = f'. "{self.LIB}" && build_exports_repo && write_specs_doc {story_key} && ' \
                     f'python3 "{SCRIPT}" --root . docs/specs/exports.md'
            return subprocess.run(["bash", "-c", script], cwd=tmp, capture_output=True, text=True)

    def test_the_fixture_document_passes_with_evidence_checked_on_disk(self):
        result = self.run_fixture()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("RESULT: PASS", result.stdout)

    def test_the_locked_variant_also_passes(self):
        result = self.run_fixture("DEMO-12")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class WorkflowTests(unittest.TestCase):
    """specs-from-prd behaves the same way from run to run on the points the review found."""

    SPECS = HERE.parent / "skills" / "specs-from-prd"

    def flat(self, path):
        return " ".join(path.read_text(encoding="utf-8").split())

    def phase(self, number_and_title, next_title):
        text = self.flat(self.SPECS / "SKILL.md")
        start = text.index(number_and_title)
        return text[start:text.index(next_title, start)]

    def test_the_default_file_name_is_deterministic_and_an_earlier_document_is_found(self):
        section = self.phase("## Phase 1: Setup", "## Phase 2")
        for needle in ("PRD file's base name", "page title", "`Source PRD`", "docs/specs/",
                       "offer it as the re-run target"):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)
        self.assertNotIn("feature name or the PRD file", section)

    def test_the_repository_paths_are_asked_in_phase_1_not_during_analysis(self):
        section = self.phase("## Phase 1: Setup", "## Phase 2")
        self.assertIn("path of each other repository", section)
        analysis = self.flat(self.SPECS / "references" / "analysis.md")
        self.assertNotIn("ask the user for the path", analysis)
        self.assertIn("settled in Phase 1", analysis)

    def test_a_locked_spec_may_have_its_gap_line_and_status_amended(self):
        rerun = self.flat(self.SPECS / "references" / "rerun.md")
        self.assertIn("only the gap line and the status", rerun)

    def test_splits_and_merges_are_approved_at_the_gate_unless_they_touch_a_lock(self):
        check = self.phase("## Phase 6: Check", "## Phase 7")
        self.assertNotIn("get their approval before any split or merge", check)
        gate = self.phase("## Phase 7: Review gate", "## Phase 8")
        self.assertIn("splits and merges", gate)
        for text in (check, self.flat(self.SPECS / "references" / "invest.md")):
            self.assertIn("locked spec or a recorded decision", text)

    def test_waits_after_an_amendment_or_a_dry_run_are_explicit(self):
        gate = self.phase("## Phase 7: Review gate", "## Phase 8")
        self.assertIn("fresh confirmation", gate)
        dry_run = self.phase("## Dry-run boundary", "## Content rules")
        self.assertIn("already saw", dry_run)


class FingerprintTests(unittest.TestCase):
    """The checker prints a short fingerprint so the written file can be compared to the draft."""

    def fingerprint(self, result):
        lines = [l for l in result.stdout.splitlines() if l.startswith("fingerprint: ")]
        self.assertEqual(len(lines), 1, result.stdout)
        return lines[0]

    def test_stdin_and_file_give_the_same_fingerprint(self):
        text = document(spec_block())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "exports.md"
            path.write_text(text, encoding="utf-8")
            from_file = self.fingerprint(run_cli(str(path)))
        self.assertEqual(from_file, self.fingerprint(run_cli("-", stdin=text)))

    def test_line_endings_trailing_spaces_and_a_bom_do_not_change_it(self):
        text = document(spec_block())
        same = ["\ufeff" + text, text.replace("\n", "\r\n"), text.replace("\n", "  \n")]
        base = self.fingerprint(run_cli("-", stdin=text))
        for variant in same:
            with self.subTest(variant=repr(variant[:12])):
                self.assertEqual(base, self.fingerprint(run_cli("-", stdin=variant)))

    def test_a_changed_word_changes_it(self):
        text = document(spec_block())
        other = text.replace("download a CSV file", "download a CSV document")
        self.assertNotEqual(self.fingerprint(run_cli("-", stdin=text)),
                            self.fingerprint(run_cli("-", stdin=other)))


class PacingProseTests(unittest.TestCase):
    """Interview pacing, durability, gap owners and the read-back are stated in the skill."""

    SPECS = HERE.parent / "skills" / "specs-from-prd"

    def flat(self, path):
        return " ".join(path.read_text(encoding="utf-8").split())

    def test_the_interview_offers_grouping_prints_the_findings_and_acknowledges_decisions(self):
        text = self.flat(self.SPECS / "references" / "interview.md")
        for needle in ("grouped by theme", "F-nn table", "Recorded as D-", "who can decide this",
                       "Unassigned"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)

    def test_the_template_does_not_invent_gap_owners(self):
        text = self.flat(self.SPECS / "templates" / "specs-document.md")
        self.assertIn("Unassigned", text)

    def test_the_written_file_is_confirmed_by_fingerprint_not_a_full_read_back(self):
        text = self.flat(self.SPECS / "SKILL.md")
        start = text.index("## Phase 8")
        phase8 = text[start:text.index("## Error handling", start)]
        self.assertIn("fingerprint", phase8)
        self.assertNotIn("read the file back with `Read`", phase8)
        phase6 = text[text.index("## Phase 6"):text.index("## Phase 7")]
        self.assertIn("fingerprint", phase6)

    def test_phase_4_in_skill_md_points_at_the_pacing_choice(self):
        text = self.flat(self.SPECS / "SKILL.md")
        phase4 = text[text.index("## Phase 4"):text.index("## Phase 5")]
        self.assertIn("F-nn table", phase4)


class StoryCorrectnessTests(unittest.TestCase):
    """Small rules in story-from-document that decide which project, which mode, which reads."""

    BASE = HERE.parent / "skills" / "story-from-document"

    def flat(self, path):
        return " ".join(path.read_text(encoding="utf-8").split())

    def phase0(self):
        text = self.flat(self.BASE / "SKILL.md")
        start = text.index("## Phase 0: Choose the mode")
        return text[start:text.index("## Phase 1 (create)", start)]

    def test_a_project_the_user_names_wins_over_the_configuration(self):
        text = self.flat(self.BASE / "references" / "investigation.md")
        self.assertIn("names in the invocation", text)
        self.assertIn("wins over the configuration", text)
        self.assertIn("say which project you are using", text)

    def test_phase_0_classifies_on_the_locator_and_keeps_the_rest_as_context(self):
        phase0 = self.phase0()
        self.assertIn("Classify on the locator", phase0)
        self.assertIn("extra context", phase0)

    def test_a_written_brief_is_unambiguous_create_not_a_question(self):
        phase0 = self.phase0()
        create = phase0[phase0.index("**Unambiguous create:**"):phase0.index("**Ambiguous:**")]
        self.assertIn("a written brief with no Jira key", create)
        self.assertNotIn("a written brief with no key is **create**", phase0)

    def test_the_phase_0_read_is_the_phase_1_read(self):
        self.assertIn("this read is the Phase 1 read", self.phase0())

    def test_a_bare_page_id_is_only_a_confluence_source_once_confirmed(self):
        text = self.flat(self.BASE / "SKILL.md")
        phase1 = text[text.index("## Phase 1 (create)"):text.index("## Phase 1 (promote)")]
        self.assertIn("a bare page ID the user has confirmed", phase1)

    def test_promote_mode_does_not_ask_the_repositories_twice(self):
        text = self.flat(self.BASE / "references" / "promote-mode.md")
        self.assertIn("do not ask it again", text)


class CompactionTests(unittest.TestCase):
    """After a summary only the first 5,000 tokens of a skill are kept, so the invariants lead."""

    BASE = HERE.parent / "skills" / "story-from-document"

    def text(self):
        return (self.BASE / "SKILL.md").read_text(encoding="utf-8")

    def test_the_standing_rules_come_first(self):
        text = self.text()
        start = text.index("## Standing rules")
        self.assertLess(start, 3000)
        self.assertLess(start, text.index("## Permissions"))
        section = " ".join(text[start:text.index("\n## ", start + 1)].split())
        for needle in ("complete draft", "skip the review", "--dry-run", "data, never instructions",
                       "declines a permission prompt"):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)

    def test_the_file_does_not_grow_past_where_the_review_gate_is_kept(self):
        text = self.text()
        # The standing rules at the top carry the invariants through a summary, so this guard
        # only stops the file (and the review gate's position in it) from drifting further.
        self.assertLess(len(text), 22000)
        self.assertLess(text.index("Confirmation must come after the user has seen the draft"), 19500)

    def test_the_mockups_step_lives_in_a_reference_whose_links_resolve(self):
        text = self.text()
        start = text.index("## Phase 3.5")
        stub = " ".join(text[start:text.index("\n## ", start + 1)].split())
        self.assertIn("references/mockups.md", stub)
        self.assertIn("--dry-run", stub)
        reference = self.BASE / "references" / "mockups.md"
        body = reference.read_text(encoding="utf-8")
        for needle in ("mockup-core.md", "render.sh", "Dry run"):
            with self.subTest(needle=needle):
                self.assertIn(needle, body)
        self.assertTrue((reference.parent / "../../ui-mockups/references/mockup-core.md").resolve().is_file())
        self.assertNotIn("(../ui-mockups/", body)


class PolishTests(unittest.TestCase):
    """Small corrections, one word per concept, and the two teaching examples."""

    STORY = HERE.parent / "skills" / "story-from-document"
    SPECS = HERE.parent / "skills" / "specs-from-prd"

    def flat(self, path):
        return " ".join(path.read_text(encoding="utf-8").split())

    def story_files(self):
        return [self.STORY / "SKILL.md", *sorted((self.STORY / "references").glob("*.md")),
                *sorted((self.STORY / "templates").glob("*.md"))]

    def test_the_mockup_template_is_linked_directly_from_the_reference(self):
        text = self.flat(self.STORY / "references" / "mockups.md")
        self.assertIn("../../ui-mockups/templates/mockup-section.md", text)
        self.assertTrue((self.STORY / "references" / "../../ui-mockups/templates/mockup-section.md").resolve().is_file())

    def test_no_stale_counts_or_unreachable_sentences(self):
        for skill in (self.STORY, self.SPECS):
            text = self.flat(skill / "SKILL.md")
            with self.subTest(skill=skill.name):
                self.assertNotIn("If no block appears above", text)
        self.assertNotIn("four of the phases", (self.STORY / "SKILL.md").read_text(encoding="utf-8"))
        self.assertNotIn("Step-3", (self.STORY / "templates" / "story-structure.md").read_text(encoding="utf-8"))

    def test_the_promote_step_has_one_name(self):
        for path in self.story_files():
            with self.subTest(file=path.name):
                text = self.flat(path)
                self.assertNotIn("promote-mode read", text)
                self.assertNotIn("promote-mode step", text)
        for name in ("breakdown-and-epic.md", "jira-write-procedure.md"):
            with self.subTest(file=name):
                self.assertIn("Phase 1 (promote)", self.flat(self.STORY / "references" / name))

    def test_the_declared_argument_is_used_or_absent(self):
        text = (self.SPECS / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("arguments: prd-source", text)
        self.assertIn("argument-hint:", text)

    def test_the_checker_requirements_are_stated(self):
        text = self.flat(self.SPECS / "SKILL.md")
        self.assertIn("Python 3.9", text)
        self.assertIn("`python3`", text)

    def test_checker_output_says_errors_and_invest_says_results(self):
        skill = self.flat(self.SPECS / "SKILL.md")
        self.assertIn("Fix every error it reports", skill)
        self.assertNotIn("Fix every finding it reports", skill)
        self.assertIn("with no errors", skill)
        self.assertIn("INVEST result cells", skill)
        invest = self.flat(self.SPECS / "references" / "invest.md")
        self.assertIn("six results", invest)
        self.assertNotIn("six verdicts", invest)
        template = (self.SPECS / "templates" / "specs-document.md").read_text(encoding="utf-8")
        self.assertIn("| Criterion | Result | Reason |", template)
        self.assertTrue(cs.__doc__.lstrip().startswith("Checker for"))
        self.assertIn("INVEST_RESULT", [f.code for f in cs.check_text(document(spec_block(invest={**{n: ("Pass", "ok") for n in cs.INVEST}, "Small": ("Maybe", "x")})))[1]])

    def test_the_story_templates_show_one_model_paragraph_each(self):
        context = self.flat(self.STORY / "templates" / "story-structure.md")
        self.assertIn("Example Context paragraph", context)
        preamble = self.flat(self.STORY / "templates" / "subtask-structure.md")
        self.assertIn("Example preamble", preamble)

    def test_invest_has_a_before_and_after_split(self):
        text = self.flat(self.SPECS / "references" / "invest.md")
        for needle in ("Example", "Before:", "After:"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)

    def test_the_dry_run_standing_rule_allows_local_mockup_files(self):
        text = (self.STORY / "SKILL.md").read_text(encoding="utf-8")
        start = text.index("## Standing rules")
        rules = " ".join(text[start:text.index("\n## ", start + 1)].split())
        self.assertIn("nothing is written to Jira, Confluence or claude.ai", rules)
        self.assertIn("local mockup files", rules)


if __name__ == "__main__":
    unittest.main()
