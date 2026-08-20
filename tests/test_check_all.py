from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_all  # noqa: E402


class AuditWaiverTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.study = Path(self._tmp.name)

    def test_missing_manifest(self) -> None:
        self.assertEqual(check_all.read_audit_waiver(self.study), "")

    def test_unset_field(self) -> None:
        (self.study / "study.yaml").write_text("status: review\n", encoding="utf-8")
        self.assertEqual(check_all.read_audit_waiver(self.study), "")

    def test_set_field(self) -> None:
        (self.study / "study.yaml").write_text(
            'status: done\naudit_waiver: "documented deviations accepted 2026-08-20"\n',
            encoding="utf-8",
        )
        self.assertEqual(
            check_all.read_audit_waiver(self.study),
            "documented deviations accepted 2026-08-20",
        )

    def test_invalid_yaml(self) -> None:
        (self.study / "study.yaml").write_text("status: [unclosed\n", encoding="utf-8")
        self.assertEqual(check_all.read_audit_waiver(self.study), "")


def write_manifest(study: Path, track: str, status: str, gate, depth: str = "briefing") -> Path:
    manifest = study / "study.yaml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        f"id: \"x\"\ntitle: \"t\"\ndepth: {depth}\ntrack: {track}\nstatus: {status}\n"
        f"gates:\n  sources_approved: false\n  notes_approved: false\n"
        f"  experiments_approved: {gate}\n  draft_approved: false\n  review_signed_off: false\n",
        encoding="utf-8",
    )
    return manifest


class ValidateManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.study = Path(self._tmp.name)

    def test_review_track_with_na_gate_passes(self) -> None:
        manifest = write_manifest(self.study, "review", "drafting", "n_a")
        self.assertEqual(check_all.validate_manifest(manifest), [])

    def test_concept_track_with_na_gate_passes(self) -> None:
        manifest = write_manifest(self.study, "concept", "done", "n_a")
        self.assertEqual(check_all.validate_manifest(manifest), [])

    def test_experimental_track_with_boolean_gate_passes(self) -> None:
        manifest = write_manifest(self.study, "experimental", "experimenting", "true")
        self.assertEqual(check_all.validate_manifest(manifest), [])

    def test_review_track_with_boolean_gate_fails(self) -> None:
        manifest = write_manifest(self.study, "review", "drafting", "true")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("experiments_approved: n_a" in e for e in errors))

    def test_experimental_track_with_na_gate_fails(self) -> None:
        manifest = write_manifest(self.study, "experimental", "drafting", "n_a")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("boolean experiments_approved" in e for e in errors))

    def test_review_track_in_experimenting_state_fails(self) -> None:
        manifest = write_manifest(self.study, "review", "experimenting", "n_a")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("experimenting state" in e for e in errors))

    def test_missing_track_fails(self) -> None:
        manifest = self.study / "study.yaml"
        manifest.write_text("status: drafting\ndepth: briefing\n", encoding="utf-8")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("track" in e for e in errors))

    def test_invalid_status_fails(self) -> None:
        manifest = write_manifest(self.study, "review", "finished", "n_a")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("invalid status" in e for e in errors))

    def test_missing_manifest_fails(self) -> None:
        errors = check_all.validate_manifest(self.study / "study.yaml")
        self.assertEqual(len(errors), 1)

    def test_repo_studies_pass(self) -> None:
        studies = ROOT / "studies"
        if not studies.is_dir():
            self.skipTest("no studies directory")
        for study in sorted(studies.iterdir()):
            if not study.is_dir():
                continue
            with self.subTest(study=study.name):
                self.assertEqual(check_all.validate_manifest(study / "study.yaml"), [])


if __name__ == "__main__":
    unittest.main()
