from __future__ import annotations

import contextlib
import io
import subprocess
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
PAPER_READING_GATES = (
    "  paper_approved: false\n"
    "  analysis_approved: false\n"
    "  deck_approved: false\n"
    "  review_signed_off: false\n"
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
        if mode == "delegated":
            gates = DELEGATED_GATES.format(exp=experiments_gate)
        elif mode == "interactive":
            gates = INTERACTIVE_GATES.format(exp=experiments_gate)
        else:
            gates = PAPER_READING_GATES
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

    def test_paper_reading_passes(self) -> None:
        manifest = write_manifest(
            self.study,
            mode="paper-reading",
            status="analyzing",
            intent="understand",
            deliverables="  - slides\n",
        )
        self.assertEqual(check_all.validate_manifest(manifest), [])

    def test_paper_reading_requires_slides(self) -> None:
        manifest = write_manifest(
            self.study,
            mode="paper-reading",
            status="analyzing",
            intent="understand",
        )
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("requires slides" in error for error in errors))

    def test_paper_reading_rejects_experimental_methodology(self) -> None:
        manifest = write_manifest(
            self.study,
            mode="paper-reading",
            status="analyzing",
            intent="understand",
            methodology="experimental",
            deliverables="  - slides\n",
        )
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("source-only or static-code" in error for error in errors))

    def test_paper_reading_done_requires_all_gates(self) -> None:
        manifest = write_manifest(
            self.study,
            mode="paper-reading",
            status="done",
            intent="understand",
            deliverables="  - slides\n",
            gates=(
                "  paper_approved: false\n"
                "  analysis_approved: true\n"
                "  deck_approved: true\n"
                "  review_signed_off: true\n"
            ),
        )
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("paper_approved" in error for error in errors))

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

    def test_report_style_invalid_value_fails(self) -> None:
        manifest = write_manifest(self.study, extra="report_style: ieee\n")
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("invalid report_style" in e for e in errors))

    def test_report_style_without_report_deliverable_fails(self) -> None:
        manifest = write_manifest(
            self.study, deliverables="  - decision-brief\n", extra="report_style: plain\n"
        )
        errors = check_all.validate_manifest(manifest)
        self.assertTrue(any("not a deliverable" in e for e in errors))

    def test_report_style_with_report_passes(self) -> None:
        manifest = write_manifest(self.study, extra="report_style: plain\n")
        self.assertEqual(check_all.validate_manifest(manifest), [])

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

    def test_slides_pdf_exempt(self) -> None:
        self.write("  slides_pdf: slides/build/main.pdf\n")
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


class ValidatePaperReadingPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.study = Path(self._tmp.name) / "paper"
        (self.study / "sources" / "docs").mkdir(parents=True)
        (self.study / "notes").mkdir()
        (self.study / "sources" / "docs" / "target.txt").write_text("paper\n", encoding="utf-8")
        (self.study / "notes" / "target.md").write_text("notes\n", encoding="utf-8")

    def write_registry(self, role: str = "target-paper", status: str = "noted") -> None:
        (self.study / "sources" / "registry.yaml").write_text(
            "sources:\n"
            "  - key: target2026\n"
            f"    role: {role}\n"
            f"    status: {status}\n"
            "    snapshot: sources/docs/target.txt\n"
            "    notes_file: notes/target.md\n",
            encoding="utf-8",
        )

    def test_complete_target_packet_passes(self) -> None:
        self.write_registry()
        data = {"mode": "paper-reading", "status": "presenting", "assurance": "grounded"}
        self.assertEqual(check_all.validate_paper_reading_packet(self.study, data, False), [])

    def test_requires_exactly_one_target(self) -> None:
        self.write_registry(role="context")
        data = {"mode": "paper-reading", "status": "analyzing", "assurance": "grounded"}
        errors = check_all.validate_paper_reading_packet(self.study, data, False)
        self.assertTrue(any("exactly one" in error for error in errors))

    def test_presenting_requires_noted_target(self) -> None:
        self.write_registry(status="to-read")
        data = {"mode": "paper-reading", "status": "presenting", "assurance": "grounded"}
        errors = check_all.validate_paper_reading_packet(self.study, data, False)
        self.assertTrue(any("status: noted" in error for error in errors))


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


class ArchiveRecordTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.study = Path(self._tmp.name) / "2026-08_test"
        self.study.mkdir()

    def write_archive(self, commit: str = "abc1234") -> None:
        (self.study / "archive.yaml").write_text(
            f"archived_at: '2026-08-21'\ngit_commit: {commit}\n"
            "removed:\n  - path: .research\n    size_kb: 1\n    files: 1\n"
            "    retrieve: git show abc:studies/x/.research\n",
            encoding="utf-8",
        )

    def test_archived_missing_artifact_passes_when_commit_unverifiable(self) -> None:
        # Temp dir is not a git repo, so commit_resolvable returns None and the
        # archived path is accepted rather than reported missing.
        (self.study / "study.yaml").write_text("artifacts:\n  dossier: .research/\n", encoding="utf-8")
        self.write_archive()
        self.assertEqual(check_all.validate_artifacts(self.study), [])

    def test_missing_artifact_not_archived_fails(self) -> None:
        (self.study / "study.yaml").write_text("artifacts:\n  dossier: .research/\n", encoding="utf-8")
        errors = check_all.validate_artifacts(self.study)
        self.assertTrue(any("missing path .research/" in e for e in errors))

    def test_archived_artifact_fails_when_commit_unresolvable(self) -> None:
        from unittest import mock

        (self.study / "study.yaml").write_text("artifacts:\n  dossier: .research/\n", encoding="utf-8")
        self.write_archive()
        with mock.patch.object(check_all, "commit_resolvable", return_value=False):
            errors = check_all.validate_artifacts(self.study)
        self.assertTrue(any("archive commit" in e for e in errors))

    def test_nested_archived_path_matches(self) -> None:
        record = {"removed": [{"path": "sources/docs"}]}
        self.assertTrue(check_all.is_archived("sources/docs/page.txt", record))
        self.assertTrue(check_all.is_archived("sources/docs", record))
        self.assertFalse(check_all.is_archived("sources/registry.yaml", record))
        self.assertFalse(check_all.is_archived("sources/docs", None))


class CommitResolvableTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_empty_sha_returns_none(self) -> None:
        self.assertIsNone(check_all.commit_resolvable(Path(self._tmp.name), ""))

    def test_non_repo_returns_none(self) -> None:
        self.assertIsNone(check_all.commit_resolvable(Path(self._tmp.name), "abc1234"))

    def test_real_repo_head_resolves(self) -> None:
        self.assertIs(check_all.commit_resolvable(ROOT, "HEAD"), True)

    def test_real_repo_bad_sha_unresolvable(self) -> None:
        self.assertIs(check_all.commit_resolvable(ROOT, "f" * 40), False)


class SnapshotWarningsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.study = Path(self._tmp.name) / "2026-08_test"
        (self.study / "sources").mkdir(parents=True)

    def write_registry(self, snapshot: str) -> None:
        (self.study / "sources" / "registry.yaml").write_text(
            "sources:\n  - key: a2026\n    status: noted\n"
            + (f"    snapshot: {snapshot}\n" if snapshot else ""),
            encoding="utf-8",
        )

    def test_cleaned_missing_snapshot_warns(self) -> None:
        (self.study / "study.yaml").write_text('cleaned: "2026-08-21"\n', encoding="utf-8")
        self.write_registry("sources/docs/a.txt")
        warnings = check_all.snapshot_warnings(self.study)
        self.assertEqual(len(warnings), 1)
        self.assertIn("historical", warnings[0])

    def test_cleaned_present_snapshot_silent(self) -> None:
        (self.study / "sources" / "docs").mkdir()
        (self.study / "sources" / "docs" / "a.txt").write_text("x\n", encoding="utf-8")
        (self.study / "study.yaml").write_text('cleaned: "2026-08-21"\n', encoding="utf-8")
        self.write_registry("sources/docs/a.txt")
        self.assertEqual(check_all.snapshot_warnings(self.study), [])

    def test_uncleaned_missing_snapshot_silent(self) -> None:
        (self.study / "study.yaml").write_text("status: drafting\n", encoding="utf-8")
        self.write_registry("sources/docs/a.txt")
        self.assertEqual(check_all.snapshot_warnings(self.study), [])


