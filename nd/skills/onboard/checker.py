"""Acceptance gate for code-grounded onboarding docs.

Usage:
  python checker.py DOCS_DIR --layout single
  python checker.py DOCS_DIR --layout tracked --track billing:'src/billing/|invoice_' --track reports:'src/reports/|report_'
  python checker.py DOCS_DIR --layout tracked --root /path/to/repo --min-cites 25

Rules enforced (all must hold for PASS):
  - every backtick-quoted string that looks like a repo path resolves from ROOT (0 dangling)
  - >= MIN_CITES unique citations per doc, each `path` or `path:anchor` counted once (a small
    repo can have few files but many anchored claims); ONBOARDING.md needs >= 40; OWNERSHIP.md exempt
  - >= 1 ```mermaid block in every C4 doc and every */components.md
  - ONBOARDING.md links every sibling doc; every relative markdown link resolves
  - paths match case-exactly; `path:func()` and `path:L1-L2, L3` are checked as `path:func` / `path:L1-L2`
  - not treated as paths: MIME types, strings starting with ~ or @, URLs, and anything with spaces
  - tracked layout: track dirs contain 0 hits of the *other* tracks' leak regexes;
    common/* names domain packages only under a heading containing "Domain extension points"
  - no backticked citation of inadmissible evidence (README*, CLAUDE.md, AGENTS.md, docs/,
    reference/, *.docx), except under a heading containing "existing in-repo prose"
  - line anchors (`path:L10-L20`) lie inside the file; symbol anchors (`path:symbol`) occur in it
  - no TODO/TBD placeholders outside code spans (use --allow-placeholders to downgrade to a warning)

Requires Python >= 3.9. For repos without LLM agents pass --ai-doc runtime-design.md --agents-doc workloads.md.

Track option format: NAME:REGEX, where NAME must equal the track's directory name and REGEX matches strings that must NOT appear in docs of
*other* tracks (i.e. the regex identifies NAME's own packages). Domain-package regex for the
common/ rule is the union of all track regexes.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BACKTICK = re.compile(r"`([^`\n]+)`")
MDLINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
ROOT_FILES = {
    "Makefile", "Dockerfile", "local.mk", "pyproject.toml", "package.json", "docker-compose.yml",
    "docker-compose.yaml", "langgraph.json", "alembic.ini", "uv.lock", "poetry.lock", ".env.example",
    ".python-version", ".dockerignore", "go.mod", "Cargo.toml", "tsconfig.json",
    "requirements.txt", "setup.py", "setup.cfg", "tox.ini", "pytest.ini", "Pipfile", "Pipfile.lock",
    "pom.xml", "build.gradle", "settings.gradle", "Jenkinsfile", "Gemfile", "Gemfile.lock",
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "go.sum", "Cargo.lock", "CMakeLists.txt",
    "compose.yaml", "compose.yml", "Procfile", ".gitlab-ci.yml", "bitbucket-pipelines.yml",
    "azure-pipelines.yml", ".pre-commit-config.yaml", ".editorconfig",
}
INADMISSIBLE_DIRS = ("docs/", "reference/")
INADMISSIBLE_NAMES = re.compile(r"(?i)^(readme(\..+)?|claude\.md|agents\.md)$")
LINE_ANCHOR = re.compile(r"^L?(\d+)(?:-L?(\d+))?$")
SYMBOL_ANCHOR = re.compile(r"^[A-Za-z_][\w.$-]*$")
PLACEHOLDER = re.compile(r"\b(TODO|TBD)\b")
MIME = re.compile(r"^(application|text|image|audio|video|multipart|font)/[\w.+-]+$")
URL_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
CODE_SPANS = re.compile(r"```.*?```|`[^`\n]*`", re.S)
ROUTE_GROUP = re.compile(r"(?:(?<=/)|^)\([\w.-]+\)(?=/|$)")  # Next.js (auth)/ style segments
BARE_CONFIG = re.compile(r"^(?:[\w-]+\.config\.\w+|\.[\w-]*rc(?:\.\w+)?)$")  # next.config.ts, .eslintrc
HEADING = re.compile(r"^(#{1,6})\s")
COMMENT_LINE = re.compile(r"^\s*(?:#(?:\s|$)|//|/\*|\*(?:\s|/|$)|--\s|<!--)")


def _candidate(s: str) -> tuple[str, str] | None:
    """Split a backticked string into (core_path, anchor), or None if it is not path-shaped."""
    s = s.strip()
    if s.startswith(("http", "<", "/", "..", "$", "-", "~", "@")) or MIME.match(s):
        return None
    s = s.split(",")[0].strip()
    if any(ch in s for ch in ' *{}<>"='):
        return None
    head, _, anchor = s.partition(":")
    head = head.split("#")[0].removeprefix("./")
    anchor = re.sub(r"\(.*\)$", "", anchor)  # `func()` and `func(x)` are checked as `func`
    bare = ROUTE_GROUP.sub("", head)  # parentheses are allowed only as whole route-group segments
    if "(" in bare or ")" in bare or "(" in anchor or ")" in anchor:
        return None
    return head, anchor


def _section(line: str, level: int | None, marker: str) -> int | None:
    """Level of the open section named by `marker` after a heading line, else None.

    A section stays open across deeper sub-headings and closes at a heading of equal or
    higher level, so `### Readme` under "Existing in-repo prose" stays inside it.
    """
    m = HEADING.match(line)
    assert m is not None
    depth = len(m.group(1))
    if level is not None and depth > level:
        return level
    return depth if marker in line.lower() else None


def cite_paths(text: str) -> list[tuple[str, str]]:
    """Return (raw, core_path) for every backticked string that is meant as a repo path."""
    out = []
    for m in BACKTICK.finditer(text):
        cand = _candidate(m.group(1))
        if cand is None:
            continue
        core = cand[0]
        if "/" not in core and core not in ROOT_FILES and not BARE_CONFIG.match(core):
            continue
        out.append((core + (f":{cand[1]}" if cand[1] else ""), core))
    return out


def exists_exact(root: Path, rel: str) -> bool:
    """Path exists with exactly this spelling (case-sensitive even on Windows/macOS)."""
    cur = root
    for part in Path(rel).parts:
        try:
            if part not in {p.name for p in cur.iterdir()}:
                return False
        except OSError:
            return False
        cur = cur / part
    return True


def inadmissible_cites(text: str) -> list[str]:
    """Backticked citations of README/CLAUDE.md/docs/** etc. outside an 'existing in-repo prose' section."""
    bad, section, fenced = [], None, False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
            continue
        if not fenced and HEADING.match(line):
            section = _section(line, section, "existing in-repo prose")
            continue
        if section is not None:
            continue
        for m in BACKTICK.finditer(line):
            cand = _candidate(m.group(1))
            if cand is None or not cand[0]:
                continue
            core = cand[0]
            name = core.rsplit("/", 1)[-1]
            if (
                core.startswith(INADMISSIBLE_DIRS)
                or INADMISSIBLE_NAMES.match(name)
                or core.lower().endswith(".docx")
            ):
                bad.append(core)
    return sorted(set(bad))


def bad_anchors(text: str, root: Path) -> list[str]:
    """Anchors that cannot be true: line ranges past EOF / reversed, symbols absent from the file."""
    bad, cache = [], {}
    for raw, core in cite_paths(text):
        anchor = raw.rpartition(":")[2] if ":" in raw else ""
        target = root / core
        if not anchor or not target.is_file():
            continue
        if core not in cache:
            cache[core] = target.read_text(encoding="utf-8", errors="replace")
        body = cache[core]
        m = LINE_ANCHOR.match(anchor)
        if m:
            start, end = int(m.group(1)), int(m.group(2) or m.group(1))
            if start < 1 or end < start or end > len(body.splitlines()):
                bad.append(raw)
        elif SYMBOL_ANCHOR.match(anchor):
            symbol = re.escape(anchor.split(".")[-1])
            code = "\n".join(ln for ln in body.splitlines() if not COMMENT_LINE.match(ln))
            if not re.search(rf"(?<![\w$]){symbol}(?![\w$])", code):
                bad.append(raw)
    return sorted(set(bad))


def single_layout(ai_doc: str) -> list[str]:
    return [
        "c4/01-context.md", "c4/02-containers.md", "c4/03-components.md",
        "engineering.md", ai_doc, "infrastructure.md", "deployment.md", "ONBOARDING.md",
    ]


def tracked_layout(tracks: list[str], ai_doc: str, agents_doc: str) -> list[str]:
    common = [
        "common/c4/01-context.md", "common/c4/02-containers.md", "common/c4/03-components.md",
        "common/engineering.md", f"common/{ai_doc}", "common/infrastructure.md",
        "common/deployment.md",
    ]
    per_track = [f"{t}/{f}" for t in tracks for f in ("README.md", "components.md", agents_doc)]
    return common + per_track + ["OWNERSHIP.md", "ONBOARDING.md"]


def check(
    docs: Path, root: Path, layout: str, tracks: dict[str, re.Pattern], min_cites: int,
    ai_doc: str = "ai-design.md", agents_doc: str = "agents.md", allow_placeholders: bool = False,
) -> bool:
    if layout == "single":
        all_docs = single_layout(ai_doc)
    else:
        all_docs = tracked_layout(list(tracks), ai_doc, agents_doc)
    domain_rx = re.compile("|".join(p.pattern for p in tracks.values())) if tracks else None
    ok = True
    for rel in all_docs:
        f = docs / rel
        if not f.exists():
            print(f"{rel}: MISSING")
            ok = False
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        cites = cite_paths(text)
        dangling = sorted({c for _, c in cites if not exists_exact(root, c)})
        n = len({raw for raw, _ in cites})
        mermaid = text.count("```mermaid")
        r: dict = {"cites": n, "dangling": dangling, "mermaid": mermaid}
        need = 40 if rel == "ONBOARDING.md" else (0 if rel == "OWNERSHIP.md" else min_cites)
        fails = []
        if n < need:
            fails.append(f"<{need} cites")
        if dangling:
            ok = False
        if ("/c4/" in f"/{rel}" or rel.endswith("components.md")) and mermaid < 1:
            fails.append("no mermaid")
        if fails:
            r["FAIL"] = fails
            ok = False
        inadmissible = inadmissible_cites(text)
        if inadmissible:
            r["INADMISSIBLE"] = inadmissible
            ok = False
        anchors = bad_anchors(text, root)
        if anchors:
            r["bad_anchors"] = anchors
            ok = False
        track = rel.split("/")[0] if "/" in rel else None
        if track in tracks:
            others = [p for name, p in tracks.items() if name != track]
            hits = sorted({m.group(0) for p in others for m in p.finditer(text) if m.group(0)})
            if hits:
                r["LEAK"] = hits
                ok = False
        if rel.startswith("common/") and domain_rx:
            section, bad, fenced = None, [], False
            for line in text.splitlines():
                if line.startswith("```"):
                    fenced = not fenced
                if not fenced and HEADING.match(line):
                    section = _section(line, section, "domain extension point")
                elif domain_rx.search(line) and section is None:
                    bad.append(line[:90])
            if bad:
                r["DOMAIN_LEAK"] = len(bad)
                r["first"] = bad[:3]
                ok = False
        broken, linked = [], set()
        for link in MDLINK.findall(text):
            if URL_SCHEME.match(link):
                continue
            target = (f.parent / link).resolve()
            linked.add(target)
            if not target.exists():
                broken.append(link)
        if rel == "ONBOARDING.md":
            missing = [s for s in all_docs if s != rel and (docs / s).resolve() not in linked]
            if missing:
                r["missing_links"] = missing
                ok = False
        if broken:
            r["broken_links"] = broken
            ok = False
        placeholders = len(PLACEHOLDER.findall(CODE_SPANS.sub("", text)))
        if placeholders:
            r["placeholder"] = placeholders
            if not allow_placeholders:
                ok = False
        print(f"{rel}: {r}")
    print("RESULT:", "PASS" if ok else "FAIL")
    return ok


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docs_dir")
    ap.add_argument("--layout", choices=["single", "tracked"], required=True)
    ap.add_argument("--root", default=None, help="repo root (default: docs_dir's nearest parent containing .git, else cwd)")
    ap.add_argument("--track", action="append", default=[], help="NAME:REGEX (tracked layout only, repeatable)")
    ap.add_argument("--min-cites", type=int, default=25)
    ap.add_argument("--ai-doc", default="ai-design.md", help="name of the AI/runtime design doc (e.g. runtime-design.md for repos without LLM agents)")
    ap.add_argument("--agents-doc", default="agents.md", help="per-track agents doc name (e.g. workloads.md)")
    ap.add_argument("--allow-placeholders", action="store_true", help="report TODO/TBD as a warning instead of a failure")
    a = ap.parse_args()
    docs = Path(a.docs_dir).resolve()
    if not docs.is_dir():
        ap.error(f"docs_dir is not a directory: {a.docs_dir}")
    if a.root:
        root = Path(a.root).resolve()
    else:
        root = next((p for p in [docs, *docs.parents] if (p / ".git").exists()), Path.cwd())
    tracks: dict[str, re.Pattern] = {}
    for t in a.track:
        name, _, rx = t.partition(":")
        if not rx:
            ap.error(f"--track needs NAME:REGEX, got {t!r}")
        tracks[name] = re.compile(rx)
    if a.layout == "tracked" and not tracks:
        ap.error("--layout tracked requires at least one --track")
    sys.exit(0 if check(docs, root, a.layout, tracks, a.min_cites, a.ai_doc, a.agents_doc, a.allow_placeholders) else 1)


if __name__ == "__main__":
    main()
