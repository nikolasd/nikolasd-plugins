"""The skill's prose must stay in step with the checker it describes.

These caught real drift twice before they existed: a rule added to the checker but not
to the brief the writers receive, and a flag the gate step never mentioned.

Run from the repo root:  python -m unittest discover -s tests/onboarding -v
"""

import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2] / "nd" / "skills" / "onboarding"
read = lambda name: (SKILL / name).read_text(encoding="utf-8")
squash = lambda text: re.sub(r"\s+", " ", text)


def shared_context() -> str:
    text = read("briefs.md")
    start = text.index("## Shared context")
    end = text.index("## Report format")
    return squash(text[start:end])


class TestBriefMatchesChecker(unittest.TestCase):
    """Every rule the checker fails a doc for is told to the agents who write the docs."""

    def test_each_checker_failure_category_is_in_the_shared_context(self):
        ctx = shared_context()
        expectations = {
            "inadmissible sources": ["AGENTS.md", "README.md", "docs/**"],
            "line and symbol anchors": ["line ranges must lie inside the file", "`:symbol` must occur in it"],
            "anchor syntax": ["`:symbol` or `:L10-L20` only"],
            "absent files in plain text": ["does NOT exist", "plain text, never backticked"],
            "non-file strings with a slash": ["model/image/package ids", "git refs"],
            "placeholders": ["TODO/TBD"],
            "unknown marker": ["UNKNOWN — needs human"],
            "mermaid": ["mermaid"],
            "relative links": ["relative markdown links"],
            "leak rules": ["Domain extension points"],
        }
        for category, phrases in expectations.items():
            for phrase in phrases:
                self.assertIn(phrase, ctx, f"shared context lacks '{phrase}' ({category})")

    def test_shared_context_tells_writers_how_to_mention_files_and_todos(self):
        ctx = shared_context()
        self.assertIn("Backtick a file only when you cite its real path", ctx)
        self.assertIn('write "to-do comments"', ctx)
        self.assertIn("literal words TODO and TBD", ctx)

    def test_checker_still_fails_the_words_so_the_brief_rule_is_load_bearing(self):
        self.assertRegex(read("checker.py"), r'PLACEHOLDER = re\.compile\(r"\\b\(TODO\|TBD\)\\b"\)')

    def test_mixed_repos_keep_agents_md_and_cover_workloads(self):
        tracks = squash(read("tracks.md"))
        self.assertIn("In a **mixed** repo", tracks)
        self.assertIn("`agents.md` covers agents *and* workloads", tracks)
        self.assertIn("documents its workloads in `agents.md`", squash(read("briefs.md")))

    def test_principal_brief_names_the_exempt_heading_exactly(self):
        self.assertIn('headed exactly "Existing in-repo prose (unverified)"', squash(read("briefs.md")))

    def test_checker_exempts_that_same_heading(self):
        self.assertIn("existing in-repo prose", read("checker.py"))


class TestGateDocMatchesChecker(unittest.TestCase):
    def test_every_checker_option_is_documented_in_gate_md(self):
        options = set(re.findall(r'add_argument\(\s*"(--[\w-]+)"', read("checker.py")))
        self.assertGreaterEqual(len(options), 6)
        gate = read("gate.md")
        for opt in options:
            self.assertIn(opt, gate, f"gate.md does not document {opt}")

    def test_gate_md_has_an_action_for_every_failure_key_the_checker_prints(self):
        checker_src = read("checker.py")
        keys = set(re.findall(r'r\["(\w+)"\]\s*=', checker_src)) | {"MISSING", "dangling"}
        keys -= {"first"}  # diagnostic detail, not a failure of its own
        self.assertGreaterEqual(len(keys), 8)
        gate = read("gate.md")
        for key in keys:
            self.assertIn(key, gate, f"gate.md has no action for checker key {key}")

    def test_gate_md_says_to_always_pass_root(self):
        gate = squash(read("gate.md"))
        self.assertIn("**Always pass `--root`**", gate)
        self.assertIn("subfolder", gate)

    def test_round_two_message_covers_what_the_gate_table_routes_to_it(self):
        gate_keys = ("dangling", "<N cites", "no mermaid", "bad_anchors", "LEAK")
        msg = squash(read("briefs.md").split("## Round-2 message")[1])
        for needle in ("dangling", "fewer citations", "missing diagram", "bad_anchors", "LEAK / DOMAIN_LEAK"):
            self.assertIn(needle, msg, f"round-2 message lacks '{needle}'")
        for key in gate_keys:
            self.assertIn(key, read("gate.md"))

    def test_gate_md_states_what_fails_twice_means(self):
        self.assertIn("fails twice", read("gate.md"))

    def test_gate_md_lists_the_inadmissible_sources_the_checker_rejects(self):
        gate = read("gate.md")
        for source in ("README", "CLAUDE.md", "AGENTS.md", "`docs/`", "`reference/`", ".docx"):
            self.assertIn(source, gate)


