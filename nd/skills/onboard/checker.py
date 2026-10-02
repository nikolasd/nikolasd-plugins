"""Acceptance gate for code-grounded onboarding docs.

Usage:
  python checker.py DOCS_DIR --layout single
  python checker.py DOCS_DIR --layout tracked --track billing:'src/billing/|invoice_' --track reports:'src/reports/|report_'
  python checker.py DOCS_DIR --layout tracked --root /path/to/repo --min-cites 25

Rules enforced (all must hold for PASS):
  - every backtick-quoted string that looks like a repo path resolves from ROOT (0 dangling)
  - >= MIN_CITES distinct cited FILES per doc (anchors of the same file count once, so a doc cannot
    be padded with many anchors of one file); ONBOARDING.md needs 1.6x that; OWNERSHIP.md exempt.
    No doc needs more distinct files than the repo has citable files. Citations under ONBOARDING's
    "existing in-repo prose" heading do not count. When --min-cites is not given, the floor is
    min(25, max(3, citable_files * 2 // 3)), printed, so a tiny repo is never asked for more than it has
  - >= 1 non-empty ```mermaid block (starting with a diagram keyword) in every C4 doc, every
    */components.md, the AI/runtime design doc, infrastructure.md, deployment.md and ONBOARDING.md
  - ONBOARDING.md links every sibling doc; every relative markdown link resolves
  - paths match case-exactly; `path:func()` and `path:L1-L2, L3` are checked as `path:func` / `path:L1-L2`
  - not treated as paths: MIME types, strings starting with ~ or @, URLs, and anything with spaces
  - tracked layout: track dirs contain 0 hits of the *other* tracks' leak regexes;
    common/* names domain packages only under a heading containing "Domain extension points"
  - no backticked citation, and no markdown link out of the docs dir, to inadmissible evidence
    (README*, CLAUDE.md, AGENTS.md, docs/, reference/, *.docx); the one exemption is ONBOARDING.md
    under a heading containing "existing in-repo prose"
  - line anchors (`path:L10-L20`) lie inside the file; symbol anchors (`path:symbol`) occur in it
  - no TODO/TBD placeholder markers ("TODO:", "TBD:", or a line opening with the word) outside code spans
    (use --allow-placeholders to downgrade to a warning)
  - no secret-shaped strings anywhere in a doc (private keys, cloud and VCS tokens, JWTs,
    credentials in URLs, long values assigned to secret-named keys); reported as SECRETS with
    line numbers and kinds, never the value

Requires Python >= 3.9. For repos without LLM agents pass --ai-doc runtime-design.md --agents-doc workloads.md.

Track option format: NAME:REGEX, where NAME must equal the track's directory name and REGEX matches strings that must NOT appear in docs of
*other* tracks (i.e. the regex identifies NAME's own packages). Domain-package regex for the
common/ rule is the union of all track regexes.
"""

from __future__ import annotations

import argparse
import functools
import os
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
# A placeholder is a marker ("TODO:", "TBD:") or a line that opens with the word, not any use of it,
# so a repo whose domain says "TODO" (a task app) can describe itself.
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD)\s*:|^\s*(?:[-*]\s+)?(?:\[ \]\s*)?(?:TODO|TBD)\b", re.M)
MIME = re.compile(r"^(application|text|image|audio|video|multipart|font)/[\w.+-]+$")
URL_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
CODE_SPANS = re.compile(r"```.*?```|`[^`\n]*`", re.S)
ROUTE_GROUP = re.compile(r"(?:(?<=/)|^)\([\w.-]+\)(?=/|$)")  # Next.js (auth)/ style segments
BARE_CONFIG = re.compile(r"^(?:[\w-]+\.config\.\w+|\.[\w-]*rc(?:\.\w+)?)$")  # next.config.ts, .eslintrc
HEADING = re.compile(r"^(#{1,6})\s")
SECRET_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("Slack token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}")),
    ("API key (sk-)", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("credentials in URL", re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s:@/<>`]+:[^\s@/<>`$]{3,}@")),
    ("secret assignment", re.compile(
        r"(?i)\b(?:secret|token|passw(?:or)?d|api[_-]?key|private[_-]?key)\w*\s*[:=]\s*[\"']?"
        r"(?![<$({\[])[A-Za-z0-9/+_=.-]{16,}")),
)
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


