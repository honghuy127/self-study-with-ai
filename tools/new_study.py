#!/usr/bin/env python3
"""Scaffold a new study directory from shared/templates/.

Usage: python3 tools/new_study.py <slug> --mode interactive|delegated
       [--title "..."] [--intent understand|solve|build|compare|decide|refresh|survey]
       [--assurance quick|grounded|audited] [--methodology source-only|static-code|experimental|mixed]
       [--deliverables report,slides] [--from-title]

- slug: lowercase-hyphen identifier, e.g., transformer-length-extrapolation
- mode is required: interactive (tutored mastery) or delegated (agent-run
  investigation and report); there is no default
- interactive scaffolds learning/ and outputs/; delegated scaffolds report/,
  slides/, and reviews/ as the deliverables request
- experiments/ is scaffolded when the methodology is experimental or mixed
- with --assurance audited, also initializes .research/ via the vendored
  dossier script; quick and grounded studies pay no dossier cost
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDIES = ROOT / "studies"
TEMPLATES = ROOT / "shared" / "templates"

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

MODES = ("interactive", "delegated")
INTENTS = ("understand", "solve", "build", "compare", "decide", "refresh", "survey")
ASSURANCES = ("quick", "grounded", "audited")
METHODOLOGIES = ("source-only", "static-code", "experimental", "mixed")
DELIVERABLES = ("learning-note", "implementation", "decision-brief", "report", "slides", "none")
EXPERIMENTAL_METHODOLOGIES = ("experimental", "mixed")

DEFAULT_INTENT = {"interactive": "understand", "delegated": "survey"}
DEFAULT_DELIVERABLES = {"interactive": ["learning-note"], "delegated": ["report", "slides"]}
DEFAULT_STATUS = {"interactive": "scoped", "delegated": "proposed"}

DELEGATED_GATES_BLOCK = """gates:
  sources_approved: false
  notes_approved: false
  experiments_approved: n_a   # n_a unless methodology is experimental or mixed
  draft_approved: false
  review_signed_off: false"""

INTERACTIVE_GATES_BLOCK = """gates:
  scope_approved: false
  evidence_approved: false
  experiments_approved: n_a   # n_a unless methodology is experimental or mixed
  mastery_approved: false"""

ARTIFACTS_BLOCK = """artifacts:
  brief: brief.md
  registry: sources/registry.yaml
  notes_dir: notes/
  report: report/main.tex
  pdf: report/build/main.pdf
  dossier: .research/"""


def render_artifacts(fields: dict) -> str:
    """List only artifacts the scaffold actually creates."""
    lines = ["artifacts:", "  brief: brief.md", "  registry: sources/registry.yaml", "  notes_dir: notes/"]
    if fields["mode"] == "interactive":
        lines.append("  learning_dir: learning/")
        if "learning-note" in fields["deliverables"]:
            lines.append("  learning_note: outputs/learning-note.md")
    if "report" in fields["deliverables"]:
        lines.append("  report: report/main.tex")
        lines.append("  pdf: report/build/main.pdf")
    if fields["assurance"] == "audited":
        lines.append("  dossier: .research/")
    return "\n".join(lines)


def slugify(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "study"


def is_valid_slug(slug: str) -> bool:
    return bool(SLUG_RE.match(slug))


def study_dir_name(slug: str, when: dt.date) -> str:
    return f"{when.strftime('%Y-%m')}_{slug}"


def render_study_yaml(template_text: str, fields: dict) -> str:
    """Fill the manifest template for one study.

    `fields` carries id, title, created, mode, intent, assurance,
    methodology, deliverables (list), and status. The gates block is
    swapped wholesale for interactive mode, and the experiments gate
    becomes boolean when the methodology runs experiments.
    """
    out = (
        template_text.replace('id: ""', f'id: "{fields["id"]}"')
        .replace('title: ""', f'title: "{fields["title"]}"')
        .replace('created: ""', f'created: "{fields["created"]}"')
        .replace("mode: delegated", f'mode: {fields["mode"]}')
        .replace("intent: survey", f'intent: {fields["intent"]}')
        .replace("assurance: grounded", f'assurance: {fields["assurance"]}')
        .replace("methodology: source-only", f'methodology: {fields["methodology"]}')
        .replace("status: proposed", f'status: {fields["status"]}')
        .replace("  - report\n", "".join(f"  - {d}\n" for d in fields["deliverables"]))
    )
    if fields["mode"] == "interactive":
        out = out.replace(DELEGATED_GATES_BLOCK, INTERACTIVE_GATES_BLOCK)
    out = out.replace(ARTIFACTS_BLOCK, render_artifacts(fields))
    if fields["methodology"] in EXPERIMENTAL_METHODOLOGIES:
        out = out.replace("experiments_approved: n_a", "experiments_approved: false")
    return out


def copy_templates(study: Path, study_id: str, title: str, config: dict) -> None:
    """Materialize the mode-aware study skeleton.

    `config` carries mode, intent, assurance, methodology, deliverables.
    Both modes keep sources/ and notes/ (the evidence packet); interactive
    adds learning/ and outputs/, delegated adds reviews/ plus report/ and
    slides/ as deliverables request; experiments/ follows the methodology.
    """
    mode = config["mode"]
    deliverables = config["deliverables"]

    (study / "sources" / "pdfs").mkdir(parents=True)
    (study / "notes").mkdir()
    if config["methodology"] in EXPERIMENTAL_METHODOLOGIES:
        (study / "experiments").mkdir()

    if mode == "interactive":
        learning = study / "learning"
        learning.mkdir()
        for name, template in (
            ("baseline.md", "learning-baseline.md"),
            ("map.md", "learning-map.md"),
            ("journal.md", "learning-journal.md"),
            ("mastery.md", "learning-mastery.md"),
        ):
            shutil.copy(TEMPLATES / template, learning / name)
        practice = learning / "practice"
        practice.mkdir()
        (practice / ".gitkeep").write_text("", encoding="utf-8")
        if "learning-note" in deliverables:
            (study / "outputs").mkdir()
            shutil.copy(TEMPLATES / "learning-note.md", study / "outputs" / "learning-note.md")
    else:
        (study / "reviews").mkdir()

    if "report" in deliverables:
        (study / "report").mkdir()
        shutil.copytree(TEMPLATES / "latex", study / "report", dirs_exist_ok=True)
        (study / "report" / "refs.bib").write_text("", encoding="utf-8")
    if "slides" in deliverables:
        (study / "slides").mkdir()
        shutil.copytree(TEMPLATES / "slides", study / "slides", dirs_exist_ok=True)

    brief = (TEMPLATES / "brief.md").read_text(encoding="utf-8")
    (study / "brief.md").write_text(brief, encoding="utf-8")

    template_text = (TEMPLATES / "study.yaml").read_text(encoding="utf-8")
    fields = {
        "id": study_id,
        "title": title,
        "created": dt.date.today().isoformat(),
        "mode": mode,
        "intent": config["intent"],
        "assurance": config["assurance"],
        "methodology": config["methodology"],
        "deliverables": deliverables,
        "status": DEFAULT_STATUS[mode],
    }
    (study / "study.yaml").write_text(render_study_yaml(template_text, fields), encoding="utf-8")

    registry = study / "sources" / "registry.yaml"
    registry.write_text(
        "# provenance: queries run (text, date, scope), inclusion/exclusion reasons\n"
        "# entries are appended by the researcher agent; schema in AGENTS.md\n",
        encoding="utf-8",
    )


def init_dossier(study: Path, title: str) -> None:
    script = ROOT / "tools" / "research" / "research_state.py"
    subprocess.run(
        [sys.executable, str(script), "init", "--root", str(study), "--title", title, "--owner", "human"],
        check=True,
    )


def parse_deliverables(raw: str) -> list[str]:
    items = [item.strip() for item in raw.split(",") if item.strip()]
    for item in items:
        if item not in DELIVERABLES:
            raise ValueError(f"unknown deliverable {item!r}; choose from {', '.join(DELIVERABLES)}")
    return items or ["none"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug", help="lowercase-hyphen slug, or a title to slugify with --from-title")
    ap.add_argument("--mode", choices=MODES, required=True, help="interactive mastery or delegated investigation; required")
    ap.add_argument("--title", default=None)
    ap.add_argument("--intent", choices=INTENTS, default=None, help="defaults to understand (interactive) or survey (delegated)")
    ap.add_argument("--assurance", choices=ASSURANCES, default="grounded", help="evidence assurance level (default: grounded)")
    ap.add_argument(
        "--methodology",
        choices=METHODOLOGIES,
        default="source-only",
        help="what kind of evidence can answer the questions (default: source-only)",
    )
    ap.add_argument(
        "--deliverables",
        default=None,
        help="comma-separated outputs; defaults to learning-note (interactive) or report,slides (delegated)",
    )
    ap.add_argument("--from-title", action="store_true", help="treat positional arg as a title and slugify it")
    args = ap.parse_args(argv)

    slug = slugify(args.slug) if args.from_title else args.slug
    if not is_valid_slug(slug):
        print(f"new_study: invalid slug '{slug}'", file=sys.stderr)
        return 2
    title = args.title or slug.replace("-", " ")
    mode = args.mode
    try:
        deliverables = parse_deliverables(args.deliverables) if args.deliverables else list(DEFAULT_DELIVERABLES[mode])
    except ValueError as exc:
        print(f"new_study: {exc}", file=sys.stderr)
        return 2

    study_id = study_dir_name(slug, dt.date.today())
    study = STUDIES / study_id
    if study.exists():
        print(f"new_study: {study} already exists", file=sys.stderr)
        return 1

    config = {
        "mode": mode,
        "intent": args.intent or DEFAULT_INTENT[mode],
        "assurance": args.assurance,
        "methodology": args.methodology,
        "deliverables": deliverables,
    }
    copy_templates(study, study_id, title, config)
    if args.assurance == "audited":
        init_dossier(study, title)

    print(f"created {study.relative_to(ROOT)}")
    if mode == "interactive":
        print(f"next: fill studies/{study_id}/brief.md, then record the unaided baseline in learning/baseline.md")
    else:
        print(f"next: fill studies/{study_id}/brief.md, then /gather studies/{study_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