class TestSkillMd(unittest.TestCase):
    def setUp(self):
        self.text = read("SKILL.md")

    def test_frontmatter(self):
        fm = self.text.split("---")[1]
        self.assertRegex(fm, r"(?m)^name: [a-z0-9-]{1,64}$")
        desc = re.search(r"(?m)^description: (.+)$", fm)
        assert desc is not None, "frontmatter has no description"
        self.assertLessEqual(len(desc.group(1)), 1024)
        self.assertIn("when_to_use:", fm)

    def test_every_markdown_link_resolves_to_a_bundled_file(self):
        links = re.findall(r"\]\(([^)#]+\.md)\)", self.text)
        self.assertTrue({"briefs.md", "gate.md", "tracks.md", "objective-template.md"} <= set(links))
        for link in links:
            self.assertTrue((SKILL / link).is_file(), f"SKILL.md links to missing {link}")

    def test_no_bundled_file_is_orphaned(self):
        for f in SKILL.iterdir():
            if f.is_file() and f.name != "SKILL.md":
                self.assertIn(f.name, self.text, f"SKILL.md never mentions {f.name}")

    def test_checklist_matches_the_workflow_steps(self):
        checklist = re.findall(r"- \[ \] (\d) ", self.text)
        steps = re.findall(r"(?m)^(\d)\. \*\*", self.text)
        self.assertEqual(checklist, [str(i) for i in range(9)])
        self.assertEqual(steps, checklist)

    def test_no_dated_measurement_in_the_skill_body(self):
        self.assertNotRegex(self.text, r"\$\d+|measured run|\d+ minutes")

    def test_single_source_for_the_hard_rules(self):
        # The rules live in briefs.md; SKILL.md only summarizes and points there.
        self.assertNotIn("Anchors are `:symbol`", self.text)
        self.assertIn("full rules live in the `# Shared context` block", self.text)

    def test_cost_line_counts_tracked_reviewers_and_flags_the_estimate(self):
        text = squash(self.text)
        self.assertIn("plus one per track when tracked", text)
        self.assertIn("unmeasured", text)

    def test_python_requirement_is_stated(self):
        self.assertIn("Python ≥3.9", self.text)


class TestReferenceFiles(unittest.TestCase):
    def test_briefs_md_has_a_table_of_contents_with_resolving_anchors(self):
        text = read("briefs.md")
        self.assertIn("## Contents", text)
        slugs = set()
        for heading in re.findall(r"(?m)^#{1,3} (.+)$", text):
            slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
            slugs.add(slug)
        for anchor in re.findall(r"\]\(#([^)]+)\)", text):
            self.assertIn(anchor, slugs, f"briefs.md TOC anchor #{anchor} has no heading")

    def test_search_wording_does_not_assume_a_shell(self):
        for name in ("briefs.md", "objective-template.md"):
            text = squash(read(name))
            self.assertIn("Grep", text, f"{name} assumes a shell for read-only search")
        self.assertNotIn("(grep, find, wc)", squash(read("briefs.md")))

    def test_inventory_step_records_the_evidence_root(self):
        self.assertIn("evidence root", read("SKILL.md"))

    def test_reviewer_brief_forbids_helpers_and_requires_a_report(self):
        text = squash(read("briefs.md"))
        self.assertIn("Do not start helper agents", text)
        self.assertIn("Your final message must contain the report", text)
        self.assertIn("Covered:", text)


if __name__ == "__main__":
    unittest.main()