@functools.lru_cache(maxsize=None)
def _names(directory: Path) -> frozenset[str] | None:
    """Entry names of a directory (None if unreadable), listed once per directory."""
    try:
        return frozenset(p.name for p in directory.iterdir())
    except OSError:
        return None


def exists_exact(root: Path, rel: str) -> bool:
    """Path exists with exactly this spelling (case-sensitive even on Windows/macOS)."""
    cur = root
    for part in Path(rel).parts:
        names = _names(cur)
        if names is None or part not in names:
            return False
        cur = cur / part
    return True


def inadmissible_cites(text: str, allow_exempt: bool = True, dirs: tuple[str, ...] = INADMISSIBLE_DIRS) -> list[str]:
    """Backticked citations of README/CLAUDE.md/docs/** etc. outside an 'existing in-repo prose' section.

    The section exemption applies only where `allow_exempt` is true (ONBOARDING.md)."""
    bad, section, fenced = [], None, False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
            continue
        if not fenced and HEADING.match(line):
            section = _section(line, section, "existing in-repo prose") if allow_exempt else None
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
                core.startswith(dirs)
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


MERMAID_BLOCK = re.compile(r"```mermaid[ \t]*\n(.*?)```", re.S)
MERMAID_KEYWORD = re.compile(
    r"^\s*(?:graph|flowchart|sequenceDiagram|classDiagram|stateDiagram(?:-v2)?|erDiagram|journey|gantt|pie|"
    r"mindmap|timeline|gitGraph|quadrantChart|C4Context|C4Container|C4Component|C4Dynamic|C4Deployment|"
    r"architecture-beta|block-beta)\b", re.M)
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", "target", ".next", ".tox"}


def mermaid_blocks(text: str) -> int:
    """Count fenced mermaid blocks that are non-empty and start with a diagram keyword."""
    return sum(1 for m in MERMAID_BLOCK.finditer(text) if MERMAID_KEYWORD.search(m.group(1)))


def needs_diagram(rel: str, ai_doc: str) -> bool:
    name = rel.rsplit("/", 1)[-1]
    return ("/c4/" in f"/{rel}" or name in ("components.md", ai_doc, "infrastructure.md", "deployment.md", "ONBOARDING.md"))


def strip_exempt(text: str) -> str:
    """Text without the lines inside an 'existing in-repo prose' section (headings included)."""
    keep, section, fenced = [], None, False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and HEADING.match(line):
            section = _section(line, section, "existing in-repo prose")
        if section is None:
            keep.append(line)
    return "\n".join(keep)


def inadmissible_links(text: str, doc: Path, docs: Path, dirs: tuple[str, ...] = INADMISSIBLE_DIRS) -> list[str]:
    """Markdown links that leave the docs dir and point at README/CLAUDE.md/AGENTS.md/docs/reference."""
    bad, docs = [], docs.resolve()
    for link in MDLINK.findall(text):
        if URL_SCHEME.match(link):
            continue
        target = (doc.parent / link).resolve()
        try:
            target.relative_to(docs)
            continue  # inside the docs dir: one of our own docs
        except ValueError:
            pass
        name = target.name
        parts = [p + "/" for p in target.parts]
        if INADMISSIBLE_NAMES.match(name) or name.lower().endswith(".docx") or any(d in parts for d in dirs):
            bad.append(f"link:{link}")
    return sorted(set(bad))


