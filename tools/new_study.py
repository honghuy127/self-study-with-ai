#!/usr/bin/env python3
"""Scaffold a new study directory from shared/templates/.

Usage: python3 tools/new_study.py <slug> [--title "..."] [--depth briefing|full] [--date YYYY-MM-DD]

- slug: lowercase-hyphen identifier, e.g., transformer-length-extrapolation
- creates studies/YYYY-MM_<slug>/ with brief.md, study.yaml, sources/, notes/,
  experiments/, report/, reviews/
- with --depth full, also initializes .research/ via the vendored dossier script
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


def slugify(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "study"


def is_valid_slug(slug: str) -> bool:
    return bool(SLUG_RE.match(slug))


def study_dir_name(slug: str, when: dt.date) -> str:
    return f"{when.strftime('%Y-%m')}_{slug}"


def render_study_yaml(template_text: str, study_id: str, title: str, depth: str, created: str) -> str:
    return (
        template_text.replace('id: ""', f'id: "{study_id}"')
        .replace('title: ""', f'title: "{title}"')
        .replace('created: ""', f'created: "{created}"')
        .replace("depth: briefing", f"depth: {depth}")
    )


def copy_templates(study: Path, study_id: str, title: str, depth: str) -> None:
    (study / "sources" / "pdfs").mkdir(parents=True)
    (study / "notes").mkdir()
    (study / "experiments").mkdir()
    (study / "report").mkdir()
    (study / "slides").mkdir()
    (study / "reviews").mkdir()

    brief = (TEMPLATES / "brief.md").read_text(encoding="utf-8")
    (study / "brief.md").write_text(brief, encoding="utf-8")

    study_yaml = (TEMPLATES / "study.yaml").read_text(encoding="utf-8")
    today = dt.date.today().isoformat()
    study_yaml = render_study_yaml(study_yaml, study_id, title, depth, today)
    (study / "study.yaml").write_text(study_yaml, encoding="utf-8")

    shutil.copytree(TEMPLATES / "latex", study / "report", dirs_exist_ok=True)
    (study / "report" / "refs.bib").write_text("", encoding="utf-8")
    shutil.copytree(TEMPLATES / "slides", study / "slides", dirs_exist_ok=True)

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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug", help="lowercase-hyphen slug, or a title to slugify with --from-title")
    ap.add_argument("--title", default=None)
    ap.add_argument("--depth", choices=("briefing", "full"), default="briefing")
    ap.add_argument("--from-title", action="store_true", help="treat positional arg as a title and slugify it")
    args = ap.parse_args()

    slug = slugify(args.slug) if args.from_title else args.slug
    if not is_valid_slug(slug):
        print(f"new_study: invalid slug '{slug}'", file=sys.stderr)
        return 2
    title = args.title or slug.replace("-", " ")

    study_id = study_dir_name(slug, dt.date.today())
    study = STUDIES / study_id
    if study.exists():
        print(f"new_study: {study} already exists", file=sys.stderr)
        return 1

    copy_templates(study, study_id, title, args.depth)
    if args.depth == "full":
        init_dossier(study, title)

    print(f"created {study.relative_to(ROOT)}")
    print("next: fill studies/%s/brief.md, then /gather studies/%s" % (study_id, study_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
