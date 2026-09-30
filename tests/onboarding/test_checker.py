"""Tests for nd/skills/onboarding/checker.py.

Run from the repo root:  python -m unittest discover -s tests/onboarding -v
"""

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

CHECKER = Path(__file__).resolve().parents[2] / "nd" / "skills" / "onboarding" / "checker.py"
spec = importlib.util.spec_from_file_location("checker", CHECKER)
assert spec is not None and spec.loader is not None
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

SINGLE = checker.single_layout("ai-design.md")


class CheckerCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.docs = self.root / "docs-out"
        src = self.root / "src"
        src.mkdir()
        for i in range(45):
            (src / f"m{i}.py").write_text("def handler():\n    pass\n" + "x = 1\n" * 8)
        (self.root / "README.md").write_text("hi\n")
        (self.root / "docs").mkdir()
        (self.root / "docs" / "guide.md").write_text("prose\n")

    def body(self, extra: str = "", mermaid: bool = True, cites: int = 30) -> str:
        lines = [f"- fact `src/m{i}.py`" for i in range(cites)]
        diagram = "```mermaid\ngraph TD\n  A-->B\n```\n" if mermaid else ""
        return "# Doc\n\n" + "\n".join(lines) + "\n\n" + diagram + extra + "\n"

    def write_all(self, overrides: dict | None = None) -> None:
        overrides = overrides or {}
        for rel in SINGLE:
            f = self.docs / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            text = overrides.get(rel)
            if text is None:
                text = self.body()
                if rel == "ONBOARDING.md":
                    links = " ".join(f"[{s}]({s})" for s in SINGLE if s != rel)
                    text = self.body(links, cites=40)
            f.write_text(text, encoding="utf-8")

    def run_check(self, **kw) -> tuple[bool, str]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ok = checker.check(self.docs, self.root, "single", {}, 25, **kw)
        return ok, buf.getvalue()


class TestGate(CheckerCase):
    def test_clean_set_passes(self):
        self.write_all()
        ok, out = self.run_check()
        self.assertTrue(ok, out)

    def test_missing_doc_fails(self):
        self.write_all()
        (self.docs / "deployment.md").unlink()
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("deployment.md: MISSING", out)

    def test_dangling_path_fails(self):
        self.write_all({"engineering.md": self.body("see `src/nope.py`")})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("src/nope.py", out)

    def test_c4_doc_without_mermaid_fails(self):
        self.write_all({"c4/01-context.md": self.body(mermaid=False)})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("no mermaid", out)

    def test_too_few_cites_fails(self):
        self.write_all({"engineering.md": self.body(cites=5)})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("<25 cites", out)

    def test_onboarding_must_link_every_sibling(self):
        self.write_all({"ONBOARDING.md": self.body("[only](engineering.md)", cites=40)})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("missing_links", out)

    def test_onboarding_mention_without_link_fails(self):
        mention = " ".join(s for s in SINGLE if s != "ONBOARDING.md")
        self.write_all({"ONBOARDING.md": self.body(mention, cites=40)})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("missing_links", out)


class TestCitationCount(CheckerCase):
    def test_anchored_citations_of_few_files_count(self):
        # 3 files, 30 distinct anchored citations: a small deploy surface, well cited.
        cites = " ".join(f"`src/m{i % 3}.py:L{i // 3 + 1}`" for i in range(30))  # lines 1-10 exist
        self.write_all({"deployment.md": "# D\n\n" + cites + "\n\n```mermaid\ngraph TD\n A-->B\n```\n"})
        ok, out = self.run_check()
        self.assertTrue(ok, out)

    def test_repeating_one_citation_does_not_pad(self):
        cites = " ".join("`src/m0.py:L1`" for _ in range(30))
        self.write_all({"deployment.md": "# D\n\n" + cites + "\n\n```mermaid\ngraph TD\n A-->B\n```\n"})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("<25 cites", out)


class TestInadmissibleEvidence(CheckerCase):
    def test_citing_docs_dir_fails(self):
        self.write_all({"engineering.md": self.body("claim `docs/guide.md`")})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("INADMISSIBLE", out)

    def test_citing_readme_fails(self):
        self.write_all({"engineering.md": self.body("claim `README.md`")})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("INADMISSIBLE", out)

    def test_citing_claude_md_fails(self):
        self.write_all({"engineering.md": self.body("claim `CLAUDE.md`")})
        ok, _ = self.run_check()
        self.assertFalse(ok)

    def test_prose_section_is_exempt(self):
        extra = "## Existing in-repo prose (unverified)\n\n- `README.md`\n- `docs/guide.md`\n"
        self.write_all({"ONBOARDING.md": self.body(
            extra + " ".join(f"[{s}]({s})" for s in SINGLE if s != "ONBOARDING.md"), cites=40)})
        ok, out = self.run_check()
        self.assertTrue(ok, out)

    def test_exemption_ends_at_next_heading(self):
        extra = "## Existing in-repo prose\n\n- `README.md`\n\n## Traps\n\n- `README.md` says so\n"
        self.assertEqual(checker.inadmissible_cites(extra), ["README.md"])
        self.assertEqual(checker.inadmissible_cites("## Existing in-repo prose\n- `README.md`\n"), [])


