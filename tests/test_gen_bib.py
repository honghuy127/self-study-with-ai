from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import gen_bib  # noqa: E402

REGISTRY = (
    "sources:\n"
    "  - key: vaswani2017attention\n"
    "    title: Attention Is All You Need\n"
    "    status: noted\n"
    "    bibtex: |\n"
    "      @article{vaswani2017attention,\n"
    "        title = {Attention Is All You Need},\n"
    "        year = {2017}\n"
    "      }\n"
    "  - key: missing2026bib\n"
    "    title: No citation record\n"
    "    status: noted\n"
    "  - key: rejected2026\n"
    "    title: Rejected source\n"
    "    status: rejected\n"
    "    bibtex: |\n"
    "      @misc{rejected2026,\n"
    "        title = {Rejected}\n"
    "      }\n"
)


def make_study(tmp: Path, registry: str, with_report: bool = True, with_slides: bool = False) -> Path:
    study = tmp / "2026-08_test"
    (study / "sources").mkdir(parents=True)
    (study / "sources" / "registry.yaml").write_text(registry, encoding="utf-8")
    if with_report:
        (study / "report").mkdir()
    if with_slides:
        (study / "slides").mkdir()
    return study


class GenerateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_writes_bibtex_blocks_with_header(self) -> None:
        study = make_study(Path(self._tmp.name), REGISTRY)
        text, written, skipped, aggregated = gen_bib.generate(study)
        self.assertIn("Generated from sources/registry.yaml", text)
        self.assertIn("@article{vaswani2017attention,", text)
        self.assertEqual(written, ["vaswani2017attention"])
        self.assertEqual(skipped, ["missing2026bib"])
        self.assertEqual(aggregated, [])

    def test_rejected_entries_excluded(self) -> None:
        study = make_study(Path(self._tmp.name), REGISTRY)
        text, _, _, _ = gen_bib.generate(study)
        self.assertNotIn("rejected2026", text)

    def test_cited_via_aggregated_not_warned(self) -> None:
        registry = (
            "sources:\n"
            "  - key: parentRepo\n"
            "    title: Aggregate repo\n"
            "    status: noted\n"
            "    bibtex: |\n"
            "      @misc{parentRepo,\n"
            "        title = {Aggregate}\n"
            "      }\n"
            "  - key: childComponent\n"
            "    title: A component of parentRepo\n"
            "    status: noted\n"
            "    cited_via: parentRepo\n"
        )
        study = make_study(Path(self._tmp.name), registry)
        text, written, skipped, aggregated = gen_bib.generate(study)
        self.assertEqual(written, ["parentRepo"])
        self.assertEqual(skipped, [])
        self.assertEqual(aggregated, ["childComponent"])
        self.assertNotIn("childComponent", text)

    def test_cited_via_dangling_target_skipped(self) -> None:
        registry = (
            "sources:\n"
            "  - key: orphanComponent\n"
            "    title: Cites a missing parent\n"
            "    status: noted\n"
            "    cited_via: doesNotExist\n"
        )
        study = make_study(Path(self._tmp.name), registry)
        _, written, skipped, aggregated = gen_bib.generate(study)
        self.assertEqual(written, [])
        self.assertEqual(skipped, ["orphanComponent"])
        self.assertEqual(aggregated, [])

    def test_missing_registry_raises(self) -> None:
        study = make_study(Path(self._tmp.name), REGISTRY)
        (study / "sources" / "registry.yaml").unlink()
        with self.assertRaises(SystemExit):
            gen_bib.generate(study)


class MainTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_main_writes_refs_bib(self) -> None:
        study = make_study(Path(self._tmp.name), REGISTRY)
        argv = sys.argv
        sys.argv = ["gen_bib.py", str(study)]
        self.addCleanup(setattr, sys, "argv", argv)
        self.assertEqual(gen_bib.main(), 0)
        text = (study / "report" / "refs.bib").read_text(encoding="utf-8")
        self.assertIn("@article{vaswani2017attention,", text)

    def test_main_refuses_without_report(self) -> None:
        study = make_study(Path(self._tmp.name), REGISTRY, with_report=False)
        argv = sys.argv
        sys.argv = ["gen_bib.py", str(study)]
        self.addCleanup(setattr, sys, "argv", argv)
        self.assertEqual(gen_bib.main(), 2)

    def test_main_supports_slides_only_study(self) -> None:
        study = make_study(Path(self._tmp.name), REGISTRY, with_report=False, with_slides=True)
        argv = sys.argv
        sys.argv = ["gen_bib.py", str(study)]
        self.addCleanup(setattr, sys, "argv", argv)
        self.assertEqual(gen_bib.main(), 0)
        self.assertIn("vaswani2017attention", (study / "slides" / "refs.bib").read_text(encoding="utf-8"))

    def test_main_missing_study_dir(self) -> None:
        argv = sys.argv
        sys.argv = ["gen_bib.py", str(Path(self._tmp.name) / "missing")]
        self.addCleanup(setattr, sys, "argv", argv)
        self.assertEqual(gen_bib.main(), 2)


if __name__ == "__main__":
    unittest.main()
