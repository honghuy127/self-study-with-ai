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


DELEGATED_GATES = (
    "  sources_approved: false\n"
    "  notes_approved: false\n"
    "  experiments_approved: {exp}\n"
    "  draft_approved: false\n"
    "  review_signed_off: false\n"
)
INTERACTIVE_GATES = (
    "  scope_approved: false\n"
    "  evidence_approved: false\n"
    "  experiments_approved: {exp}\n"
    "  mastery_approved: false\n"
)


def write_manifest(
    study: Path,
    mode: str = "delegated",
    status: str = "drafting",
    intent: str = "survey",
    assurance: str = "grounded",
    methodology: str = "source-only",
    deliverables: str = "  - report\n",
    experiments_gate: str = "n_a",
    gates: str | None = None,
    extra: str = "",
    schema_version: str = "2",
    verdict: str = "PASS",
) -> Path:
    if gates is None:
        gates = (DELEGATED_GATES if mode == "delegated" else INTERACTIVE_GATES).format(exp=experiments_gate)
    manifest = study / "study.yaml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    schema_line = f"schema_version: {schema_version}\n" if schema_version else ""
    manifest.write_text(
        'id: "x"\n'
        'title: "t"\n'
        'created: "2026-08-21"\n'
        f"{schema_line}"
        f"mode: {mode}\n"
        f"intent: {intent}\n"
        f"assurance: {assurance}\n"
        f"methodology: {methodology}\n"
        f"deliverables:\n{deliverables}"
        f"status: {status}\n"
        f"gates:\n{gates}"
        f'last_gate_verdict: "{verdict}"\n'
        f"{extra}",
        encoding="utf-8",
    )
    return manifest


class ValidateManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.study = Path(self._tmp.name)

    def test_delegated_source_only_passes(self) -> None:
        manifest = write_manifest(self.study)
        self.assertEqual(check_all.validate_manifest(manifest), [])

    def test_interactive_passes(self) -> None:
        manifest = write_manifest(
            self.study,
            mode="interactive",
            status="learning",
            intent="understand",
            deliverables="  - learning-note\n",
        )
        self.assertEqual(check_all.validate_manifest(manifest), [])

    def test_experimental_methodology_with_boolean_gate_passes(self) -> None:
        manifest = write_manifest(self.study, status="experimenting", methodology="experimental", experiments_gate="true")
        self.assertEqual(check_all.validate_manifest(manifest), [])

    def test_deprecated_track_fails(self) -> None:
        manifest = write_manifest(self.study, extra="track: review\n")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("deprecated field 'track'" in e for e in errors))

    def test_deprecated_depth_fails(self) -> None:
        manifest = write_manifest(self.study, extra="depth: full\n")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("deprecated field 'depth'" in e for e in errors))

    def test_missing_schema_version_fails(self) -> None:
        manifest = write_manifest(self.study, schema_version="")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("schema_version" in e for e in errors))

    def test_wrong_schema_version_fails(self) -> None:
        manifest = write_manifest(self.study, schema_version="1")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("schema_version must be 2" in e for e in errors))

    def test_missing_mode_fails(self) -> None:
        manifest = self.study / "study.yaml"
        manifest.write_text("status: drafting\n", encoding="utf-8")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("mode" in e for e in errors))

    def test_invalid_intent_fails(self) -> None:
        manifest = write_manifest(self.study, intent="explore")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("intent" in e for e in errors))

    def test_invalid_assurance_fails(self) -> None:
        manifest = write_manifest(self.study, assurance="exhaustive")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("assurance" in e for e in errors))

    def test_invalid_methodology_fails(self) -> None:
        manifest = write_manifest(self.study, methodology="theory")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("methodology" in e for e in errors))

    def test_invalid_deliverable_fails(self) -> None:
        manifest = write_manifest(self.study, deliverables="  - paper\n")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("deliverable" in e for e in errors))

    def test_empty_deliverables_fail(self) -> None:
        manifest = self.study / "study.yaml"
        manifest.write_text(
            'id: "x"\nmode: delegated\nintent: survey\nassurance: grounded\n'
            "methodology: source-only\ndeliverables: []\nstatus: drafting\n",
            encoding="utf-8",
        )
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("non-empty" in e for e in errors))

    def test_delegated_status_on_interactive_fails(self) -> None:
        manifest = write_manifest(
            self.study,
            mode="interactive",
            status="drafting",
            intent="understand",
            deliverables="  - learning-note\n",
        )
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("invalid status for interactive" in e for e in errors))

    def test_interactive_status_on_delegated_fails(self) -> None:
        manifest = write_manifest(self.study, status="practicing")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("invalid status for delegated" in e for e in errors))

    def test_source_only_with_boolean_experiments_gate_fails(self) -> None:
        manifest = write_manifest(self.study, experiments_gate="true")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("experiments_approved: n_a" in e for e in errors))

    def test_experimental_methodology_with_na_gate_fails(self) -> None:
        manifest = write_manifest(self.study, methodology="experimental")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("boolean experiments_approved" in e for e in errors))

    def test_experimenting_status_without_experimental_methodology_fails(self) -> None:
        manifest = write_manifest(self.study, status="experimenting")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("status experimenting" in e for e in errors))

    def test_interactive_missing_mastery_gate_fails(self) -> None:
        manifest = write_manifest(
            self.study,
            mode="interactive",
            status="learning",
            intent="understand",
            deliverables="  - learning-note\n",
            gates="  scope_approved: false\n  evidence_approved: false\n  experiments_approved: n_a\n",
        )
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("mastery_approved" in e for e in errors))

    def test_delegated_gates_on_interactive_fail(self) -> None:
        manifest = write_manifest(
            self.study,
            mode="interactive",
            status="learning",
            intent="understand",
            deliverables="  - learning-note\n",
            gates=DELEGATED_GATES.format(exp="n_a"),
        )
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("scope_approved" in e for e in errors))
        self.assertTrue(any("mastery_approved" in e for e in errors))

    def test_missing_manifest_fails(self) -> None:
        errors = check_all.validate_manifest(self.study / "study.yaml")
        self.assertEqual(len(errors), 1)

    def test_done_without_signoff_fails(self) -> None:
        manifest = write_manifest(
            self.study,
            status="done",
            gates=(
                "  sources_approved: true\n"
                "  notes_approved: true\n"
                "  experiments_approved: n_a\n"
                "  draft_approved: true\n"
                "  review_signed_off: false\n"
            ),
        )
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("review_signed_off" in e for e in errors))

    def test_done_with_empty_verdict_fails(self) -> None:
        manifest = write_manifest(
            self.study,
            status="done",
            gates=(
                "  sources_approved: true\n"
                "  notes_approved: true\n"
                "  experiments_approved: n_a\n"
                "  draft_approved: true\n"
                "  review_signed_off: true\n"
            ),
            verdict="",
        )
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("empty last_gate_verdict" in e for e in errors))

    def test_done_signed_off_with_verdict_passes(self) -> None:
        manifest = write_manifest(
            self.study,
            status="done",
            gates=(
                "  sources_approved: true\n"
                "  notes_approved: true\n"
                "  experiments_approved: n_a\n"
                "  draft_approved: true\n"
                "  review_signed_off: true\n"
            ),
        )
        self.assertEqual(check_all.validate_manifest(manifest), [])

    def test_retained_without_mastery_gate_fails(self) -> None:
        manifest = write_manifest(
            self.study,
            mode="interactive",
            status="retained",
            intent="understand",
            deliverables="  - learning-note\n",
        )
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("mastery_approved" in e for e in errors))

    def test_repo_studies_pass(self) -> None:
        studies = ROOT / "studies"
        if not studies.is_dir():
            self.skipTest("no studies directory")
        for study in sorted(studies.iterdir()):
            if not study.is_dir():
                continue
            with self.subTest(study=study.name):
                self.assertEqual(check_all.validate_manifest(study / "study.yaml"), [])


class ValidateArtifactsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.study = Path(self._tmp.name) / "2026-08_test"
        self.study.mkdir()

    def write(self, artifacts: str, cleaned: str = "") -> None:
        (self.study / "study.yaml").write_text(
            'id: "x"\n'
            f'cleaned: "{cleaned}"\n'
            f"artifacts:\n{artifacts}",
            encoding="utf-8",
        )

    def test_resolved_artifacts_pass(self) -> None:
        (self.study / "brief.md").write_text("x\n", encoding="utf-8")
        self.write("  brief: brief.md\n")
        self.assertEqual(check_all.validate_artifacts(self.study), [])

    def test_missing_artifact_fails(self) -> None:
        self.write("  report: report/main.tex\n")
        errors = check_all.validate_artifacts(self.study)
        self.assertTrue(any("missing path report/main.tex" in e for e in errors))

    def test_pdf_exempt(self) -> None:
        self.write("  pdf: report/build/main.pdf\n")
        self.assertEqual(check_all.validate_artifacts(self.study), [])

    def test_dossier_exempt_after_cleanup(self) -> None:
        self.write("  dossier: .research/\n", cleaned="2026-08-21")
        self.assertEqual(check_all.validate_artifacts(self.study), [])

    def test_dossier_required_before_cleanup(self) -> None:
        self.write("  dossier: .research/\n")
        errors = check_all.validate_artifacts(self.study)
        self.assertTrue(any("dossier" in e for e in errors))

    def test_audited_assurance_requires_dossier(self) -> None:
        (self.study / "study.yaml").write_text("assurance: audited\nartifacts: {}\n", encoding="utf-8")
        errors = check_all.validate_artifacts(self.study)
        self.assertTrue(any("audited assurance requires" in e for e in errors))

    def test_audited_assurance_with_dossier_passes(self) -> None:
        (self.study / ".research").mkdir()
        (self.study / "study.yaml").write_text("assurance: audited\nartifacts: {}\n", encoding="utf-8")
        self.assertEqual(check_all.validate_artifacts(self.study), [])

    def test_audited_cleaned_exempt(self) -> None:
        (self.study / "study.yaml").write_text(
            'assurance: audited\ncleaned: "2026-08-21"\nartifacts: {}\n', encoding="utf-8"
        )
        self.assertEqual(check_all.validate_artifacts(self.study), [])

    def test_delegated_done_requires_review_record(self) -> None:
        (self.study / "study.yaml").write_text(
            "mode: delegated\nstatus: done\nartifacts: {}\n", encoding="utf-8"
        )
        errors = check_all.validate_artifacts(self.study)
        self.assertTrue(any("reviews/" in e for e in errors))

    def test_delegated_done_with_reviews_passes(self) -> None:
        (self.study / "reviews").mkdir()
        (self.study / "reviews" / "r1-agent.md").write_text("x\n", encoding="utf-8")
        (self.study / "study.yaml").write_text(
            "mode: delegated\nstatus: done\nartifacts: {}\n", encoding="utf-8"
        )
        self.assertEqual(check_all.validate_artifacts(self.study), [])

    def test_delegated_done_cleaned_exempt(self) -> None:
        (self.study / "study.yaml").write_text(
            'mode: delegated\nstatus: done\ncleaned: "2026-08-21"\nartifacts: {}\n', encoding="utf-8"
        )
        self.assertEqual(check_all.validate_artifacts(self.study), [])

    def test_missing_manifest_is_silent(self) -> None:
        (self.study / "study.yaml").unlink(missing_ok=True)
        self.assertEqual(check_all.validate_artifacts(self.study), [])


class ValidateBriefTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.study = Path(self._tmp.name) / "2026-08_test"
        (self.study / "sources").mkdir(parents=True)

    def write_brief(self, text: str) -> None:
        (self.study / "brief.md").write_text(text, encoding="utf-8")

    def write_registry(self, keys: list[tuple[str, str]]) -> None:
        lines = ["sources:"]
        for key, status in keys:
            lines.append(f"  - key: {key}")
            lines.append(f"    status: {status}")
        (self.study / "sources" / "registry.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_filled_brief_passes(self) -> None:
        self.write_brief("# Brief\n\n- Source budget: 5 sources.\n\nFilled prose.\n")
        self.write_registry([("a2026", "noted")])
        errors, warnings = check_all.validate_brief(self.study)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_template_sentinel_fails(self) -> None:
        self.write_brief("# Brief\n\n- Primary question: [one sentence, answerable]\n")
        errors, _ = check_all.validate_brief(self.study)
        self.assertTrue(any("template guidance" in e for e in errors))

    def test_budget_exceeded_warns(self) -> None:
        self.write_brief("# Brief\n\n- Source budget: 2 sources.\n")
        self.write_registry([("a2026", "noted"), ("b2026", "noted"), ("c2026", "to-read")])
        errors, warnings = check_all.validate_brief(self.study)
        self.assertEqual(errors, [])
        self.assertTrue(any("source budget 2 exceeded: 3 sources" in w for w in warnings))

    def test_rejected_sources_not_counted(self) -> None:
        self.write_brief("# Brief\n\n- Source budget: 2 sources.\n")
        self.write_registry([("a2026", "noted"), ("b2026", "noted"), ("c2026", "rejected")])
        errors, warnings = check_all.validate_brief(self.study)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_missing_brief_is_silent(self) -> None:
        errors, warnings = check_all.validate_brief(self.study)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])


class NotAssessedTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._old_studies = check_all.STUDIES
        check_all.STUDIES = Path(self._tmp.name)
        self.addCleanup(setattr, check_all, "STUDIES", self._old_studies)

    def test_no_studies_reports_not_assessed(self) -> None:
        self.assertEqual(check_all.check_lint(), "NOT_ASSESSED")
        self.assertEqual(check_all.check_manifests(), "NOT_ASSESSED")
        self.assertEqual(check_all.check_artifacts(), "NOT_ASSESSED")
        self.assertEqual(check_all.check_briefs(), "NOT_ASSESSED")

    def test_no_dossiers_reports_not_assessed(self) -> None:
        (Path(self._tmp.name) / "2026-08_test").mkdir()
        self.assertEqual(check_all.check_audit(), "NOT_ASSESSED")


if __name__ == "__main__":
    unittest.main()