class TestAnchors(CheckerCase):
    def test_line_range_inside_file_passes(self):
        self.assertEqual(checker.bad_anchors("`src/m0.py:L1-L5`", self.root), [])

    def test_line_range_past_eof_fails(self):
        self.assertEqual(checker.bad_anchors("`src/m0.py:L1-L999`", self.root), ["src/m0.py:L1-L999"])

    def test_reversed_range_fails(self):
        self.assertEqual(checker.bad_anchors("`src/m0.py:L5-L2`", self.root), ["src/m0.py:L5-L2"])

    def test_symbol_present_passes(self):
        self.assertEqual(checker.bad_anchors("`src/m0.py:handler`", self.root), [])

    def test_symbol_absent_fails(self):
        self.assertEqual(checker.bad_anchors("`src/m0.py:ghost`", self.root), ["src/m0.py:ghost"])

    def test_dotted_symbol_checks_last_part(self):
        self.assertEqual(checker.bad_anchors("`src/m0.py:Cls.handler`", self.root), [])

    def test_anchor_failure_fails_gate(self):
        self.write_all({"engineering.md": self.body("see `src/m0.py:ghost`")})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("bad_anchors", out)


class TestPlaceholders(CheckerCase):
    def test_placeholder_fails_by_default(self):
        self.write_all({"engineering.md": self.body("TBD later")})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("placeholder", out)

    def test_placeholder_allowed_by_flag(self):
        self.write_all({"engineering.md": self.body("TBD later")})
        ok, out = self.run_check(allow_placeholders=True)
        self.assertTrue(ok, out)

    def test_placeholder_in_code_span_ignored(self):
        self.write_all({"engineering.md": self.body("the `TODO` marker in `src/m1.py`")})
        ok, out = self.run_check()
        self.assertTrue(ok, out)


class TestRootFiles(CheckerCase):
    def test_non_python_root_files_are_checked(self):
        pairs = checker.cite_paths("`requirements.txt` `pom.xml` `Jenkinsfile`")
        self.assertEqual([c for _, c in pairs], ["requirements.txt", "pom.xml", "Jenkinsfile"])

    def test_missing_root_file_is_dangling(self):
        self.write_all({"deployment.md": self.body("needs `Jenkinsfile`")})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("Jenkinsfile", out)


class TestNotPaths(CheckerCase):
    def test_non_repo_strings_are_not_paths(self):
        text = "`application/json` `~/.cache/x` `@scope/pkg` `https://a/b` `make build`"
        self.assertEqual(checker.cite_paths(text), [])

    def test_trailing_parens_are_stripped_and_path_still_checked(self):
        self.assertEqual(checker.cite_paths("`src/nope.py:run()`"), [("src/nope.py:run", "src/nope.py")])
        self.write_all({"engineering.md": self.body("see `src/nope.py:run()`")})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("src/nope.py", out)

    def test_comma_anchor_keeps_first_part(self):
        self.assertEqual(checker.cite_paths("`src/m0.py:L1-L2, L3`"), [("src/m0.py:L1-L2", "src/m0.py")])

    def test_call_syntax_anchor_is_validated(self):
        self.assertEqual(checker.bad_anchors("`src/m0.py:ghost()`", self.root), ["src/m0.py:ghost"])

    def test_mailto_link_is_not_broken(self):
        self.write_all({"engineering.md": self.body("[mail](mailto:a@b.c)")})
        ok, out = self.run_check()
        self.assertTrue(ok, out)

    def test_fenced_heading_does_not_reset_prose_exemption(self):
        text = "## Existing in-repo prose\n```\n# not a heading\n```\n- `README.md`\n"
        self.assertEqual(checker.inadmissible_cites(text), [])


