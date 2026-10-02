"""Tests for nd/skills/onboard/checker.py.

Run from the repo root:  python -m unittest discover -s tests/onboarding -v
"""

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

CHECKER = Path(__file__).resolve().parents[2] / "nd" / "skills" / "onboard" / "checker.py"
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


class TestSecrets(CheckerCase):
    def test_secret_shaped_string_fails_and_is_never_printed(self):
        key = "AKIA" + "ABCDEFGHIJKLMNOP"
        self.write_all({"deployment.md": self.body(f"The CI uses {key} as its key.")})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("SECRETS", out)
        self.assertIn("AWS access key at line", out)
        self.assertNotIn(key, out)

    def test_credentials_in_a_url_fail(self):
        self.write_all({"deployment.md": self.body("DB is postgres://admin:hunter2@db.internal/app")})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("credentials in URL", out)

    def test_variable_names_and_references_pass(self):
        self.write_all({"deployment.md": self.body(
            "Set `DATABASE_URL`; the key comes from api_key = ${API_KEY} and token = os.environ['TOKEN']."
        )})
        ok, out = self.run_check()
        self.assertTrue(ok, out)


class TestCitationCount(CheckerCase):
    def test_anchors_of_few_files_do_not_pad_the_floor(self):
        # 3 files, 30 distinct anchors: the floor counts distinct files, so this fails.
        cites = " ".join(f"`src/m{i % 3}.py:L{i // 3 + 1}`" for i in range(30))  # lines 1-10 exist
        self.write_all({"deployment.md": "# D\n\n" + cites + "\n\n```mermaid\ngraph TD\n A-->B\n```\n"})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("<25 cites", out)

    def test_default_floor_scales_with_citable_files(self):
        # 45 sources; README.md and docs/guide.md are not citable.
        self.assertEqual(checker.citable_files(self.root), 45)
        self.assertEqual(checker.default_min_cites(self.root), 25 if 45 * 2 // 3 > 25 else 45 * 2 // 3)
        small = self.root / "small"
        small.mkdir()
        for i in range(5):
            (small / f"f{i}.py").write_text("x = 1\n")
        (small / "README.md").write_text("hi\n")
        self.assertEqual(checker.citable_files(small), 5)   # the README does not count
        self.assertEqual(checker.default_min_cites(small), 3)  # a tiny repo gets a reachable floor

    def test_tiny_repo_passes_at_the_default_floor_citing_everything_it_has(self):
        import shutil
        shutil.rmtree(self.root / "src")
        (self.root / "src").mkdir()
        for i in range(5):
            (self.root / "src" / f"m{i}.py").write_text("def handler():\n    pass\n" + "x = 1\n" * 8)
        floor, citable = checker.default_min_cites(self.root, self.docs), checker.citable_files(self.root, self.docs)
        self.assertEqual((floor, citable), (3, 5))
        every = " ".join(f"`src/m{i}.py`" for i in range(5))
        links = " ".join(f"[{x}]({x})" for x in SINGLE if x != "ONBOARDING.md")
        docs = {rel: "# D\n\n" + every + "\n\n```mermaid\ngraph TD\n A-->B\n```\n" for rel in SINGLE}
        docs["ONBOARDING.md"] = docs["ONBOARDING.md"] + links
        self.write_all(docs)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ok = checker.check(self.docs, self.root, "single", {}, floor, citable=citable)
        self.assertTrue(ok, buf.getvalue())

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

    def test_tiny_repo_passes_through_main_at_the_default_floor(self):
        import shutil
        shutil.rmtree(self.root / "src")
        (self.root / "src").mkdir()
        for i in range(5):
            (self.root / "src" / f"m{i}.py").write_text("def handler():\n    pass\n" + "x = 1\n" * 8)
        every = " ".join(f"`src/m{i}.py`" for i in range(5))
        links = " ".join(f"[{x}]({x})" for x in SINGLE if x != "ONBOARDING.md")
        docs = {rel: "# D\n\n" + every + "\n\n```mermaid\ngraph TD\n A-->B\n```\n" for rel in SINGLE}
        docs["ONBOARDING.md"] += links
        self.write_all(docs)
        # no --min-cites: the default floor for 5 citable files must be reachable
        self.assertEqual(self.run_cli(str(self.docs), "--layout", "single", "--root", str(self.root)), 0)

    def test_allow_placeholders_flag(self):
        self.write_all({"engineering.md": self.body("TBD later")})
        args = [str(self.docs), "--layout", "single", "--root", str(self.root)]
        self.assertEqual(self.run_cli(*args), 1)
        self.assertEqual(self.run_cli(*args, "--allow-placeholders"), 0)



class TestStricterRules(CheckerCase):
    def test_diagram_required_in_infrastructure_deployment_ai_and_onboarding(self):
        for rel in ("infrastructure.md", "deployment.md", "ai-design.md"):
            with self.subTest(rel=rel):
                self.write_all({rel: self.body(mermaid=False)})
                ok, out = self.run_check()
                self.assertFalse(ok)
                self.assertIn("no mermaid", out)
        links = " ".join(f"[{s}]({s})" for s in SINGLE if s != "ONBOARDING.md")
        self.write_all({"ONBOARDING.md": self.body(links, mermaid=False, cites=40)})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("no mermaid", out)

    def test_empty_or_keywordless_mermaid_block_does_not_count(self):
        self.write_all({"deployment.md": self.body(mermaid=False) + "\n```mermaid\n```\n\n```mermaid\njust words\n```\n"})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("no mermaid", out)

    def test_prose_exemption_applies_only_in_onboarding(self):
        extra = "\n## Existing in-repo prose (unverified)\n\nThe README says things: `README.md`.\n"
        self.write_all({"engineering.md": self.body(extra)})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("INADMISSIBLE", out)
        links = " ".join(f"[{s}]({s})" for s in SINGLE if s != "ONBOARDING.md")
        self.write_all({"ONBOARDING.md": self.body(links + extra, cites=40)})
        ok, out = self.run_check()
        self.assertTrue(ok, out)

    def test_citations_under_the_exempt_heading_do_not_count_toward_the_floor(self):
        links = " ".join(f"[{s}]({s})" for s in SINGLE if s != "ONBOARDING.md")
        # 39 counted files + 5 more only under the exempt heading: still below the 40 needed.
        extra = "\n## Existing in-repo prose (unverified)\n\n" + " ".join(f"`src/m{i}.py`" for i in range(39, 44)) + "\n"
        self.write_all({"ONBOARDING.md": self.body(links, cites=39) + extra})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("<40 cites", out)

    def test_markdown_link_out_of_the_docs_dir_to_the_readme_fails(self):
        self.write_all({"engineering.md": self.body("See [the README](../README.md) for context.")})
        ok, out = self.run_check()
        self.assertFalse(ok)
        self.assertIn("link:../README.md", out)

    def test_bare_word_todo_in_prose_is_not_a_placeholder(self):
        self.write_all({"engineering.md": self.body("A task app lets users add a TODO item and mark a TBD date.")})
        ok, out = self.run_check()
        self.assertTrue(ok, out)

    def test_todo_marker_is_still_a_placeholder(self):
        for text in ("TODO: fill this in", "- TBD", "see this later TBD: owner"):
            with self.subTest(text=text):
                self.write_all({"engineering.md": self.body(text)})
                ok, out = self.run_check()
                self.assertFalse(ok)
                self.assertIn("placeholder", out)

    def test_inadmissible_dirs_can_be_replaced(self):
        # A real source dir named docs/ is flagged by default and fine once only reference/ is listed.
        (self.root / "docs" / "conf.py").write_text("x = 1\n")
        self.write_all({"engineering.md": self.body("The builder reads `docs/conf.py`.")})
        ok, out = self.run_check()
        self.assertFalse(ok)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ok = checker.check(self.docs, self.root, "single", {}, 25, inadmissible_dirs=("reference/",))
        self.assertTrue(ok, buf.getvalue())

    def test_directory_listings_are_cached(self):
        checker._names.cache_clear()
        for _ in range(3):
            self.assertTrue(checker.exists_exact(self.root, "src/m0.py"))
        info = checker._names.cache_info()
        self.assertGreaterEqual(info.hits, 2)


class TestRootArgument(CheckerCase):
    def test_nonexistent_root_is_a_usage_error(self):
        import sys
        self.write_all()
        old = sys.argv
        sys.argv = ["checker.py", str(self.docs), "--layout", "single", "--root", str(self.root / "typo")]
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as cm:
                    checker.main()
        finally:
            sys.argv = old
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