VALID_UNIT = (
    "---\n"
    "id: topic.concept\n"
    "question: Why?\n"
    "source_ids: [a2026]\n"
    "mastery:\n  last_assessed: '2026-08-21'\n  level: explained\n  help: none\n"
    "review:\n  next_due: '2026-09-21'\n"
    "---\n\n# Topic\n\nProse.\n"
)


class KnowledgeUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def write_page(self, name: str, text: str) -> None:
        (self.dir / name).write_text(text, encoding="utf-8")

    def test_parse_no_frontmatter(self) -> None:
        meta, error = check_all.parse_frontmatter("# Title\n")
        self.assertIsNone(meta)
        self.assertEqual(error, "")

    def test_parse_unclosed_frontmatter(self) -> None:
        _, error = check_all.parse_frontmatter("---\nid: x\n")
        self.assertIn("never closed", error)

    def test_parse_invalid_yaml(self) -> None:
        _, error = check_all.parse_frontmatter("---\nid: [unclosed\n---\n")
        self.assertIn("invalid YAML", error)

    def test_validate_valid_unit(self) -> None:
        meta, error = check_all.parse_frontmatter(VALID_UNIT)
        self.assertEqual(error, "")
        self.assertEqual(check_all.validate_knowledge_unit(meta), [])

    def test_validate_missing_id_fails(self) -> None:
        meta, _ = check_all.parse_frontmatter("---\nquestion: Why?\n---\n")
        errors = check_all.validate_knowledge_unit(meta)
        self.assertTrue(any("'id'" in e for e in errors))

    def test_validate_bad_date_fails(self) -> None:
        meta, _ = check_all.parse_frontmatter(
            "---\nid: a.b\nquestion: Why?\nreview:\n  next_due: not-a-date\n---\n"
        )
        errors = check_all.validate_knowledge_unit(meta)
        self.assertTrue(any("next_due" in e for e in errors))

    def test_check_knowledge_valid_page_passes(self) -> None:
        self.write_page("topic.md", VALID_UNIT)
        self.assertEqual(check_all.check_knowledge(self.dir), "PASS")

    def test_check_knowledge_legacy_page_warns_but_passes(self) -> None:
        self.write_page("legacy.md", "# Legacy\n\nNo frontmatter.\n")
        self.assertEqual(check_all.check_knowledge(self.dir), "PASS")

    def test_check_knowledge_malformed_fails(self) -> None:
        self.write_page("broken.md", "---\nid: [unclosed\n---\n")
        self.assertEqual(check_all.check_knowledge(self.dir), "FAIL")

    def test_check_knowledge_empty_not_assessed(self) -> None:
        self.assertEqual(check_all.check_knowledge(self.dir), "NOT_ASSESSED")


class HygieneWarnTests(unittest.TestCase):
    """Oversized tracked non-PDF files warn without failing hygiene."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        git = lambda *args: subprocess.run(  # noqa: E731
            ["git", "-C", str(self.repo), *args], check=True, capture_output=True, text=True
        )
        git("init")
        (self.repo / "big.bin").write_bytes(b"x" * (check_all.HYGIENE_SIZE_LIMIT + 1))
        git("add", "big.bin")
        git("-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-m", "oversized fixture")
        self._old_root = check_all.ROOT
        check_all.ROOT = self.repo
        self.addCleanup(setattr, check_all, "ROOT", self._old_root)

    def test_oversized_non_pdf_is_warn_not_fail(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            result = check_all.check_hygiene()
        self.assertEqual(result, "PASS")
        text = out.getvalue()
        self.assertIn("hygiene pdfs: PASS", text)
        self.assertIn("hygiene big.bin: WARN", text)


if __name__ == "__main__":
    unittest.main()