def citable_files(root: Path, exclude: Path | None = None, limit: int = 60) -> int:
    """Files a doc could legitimately cite: not README/CLAUDE.md/AGENTS.md, docs/, reference/, LICENSE,
    .docx, caches or hidden dirs, and not the docs dir being checked (`exclude`). Counting stops at
    `limit` (the floors never need more)."""
    n = 0
    skip = exclude.resolve() if exclude is not None else None
    for dirpath, dirs, files in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root).as_posix()
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")
                   and (skip is None or (Path(dirpath) / d).resolve() != skip)]
        if rel_dir == "." :
            dirs[:] = [d for d in dirs if f"{d}/" not in INADMISSIBLE_DIRS]
        for name in files:
            if INADMISSIBLE_NAMES.match(name) or name.lower().startswith("license") or name.lower().endswith(".docx"):
                continue
            n += 1
            if n >= limit:
                return n
    return n


def default_min_cites(root: Path, exclude: Path | None = None) -> int:
    """min(25, max(3, citable_files * 2 // 3)): a tiny repo gets a floor it can actually reach."""
    return min(25, max(3, citable_files(root, exclude) * 2 // 3))


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


def secret_hits(text: str) -> list[str]:
    """Kinds and line numbers of secret-shaped strings. Never returns the matched text."""
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        for kind, rx in SECRET_PATTERNS:
            if rx.search(line):
                hits.append(f"{kind} at line {n}")
    return hits


def check(
    docs: Path, root: Path, layout: str, tracks: dict[str, re.Pattern], min_cites: int,
    ai_doc: str = "ai-design.md", agents_doc: str = "agents.md", allow_placeholders: bool = False,
    inadmissible_dirs: tuple[str, ...] = INADMISSIBLE_DIRS, citable: int | None = None,
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
        exempt_ok = rel == "ONBOARDING.md"
        counted = strip_exempt(text) if exempt_ok else text
        cites = cite_paths(text)
        dangling = sorted({c for _, c in cites if not exists_exact(root, c)})
        n = len({core for _, core in cite_paths(counted)})
        mermaid = mermaid_blocks(text)
        r: dict = {"cites": n, "dangling": dangling, "mermaid": mermaid}
        need = round(min_cites * 1.6) if rel == "ONBOARDING.md" else (0 if rel == "OWNERSHIP.md" else min_cites)
        if citable is not None:
            need = min(need, citable)
        fails = []
        if n < need:
            fails.append(f"<{need} cites")
        if dangling:
            ok = False
        if needs_diagram(rel, ai_doc) and mermaid < 1:
            fails.append("no mermaid")
        if fails:
            r["FAIL"] = fails
            ok = False
        inadmissible = inadmissible_cites(text, exempt_ok, inadmissible_dirs) + inadmissible_links(counted, f, docs, inadmissible_dirs)
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
        secrets = secret_hits(text)
        if secrets:
            r["SECRETS"] = secrets
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
    ap.add_argument("--min-cites", type=int, default=None, help="distinct cited files per doc (default: min(25, max(5, repo_files // 2)), printed)")
    ap.add_argument("--ai-doc", default="ai-design.md", help="name of the AI/runtime design doc (e.g. runtime-design.md for repos without LLM agents)")
    ap.add_argument("--agents-doc", default="agents.md", help="per-track agents doc name (e.g. workloads.md)")
    ap.add_argument("--inadmissible-dir", action="append", default=None, metavar="DIR/",
                    help="repo-root directory whose files are not admissible evidence (repeatable; replaces the default docs/ and reference/). Use it when a real source dir is named docs/")
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
    if not root.is_dir():
        ap.error(f"--root is not a directory: {root}")
    dirs = tuple(d if d.endswith("/") else d + "/" for d in a.inadmissible_dir) if a.inadmissible_dir else INADMISSIBLE_DIRS
    citable = citable_files(root, docs)
    min_cites = a.min_cites if a.min_cites is not None else min(25, max(3, citable * 2 // 3))
    print(f"min-cites: {min_cites}" + ("" if a.min_cites is not None else f" (default; the repo has {citable} citable files)"))
    sys.exit(0 if check(docs, root, a.layout, tracks, min_cites, a.ai_doc, a.agents_doc, a.allow_placeholders, dirs, citable) else 1)


if __name__ == "__main__":
    main()