class TestSections(CheckerCase):
    def test_subheading_stays_inside_the_exempt_section(self):
        text = "## Existing in-repo prose (unverified)\n\n### Readme\n- `README.md`\n#### Deeper\n- `docs/x.md`\n"
        self.assertEqual(checker.inadmissible_cites(text), [])

    def test_same_level_heading_ends_the_exempt_section(self):
        text = "## Existing in-repo prose\n- `README.md`\n## Traps\n- `docs/x.md`\n"
        self.assertEqual(checker.inadmissible_cites(text), ["docs/x.md"])

    def test_higher_level_heading_ends_the_exempt_section(self):
        text = "### Existing in-repo prose\n- `README.md`\n## Traps\n- `docs/x.md`\n"
        self.assertEqual(checker.inadmissible_cites(text), ["docs/x.md"])

    def test_subheading_stays_inside_domain_extension_points(self):
        TRACKS = {"billing": checker.re.compile(r"invoice_"), "reports": checker.re.compile(r"report_")}
        layout = checker.tracked_layout(list(TRACKS), "ai-design.md", "agents.md")
        for rel in layout:
            f = self.docs / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            body = self.body()
            if rel == "common/engineering.md":
                body = self.body("## Domain extension points\n\n### Billing\n\nhooks via invoice_ calls\n")
            if rel == "ONBOARDING.md":
                body = self.body(" ".join(f"[{s}]({s})" for s in layout if s != rel), cites=40)
            f.write_text(body, encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ok = checker.check(self.docs, self.root, "tracked", TRACKS, 25)
        self.assertTrue(ok, buf.getvalue())


class TestPathShapes(CheckerCase):
    def test_route_group_paths_are_counted(self):
        pairs = checker.cite_paths("`src/app/(auth)/login/page.tsx` `(admin)/x.ts`")
        self.assertEqual([c for _, c in pairs], ["src/app/(auth)/login/page.tsx", "(admin)/x.ts"])

    def test_fabricated_route_group_path_is_dangling(self):
        self.write_all({"engineering.md": self.body("see `src/ghost/(x)/y.ts`")})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("src/ghost/(x)/y.ts", out)

    def test_real_route_group_path_passes(self):
        d = self.root / "src" / "app" / "(auth)" / "login"
        d.mkdir(parents=True)
        (d / "page.tsx").write_text("export default function Page() {}\n")
        self.write_all({"engineering.md": self.body("see `src/app/(auth)/login/page.tsx`")})
        ok, out = self.run_check()
        self.assertTrue(ok, out)

    def test_parentheses_elsewhere_are_not_paths(self):
        self.assertEqual(checker.cite_paths("`foo(bar)` `src/(a|b)/x` `call(x)/y`"), [])

    def test_call_arguments_in_anchor_are_dropped(self):
        self.assertEqual(checker.cite_paths("`src/m0.py:handler(x, y)`"), [])  # space: not path-shaped
        self.assertEqual(checker.cite_paths("`src/m0.py:handler(x)`"), [("src/m0.py:handler", "src/m0.py")])

    def test_fabricated_bare_config_file_is_dangling(self):
        self.write_all({"deployment.md": self.body("build via `next.config.ts` and `.eslintrc.json`")})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("next.config.ts", out)

    def test_real_bare_config_file_passes(self):
        (self.root / "next.config.ts").write_text("export default {}\n")
        self.write_all({"deployment.md": self.body("build via `next.config.ts`")})
        ok, out = self.run_check()
        self.assertTrue(ok, out)


class TestSymbolsInComments(CheckerCase):
    def setUp(self):
        super().setUp()
        (self.root / "src" / "c.py").write_text(
            "# only_in_comment helps here\n"
            "def real_fn():\n"
            "    pass\n"
            "// also_c_style comment\n"
            " * also_doc_block\n"
            "x = 1  # trailing_ok stays counted\n"
        )

    def test_symbol_only_in_a_comment_fails(self):
        self.assertEqual(checker.bad_anchors("`src/c.py:only_in_comment`", self.root), ["src/c.py:only_in_comment"])
        self.assertEqual(checker.bad_anchors("`src/c.py:also_c_style`", self.root), ["src/c.py:also_c_style"])
        self.assertEqual(checker.bad_anchors("`src/c.py:also_doc_block`", self.root), ["src/c.py:also_doc_block"])

    def test_symbol_in_code_passes(self):
        self.assertEqual(checker.bad_anchors("`src/c.py:real_fn`", self.root), [])

    def test_trailing_comment_on_a_code_line_still_counts(self):
        self.assertEqual(checker.bad_anchors("`src/c.py:trailing_ok`", self.root), [])

    def test_preprocessor_and_shebang_lines_are_not_comments(self):
        self.assertIsNone(checker.COMMENT_LINE.match("#define MAX 3"))
        self.assertIsNone(checker.COMMENT_LINE.match("#!/usr/bin/env bash"))
        self.assertIsNotNone(checker.COMMENT_LINE.match("# a comment"))


class TestExactness(CheckerCase):
    def test_symbol_is_whole_word(self):
        self.assertEqual(checker.bad_anchors("`src/m0.py:h`", self.root), ["src/m0.py:h"])
        self.assertEqual(checker.bad_anchors("`src/m0.py:handler`", self.root), [])

    def test_path_case_must_match(self):
        self.assertTrue(checker.exists_exact(self.root, "src/m0.py"))
        self.assertFalse(checker.exists_exact(self.root, "src/M0.py"))
        self.assertFalse(checker.exists_exact(self.root, "SRC/m0.py"))
        self.write_all({"engineering.md": self.body("see `src/M0.py`")})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("src/M0.py", out)


class TestTracked(CheckerCase):
    TRACKS = {"billing": checker.re.compile(r"src/billing/|invoice_"),
              "reports": checker.re.compile(r"src/reports/|report_")}

    def setUp(self):
        super().setUp()
        self.layout = checker.tracked_layout(list(self.TRACKS), "ai-design.md", "agents.md")

    def write_tracked(self, overrides: dict | None = None) -> None:
        overrides = overrides or {}
        for rel in self.layout:
            f = self.docs / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            text = overrides.get(rel)
            if text is None:
                text = self.body()
                if rel == "ONBOARDING.md":
                    links = " ".join(f"[{s}]({s})" for s in self.layout if s != rel)
                    text = self.body(links, cites=40)
            f.write_text(text, encoding="utf-8")

    def run_tracked(self) -> tuple[bool, str]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ok = checker.check(self.docs, self.root, "tracked", self.TRACKS, 25)
        return ok, buf.getvalue()

    def test_clean_tracked_set_passes(self):
        self.write_tracked()
        ok, out = self.run_tracked()
        self.assertTrue(ok, out)

    def test_layout_lists_per_track_docs(self):
        self.assertIn("billing/agents.md", self.layout)
        self.assertIn("reports/components.md", self.layout)
        self.assertIn("OWNERSHIP.md", self.layout)

    def test_track_doc_naming_other_track_leaks(self):
        self.write_tracked({"billing/README.md": self.body("calls src/reports/x")})
        ok, out = self.run_tracked()
        self.assertFalse(ok)
        self.assertIn("LEAK", out)

    def test_common_naming_track_outside_extension_points_fails(self):
        self.write_tracked({"common/engineering.md": self.body("uses invoice_ tables")})
        ok, out = self.run_tracked()
        self.assertFalse(ok)
        self.assertIn("DOMAIN_LEAK", out)

    def test_common_naming_track_under_extension_points_passes(self):
        extra = "## Domain extension points\n\nbilling plugs in via invoice_ hooks\n"
        self.write_tracked({"common/engineering.md": self.body(extra)})
        ok, out = self.run_tracked()
        self.assertTrue(ok, out)

    def test_leak_report_shows_matched_text_not_group_text(self):
        # A regex with an optional group: findall would report the empty group, not the match.
        self.TRACKS = {"a": checker.re.compile(r"src/(zzz)?"), "b": checker.re.compile(r"never-matches-xyz")}
        self.layout = checker.tracked_layout(list(self.TRACKS), "ai-design.md", "agents.md")
        self.write_tracked()
        _, out = self.run_tracked()
        self.assertIn("'LEAK': ['src/']", out)
        self.assertNotIn("'LEAK': ['']", out)


class TestRenamedDocs(CheckerCase):
    def test_ai_doc_rename_needs_flag(self):
        layout = checker.single_layout("runtime-design.md")
        for rel in layout:
            f = self.docs / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            text = self.body()
            if rel == "ONBOARDING.md":
                text = self.body(" ".join(f"[{s}]({s})" for s in layout if s != rel), cites=40)
            f.write_text(text, encoding="utf-8")
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("ai-design.md: MISSING", out)
        ok, out = self.run_check(ai_doc="runtime-design.md")
        self.assertTrue(ok, out)


class TestCli(CheckerCase):
    def run_cli(self, *argv: str) -> int:
        import sys
        old = sys.argv
        sys.argv = ["checker.py", *argv]
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                checker.main()
        except SystemExit as e:
            return int(e.code or 0)
        finally:
            sys.argv = old
        return 0

    def test_pass_exits_zero_fail_exits_one(self):
        self.write_all()
        args = [str(self.docs), "--layout", "single", "--root", str(self.root)]
        self.assertEqual(self.run_cli(*args), 0)
        (self.docs / "deployment.md").unlink()
        self.assertEqual(self.run_cli(*args), 1)

    def test_tracked_without_track_is_a_usage_error(self):
        self.write_all()
        self.assertEqual(self.run_cli(str(self.docs), "--layout", "tracked"), 2)

    def test_missing_docs_dir_is_a_usage_error(self):
        self.assertEqual(self.run_cli(str(self.root / "nope"), "--layout", "single"), 2)

    def test_allow_placeholders_flag(self):
        self.write_all({"engineering.md": self.body("TBD later")})
        args = [str(self.docs), "--layout", "single", "--root", str(self.root)]
        self.assertEqual(self.run_cli(*args), 1)
        self.assertEqual(self.run_cli(*args, "--allow-placeholders"), 0)


if __name__ == "__main__":
    unittest.main()
