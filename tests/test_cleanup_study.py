from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import cleanup_study  # noqa: E402


def manifest_text(status: str = "done", signed_off: bool = True, cleaned: str | None = None) -> str:
    lines = [
        "id: \"2026-08_test\"",
        "title: \"Test study\"",
        "created: \"2026-08-20\"",
        "depth: briefing",
        f"status: {status}",
        "",
        "gates:",
        "  sources_approved: true",
        "  notes_approved: true",
        "  experiments_approved: true",
        "  draft_approved: true",
        f"  review_signed_off: {'true' if signed_off else 'false'}",
    ]
    if cleaned is not None:
        lines.append(f'cleaned: "{cleaned}"')
    return "\n".join(lines) + "\n"


def make_study(tmp: Path, **manifest_kwargs) -> Path:
    study = tmp / "studies" / "2026-08_test"
    for parts in (
        ("brief.md",),
        ("notes", "source.md"),
        ("notes", "_synthesis.md"),
        ("report", "main.tex"),
        ("report", "refs.bib"),
        ("report", "build", "main.pdf"),
        ("slides", "main.tex"),
        ("slides", "build", "main.pdf"),
        ("sources", "registry.yaml"),
        ("sources", "repos.yaml"),
        ("sources", "docs", "page-01.md"),
        ("sources", "pdfs", "paper.pdf"),
        ("experiments", "E1", "out.json"),
        (".research", "state.json"),
        (".research", "runs", "run-001.json"),
        ("reviews", "r1-agent.md"),
    ):
        path = study.joinpath(*parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n", encoding="utf-8")
    (study / "study.yaml").write_text(manifest_text(**manifest_kwargs), encoding="utf-8")
    return study


class CleanupStudyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="cleanup-study-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_removes_process_material_and_keeps_knowledge_core(self) -> None:
        study = make_study(self.tmp)
        removed = cleanup_study.clean(study, dry_run=False)
        self.assertEqual(sorted(rel for rel, _ in removed), sorted(cleanup_study.REMOVABLE))
        for rel, size in removed:
            self.assertGreater(size, 0, rel)
        for rel in ("sources/docs", "sources/pdfs", "experiments", ".research", "reviews"):
            self.assertFalse((study / rel).exists(), rel)
        for rel in (
            "brief.md",
            "study.yaml",
            "notes/source.md",
            "notes/_synthesis.md",
            "report/main.tex",
            "report/refs.bib",
            "report/build/main.pdf",
            "slides/main.tex",
            "slides/build/main.pdf",
            "sources/registry.yaml",
            "sources/repos.yaml",
        ):
            self.assertTrue((study / rel).exists(), rel)
        data = yaml.safe_load((study / "study.yaml").read_text(encoding="utf-8"))
        self.assertTrue(data.get("cleaned"))

    def test_refuses_when_not_done(self) -> None:
        study = make_study(self.tmp, status="review")
        with self.assertRaises(SystemExit):
            cleanup_study.clean(study, dry_run=False)
        self.assertTrue((study / "experiments").is_dir())
        self.assertTrue((study / ".research").is_dir())

    def test_refuses_when_not_signed_off(self) -> None:
        study = make_study(self.tmp, signed_off=False)
        with self.assertRaises(SystemExit):
            cleanup_study.clean(study, dry_run=False)
        self.assertTrue((study / "experiments").is_dir())

    def test_refuses_when_already_cleaned(self) -> None:
        study = make_study(self.tmp, cleaned="2026-08-20")
        with self.assertRaises(SystemExit):
            cleanup_study.clean(study, dry_run=False)

    def test_dry_run_changes_nothing(self) -> None:
        study = make_study(self.tmp)
        removed = cleanup_study.clean(study, dry_run=True)
        self.assertEqual(sorted(rel for rel, _ in removed), sorted(cleanup_study.REMOVABLE))
        for rel in cleanup_study.REMOVABLE:
            self.assertTrue((study / rel).exists(), rel)
        text = (study / "study.yaml").read_text(encoding="utf-8")
        self.assertNotIn("cleaned:", text)

    def test_main_missing_study_dir(self) -> None:
        argv = sys.argv
        sys.argv = ["cleanup_study.py", str(self.tmp / "missing")]
        self.addCleanup(setattr, sys, "argv", argv)
        self.assertEqual(cleanup_study.main(), 2)


if __name__ == "__main__":
    unittest.main()
