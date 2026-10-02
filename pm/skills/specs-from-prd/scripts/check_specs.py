#!/usr/bin/env python3
"""Checker for a specs-from-prd document.

Usage:
  python3 check_specs.py docs/specs/exports.md
  python3 check_specs.py --root . docs/specs/exports.md   (also look up every cited path:line)
  python3 check_specs.py - < draft.md        (read the document from stdin)

Rules (every one must hold for PASS):
  - spec IDs (S-nn) and decision IDs (D-nn) are unique
  - every heading under "## Specs" starts with a spec ID, there is one "## Specs" section,
    and no spec heading sits outside it
  - no field line is repeated within a spec, and no code fence is left open
  - every spec has the four field lines: Status, Story, Repo, Depends on
  - Status is Ready, Needs decision or Withdrawn
  - every "Depends on" names real spec IDs (or "none"), the graph has no cycle, and no
    live spec depends on a withdrawn one
  - every live (not withdrawn) spec has exactly one repo, at least one acceptance
    criterion, and a Pass or Fail result for each of the six INVEST criteria, none Fail
  - Status agrees with the gaps: Ready has no [GAP: ...] (any case, in any line of the spec,
    heading included), Needs decision has at least one
  - every live spec has the bold labels User story, Scope, Acceptance criteria, Technical
    approach, Gaps and PRD trace, and its Technical approach and the Components touched
    table each cite a `path:line`; with --root every cited file must exist under the root
    and the line must be inside it
  - the header has Source PRD, Date (YYYY-MM-DD), Repositories and Audience and success
    signal; every live spec's Repo is one of the Repositories
  - the Open gaps section names exactly the specs that hold a gap (entries with no spec ID,
    such as a document-level gap, are allowed)
  - no em dash anywhere in the prose

It also prints a `fingerprint:` line, a short hash of the text that ignores line endings,
trailing spaces and a byte-order mark, so a written file can be compared with the draft that
was checked before it was written.

Headings and text inside fenced code blocks are ignored, so a Mermaid diagram cannot
create or hide a spec. Exit codes: 0 PASS, 1 FAIL, 2 the document cannot be read.
Requires Python >= 3.9. Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

STATUSES = ("Ready", "Needs decision", "Withdrawn")
INVEST = ("Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable")
FIELDS = ("Status", "Story", "Repo", "Depends on")
SPECS_HEADING = "## Specs"

H2 = re.compile(r"^## ")
H3 = re.compile(r"^### ")
SPEC_HEADING = re.compile(r"^### (S-\d+)(?:[ \t]+(.*))?$")
DECISION_HEADING = re.compile(r"^#### (D-\d+)(?:[ \t]+(.*))?$")
FIELD_LINE = re.compile(r"^- \*\*(Status|Story|Repo|Depends on):\*\*[ \t]*(.*?)[ \t]*$")
LABEL_LINE = re.compile(r"^\*\*[^*\n]+:\*\*")
LIST_ITEM = re.compile(r"^[ \t]*(?:\d+\.|-)[ \t]+\S")
ID_TOKEN = re.compile(r"^S-\d+$")
REQUIRED_LABELS = ("User story", "Scope", "Acceptance criteria", "Technical approach", "Gaps", "PRD trace")
HEADER_FIELDS = ("Source PRD", "Date", "Repositories", "Audience and success signal")
HEADER_LINE = re.compile(r"^- \*\*([^*]+):\*\*[ \t]*(.*?)[ \t]*$")
LABEL_NAME = re.compile(r"^\*\*([^*\n]+):\*\*")
EVIDENCE = re.compile(r"`([^`\s:]+):(\d+)(?:-(\d+))?`")
DATE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SPLIT_REPOS = re.compile(r"[,;&]|\s+and\s+")
GAP_MARK = re.compile(r"\[gap\b", re.IGNORECASE)
CRITERION_TEXT = re.compile(r"^[ \t]*(?:\d+\.|-)[ \t]+(.*)$")
MANY_REPOS = re.compile(r"[,;&]|\s+and\s+")


@dataclass
class Finding:
    code: str
    message: str
    line: int
    spec: str = ""

    def render(self) -> str:
        who = f"{self.spec} " if self.spec else ""
        return f"{who}(line {self.line}): {self.code}: {self.message}"


@dataclass
class Spec:
    id: str
    line: int
    fields: dict = field(default_factory=dict)  # field name -> value
    criteria: int = 0
    invest: dict = field(default_factory=dict)  # criterion -> verdict cell
    gaps: int = 0
    lines: list = field(default_factory=list)  # (lineno, text) outside fences
    labels: set = field(default_factory=set)  # bold labels found, e.g. "Scope"
    approach: list = field(default_factory=list)  # (lineno, text) of the Technical approach

    @property
    def status(self) -> str:
        return self.fields.get("Status", "")

    @property
    def live(self) -> bool:
        return self.status != "Withdrawn"


def prose_lines(text: str):
    """((line number, text) for every line outside a fenced code block, line of an unclosed fence)."""
    out = []
    fence = None
    opened = 0
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        stripped = line.lstrip()
        marker = stripped[:3]
        if fence is None and marker in ("```", "~~~"):
            fence = marker
            opened = number
            continue
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            continue
        out.append((number, line))
    return out, (opened if fence is not None else 0)


def table_cells(line: str):
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    return cells if len(cells) >= 2 else None


def fill_spec(spec: Spec, findings: list) -> None:
    in_criteria = False
    current_label = None
    for number, line in spec.lines:
        spec.gaps += len(GAP_MARK.findall(line))
        match = FIELD_LINE.match(line)
        if match:
            if match.group(1) in spec.fields:
                findings.append(Finding("DUP_FIELD", f"the '{match.group(1)}' line appears twice", number, spec.id))
            spec.fields[match.group(1)] = match.group(2)
            in_criteria = False
            current_label = None
            continue
        if LABEL_LINE.match(line):
            current_label = LABEL_NAME.match(line).group(1)
            spec.labels.add(current_label)
            if current_label == "Technical approach":
                spec.approach.append((number, line))
            in_criteria = current_label == "Acceptance criteria"
            continue
        if current_label == "Technical approach":
            spec.approach.append((number, line))
        if in_criteria and LIST_ITEM.match(line):
            item = CRITERION_TEXT.match(line).group(1).strip()
            if not (re.fullmatch(r"\W*none\W*", item, re.IGNORECASE) or item.lower().startswith("[gap")):
                spec.criteria += 1
        cells = table_cells(line)
        if cells and cells[0] in INVEST:
            spec.invest[cells[0]] = cells[1]


def parse_depends(raw: str):
    value = raw.strip()
    if value.lower() == "none":
        return [], []
    ids, bad = [], []
    for token in value.split(","):
        token = token.strip()
        (ids if ID_TOKEN.match(token) else bad).append(token)
    return ids, bad


def find_cycle(graph: dict):
    white, grey, black = 0, 1, 2
    color = {node: white for node in graph}
    stack: list = []

    def visit(node):
        color[node] = grey
        stack.append(node)
        for nxt in graph[node]:
            if color[nxt] == grey:
                return stack[stack.index(nxt):] + [nxt]
            if color[nxt] == white:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        color[node] = black
        return None

    for node in graph:
        if color[node] == white:
            found = visit(node)
            if found:
                return found
    return None


def dangling(path: str, start: int, end, root: Path):
    """A reason the citation path:start[-end] does not resolve under root, or None."""
    root = root.resolve()
    target = (root / path).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return f"{path} is outside the repository root"
    if not target.is_file():
        return f"{path} does not exist under the root"
    count = len(target.read_text(encoding="utf-8", errors="replace").splitlines())
    last = end if end else start
    if start < 1 or last < start or last > count:
        span = f"{start}-{end}" if end else str(start)
        return f"{path} has {count} lines, so line {span} is out of range"
    return None


def check_spec(spec: Spec, by_id: dict, findings: list, repositories=None) -> None:
    def add(code, message, line=None):
        findings.append(Finding(code, message, line or spec.line, spec.id))

    for name in FIELDS:
        if name not in spec.fields:
            add("MISSING_FIELD", f"no '- **{name}:**' line")
    if "Status" in spec.fields and spec.status not in STATUSES:
        add("BAD_STATUS", f"Status must be one of {', '.join(STATUSES)}, got {spec.status!r}")

    if "Depends on" in spec.fields:
        raw = spec.fields["Depends on"]
        if not raw.strip():
            add("MISSING_FIELD", "'Depends on' is empty: write 'none' or spec IDs such as S-01, S-02")
        ids, bad = parse_depends(raw) if raw.strip() else ([], [])
        for token in bad:
            add("DEP_UNRESOLVED", f"{token!r} is not a spec ID: write S-01, S-02 or none")
        for target in ids:
            if target not in by_id:
                add("DEP_UNRESOLVED", f"{target} is not a spec in this document")
            elif spec.live and by_id[target].status == "Withdrawn":
                add("DEP_ON_WITHDRAWN", f"{spec.id} depends on {target}, which is Withdrawn")

    if not spec.live:
        return

    repo = spec.fields.get("Repo", "")
    if "Repo" in spec.fields and (not repo.strip() or MANY_REPOS.search(repo)):
        add("REPO_COUNT", f"a spec belongs to exactly one repository, got {repo!r}")
    if (repositories is not None and repo.strip() and not SPLIT_REPOS.search(repo)
            and repo.strip() not in repositories):
        add("REPO_NOT_LISTED", f"Repo {repo.strip()!r} is not in the header's Repositories ({', '.join(repositories)})")
    if spec.criteria == 0:
        add("NO_AC", "no acceptance criterion under '**Acceptance criteria:**'")
    absent = [label for label in REQUIRED_LABELS if label not in spec.labels]
    if absent:
        add("MISSING_LABEL", f"no bold label for: {', '.join(absent)}")
    if "Technical approach" in spec.labels and not any(EVIDENCE.search(text) for _, text in spec.approach):
        add("NO_EVIDENCE", "the Technical approach cites no `path:line`")

    missing = [name for name in INVEST if name not in spec.invest]
    if missing:
        add("INVEST_MISSING", f"no INVEST row for: {', '.join(missing)}")
    for name, verdict in spec.invest.items():
        if verdict not in ("Pass", "Fail"):
            add("INVEST_RESULT", f"{name} result must be Pass or Fail, got {verdict!r}")
        elif verdict == "Fail":
            add("INVEST_FAIL", f"{name} is Fail: split, merge or reframe the spec, or record the gap")

    if spec.status == "Ready" and spec.gaps:
        add("STATUS_GAP_MISMATCH", f"Status is Ready but the spec holds {spec.gaps} [GAP: ...]")
    if spec.status == "Needs decision" and not spec.gaps:
        add("STATUS_GAP_MISMATCH", "Status is Needs decision but the spec holds no [GAP: ...]")


def section_lines(lines: list, heading: str):
    """The lines under a heading, up to the next heading of the same or a higher level, or None."""
    level = len(heading) - len(heading.lstrip("#"))
    for i, (_, line) in enumerate(lines):
        if line.strip() == heading:
            body = []
            for number, text in lines[i + 1:]:
                if re.match(r"^#{1,%d} " % level, text):
                    break
                body.append((number, text))
            return body
    return None


def check_text(text: str, root=None):
    """Return (specs, findings) for the document text. With a root, cited paths are looked up."""
    lines, unclosed = prose_lines(text)
    findings: list = []
    if unclosed:
        findings.append(Finding("UNCLOSED_FENCE", "this code fence is never closed, so everything after it was ignored", unclosed))

    for number, line in lines:
        if "\u2014" in line:
            findings.append(Finding("EM_DASH", "an em dash; rewrite the sentence without one", number))

    first_h2 = next((i for i, (_, line) in enumerate(lines) if H2.match(line)), len(lines))
    header = {}
    for _, line in lines[:first_h2]:
        match = HEADER_LINE.match(line)
        if match:
            header[match.group(1)] = match.group(2)
    for name in HEADER_FIELDS:
        if not header.get(name, "").strip():
            findings.append(Finding("MISSING_HEADER", f"the header has no '- **{name}:**' line, or it is empty", 1))
    if header.get("Date", "").strip() and not DATE_ISO.match(header["Date"].strip()):
        findings.append(Finding("BAD_DATE", f"Date must be YYYY-MM-DD, got {header['Date'].strip()!r}", 1))
    repositories = None
    if header.get("Repositories", "").strip():
        repositories = [part.strip() for part in SPLIT_REPOS.split(header["Repositories"]) if part.strip()]

    decisions: dict = {}
    for number, line in lines:
        match = DECISION_HEADING.match(line)
        if not match:
            continue
        did = match.group(1)
        if did in decisions:
            findings.append(Finding("DUP_ID", f"decision {did} is defined twice (first at line {decisions[did]})", number))
        else:
            decisions[did] = number

    start = next((i for i, (_, line) in enumerate(lines) if line.strip() == SPECS_HEADING), None)
    if start is None:
        findings.append(Finding("NO_SPECS", f"the document has no '{SPECS_HEADING}' section", 1))
        return [], findings
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if H2.match(lines[i][1]):
            end = i
            break

    for i, (number, line) in enumerate(lines):
        if i >= end and line.strip() == SPECS_HEADING:
            findings.append(Finding("DUP_SECTION", f"a second '{SPECS_HEADING}' section; keep every spec in one", number))
        if (i <= start or i >= end) and SPEC_HEADING.match(line):
            findings.append(Finding("SPEC_OUTSIDE_SECTION", f"{line.strip()!r} is outside the '{SPECS_HEADING}' section, so it is not checked", number))

    specs: list = []
    seen: dict = {}
    current = None
    for number, line in lines[start + 1:end]:
        if H3.match(line):
            match = SPEC_HEADING.match(line)
            if not match:
                findings.append(Finding("BAD_HEADING", f"a spec heading must start with an ID such as 'S-01': {line.strip()!r}", number))
                current = None
                continue
            sid = match.group(1)
            if sid in seen:
                findings.append(Finding("DUP_ID", f"spec {sid} is defined twice (first at line {seen[sid]})", number, sid))
                current = None
                continue
            seen[sid] = number
            current = Spec(id=sid, line=number, gaps=len(GAP_MARK.findall(line)))
            specs.append(current)
        elif current is not None:
            current.lines.append((number, line))

    if not specs and not any(f.code in ("DUP_ID", "BAD_HEADING") for f in findings):
        findings.append(Finding("NO_SPECS", f"the '{SPECS_HEADING}' section holds no spec", lines[start][0]))

    by_id = {spec.id: spec for spec in specs}
    for spec in specs:
        fill_spec(spec, findings)
    for spec in specs:
        check_spec(spec, by_id, findings, repositories)

    components = section_lines(lines, "### Components touched")
    if components is None:
        findings.append(Finding("MISSING_SECTION", "the document has no '### Components touched' section", 1))
    elif not any(EVIDENCE.search(text) for _, text in components):
        findings.append(Finding("NO_EVIDENCE", "the Components touched table cites no `path:line`", 1))

    gaps_section = section_lines(lines, "## Open gaps")
    named = set()
    if gaps_section is not None:
        named = set(re.findall(r"\bS-\d+\b", " ".join(text for _, text in gaps_section)))
    for spec in specs:
        if spec.live and spec.gaps and spec.id not in named:
            findings.append(Finding("GAPS_SUMMARY_MISMATCH", f"{spec.id} holds {spec.gaps} gap(s) but the Open gaps section does not name it", spec.line, spec.id))
    for sid in sorted(named):
        spec = by_id.get(sid)
        if spec is None:
            findings.append(Finding("GAPS_SUMMARY_MISMATCH", f"Open gaps names {sid}, which is not a spec in this document", 1))
        elif not spec.live or not spec.gaps:
            findings.append(Finding("GAPS_SUMMARY_MISMATCH", f"Open gaps names {sid}, which holds no gap", spec.line, sid))

    if root is not None:
        cited = [(spec.id, spec.approach) for spec in specs if spec.live] + [("", components or [])]
        for sid, entries in cited:
            for number, entry in entries:
                for match in EVIDENCE.finditer(entry):
                    end = int(match.group(3)) if match.group(3) else None
                    reason = dangling(match.group(1), int(match.group(2)), end, Path(root))
                    if reason:
                        findings.append(Finding("DANGLING_EVIDENCE", reason, number, sid))

    graph = {}
    for spec in specs:
        raw = spec.fields.get("Depends on", "")
        ids, _ = parse_depends(raw) if raw.strip() else ([], [])
        graph[spec.id] = [target for target in ids if target in by_id]
    cycle = find_cycle(graph)
    if cycle:
        findings.append(Finding("DEP_CYCLE", " -> ".join(cycle), by_id[cycle[0]].line, cycle[0]))
    return specs, findings


def fingerprint(text: str) -> str:
    """A short hash of the text that ignores line endings, trailing spaces and a leading BOM."""
    normal = "\n".join(line.rstrip() for line in text.lstrip("\ufeff").splitlines()) + "\n"
    return hashlib.sha256(normal.encode("utf-8")).hexdigest()[:12]


def summary(spec: Spec) -> str:
    depends = spec.fields.get("Depends on", "?") or "?"
    return f"{spec.id}: {spec.status or '?'}, {spec.criteria} criteria, {spec.gaps} gaps, depends on {depends}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Checker for a specs-from-prd document.")
    parser.add_argument("doc", help="path to the specs document, or - to read stdin")
    parser.add_argument("--root", type=Path, default=None,
                        help="repository root: when given, every cited path:line must exist under it")
    args = parser.parse_args(argv)
    try:
        if args.doc == "-":
            text = sys.stdin.read()
        else:
            text = Path(args.doc).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        print(f"cannot read {args.doc}: {error}", file=sys.stderr)
        return 2
    specs, findings = check_text(text, root=args.root)
    for spec in specs:
        print(summary(spec))
    for finding in sorted(findings, key=lambda f: f.line):
        print(finding.render())
    print(f"fingerprint: {fingerprint(text)}")
    print("RESULT: PASS" if not findings else "RESULT: FAIL")
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
