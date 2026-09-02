"""The shipped audited study must keep auditing, on every platform.

`audit` was the last check group that never ran: no study in the repo used
audited assurance, so `audit_research.py`, the script enforcing the
claim-to-evidence traceability the README sells as the epistemic layer, was
exercised by nothing. examples/2026-08_attention-logit-variance closes that,
and these tests guard the two ways a committed dossier silently rots:

  * absolute paths, which capture_run.py records by default and which are
    meaningless on any other machine;
  * line-ending translation, which would change the byte content of the
    hashed artifacts on checkout and make the dossier look tampered with.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDY = ROOT / "examples" / "2026-08_attention-logit-variance"
DOSSIER = STUDY / ".research"


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class AuditedExampleTests(unittest.TestCase):
    def test_audit_reports_no_errors(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "research.py"), str(STUDY), "audit_research.py"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("errors=0", proc.stdout)

    def test_dossier_validates(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "research.py"), str(STUDY), "research_state.py", "validate"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def recorded_paths(self) -> list[tuple[str, str]]:
        """Every path a committed dossier records, as (where, value)."""
        found: list[tuple[str, str]] = []
        for manifest_path in sorted((DOSSIER / "runs").glob("*/manifest.json")):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for group in ("configs", "inputs", "outputs"):
                for record in manifest.get(group) or []:
                    found.append((f"{manifest_path.parent.name}/{group}", record["path"]))
            for key in manifest.get("versions") or {}:
                found.append((f"{manifest_path.parent.name}/versions", key))
        for record in jsonl(DOSSIER / "experiments.jsonl"):
            found.append((f"experiments.jsonl/{record['run_id']}", record["manifest_path"]))
        return found

    def test_recorded_paths_are_relative(self) -> None:
        """An absolute path in a committed manifest is portable to nowhere."""
        paths = self.recorded_paths()
        self.assertTrue(paths)
        for where, value in paths:
            with self.subTest(where=where, path=value):
                self.assertFalse(
                    Path(value).is_absolute(),
                    f"{value} is absolute; run tools/research.py <study> relativize",
                )

    def test_recorded_paths_use_posix_separators(self) -> None:
        """A backslash separator is a filename character on Linux.

        This is not pedantry: a relative path recorded as
        `.research\\runs\\x\\manifest.json` resolves on Windows and reads as a
        single strange filename on Linux, so the manifest looks unledgered and
        every claim linking that run fails behind it. That exact bug shipped
        once and was invisible until CI ran on Linux.
        """
        for where, value in self.recorded_paths():
            with self.subTest(where=where, path=value):
                self.assertNotIn("\\", value, f"{value} uses Windows separators")

    def test_recorded_paths_resolve_to_real_files(self) -> None:
        for where, value in self.recorded_paths():
            with self.subTest(where=where, path=value):
                self.assertTrue((STUDY / value).is_file(), f"{value} does not resolve under the study")

    def test_recorded_hashes_match_the_committed_files(self) -> None:
        """Catches line-ending translation as well as edited artifacts."""
        checked = 0
        for manifest_path in sorted((DOSSIER / "runs").glob("*/manifest.json")):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for group in ("inputs", "outputs"):
                for record in manifest.get(group) or []:
                    if not record.get("exists"):
                        continue
                    path = STUDY / record["path"]
                    with self.subTest(path=record["path"]):
                        self.assertTrue(path.is_file(), f"{path} is missing")
                        data = path.read_bytes()
                        self.assertEqual(len(data), record["size_bytes"], "size changed (line endings?)")
                        self.assertEqual(hashlib.sha256(data).hexdigest(), record["sha256"])
                        checked += 1
        self.assertGreaterEqual(checked, 4, "expected both runs to record an input and an output")

    def test_every_reported_claim_has_an_independent_verification_run(self) -> None:
        run_ids = {record["run_id"] for record in jsonl(DOSSIER / "experiments.jsonl")}
        claims = jsonl(DOSSIER / "claims.jsonl")
        self.assertTrue(claims)
        for claim in claims:
            with self.subTest(claim=claim["id"]):
                self.assertEqual(claim["lifecycle_state"], "reported")
                verification = set(claim.get("verification_run_ids") or [])
                linked = set(claim.get("run_ids") or [])
                self.assertTrue(verification, "reported empirical claim without an independent check")
                self.assertFalse(verification & linked, "verification run is not independent")
                self.assertTrue(verification <= run_ids)
                self.assertTrue(linked <= run_ids)

    def test_evidence_and_claims_link_both_ways(self) -> None:
        evidence = {record["id"]: record for record in jsonl(DOSSIER / "evidence.jsonl")}
        for claim in jsonl(DOSSIER / "claims.jsonl"):
            for source_id in claim.get("evidence_ids") or []:
                with self.subTest(claim=claim["id"], evidence=source_id):
                    self.assertIn(source_id, evidence)
                    self.assertIn(claim["id"], evidence[source_id].get("supports") or [])

    def test_reported_numbers_exist_in_the_result_artifacts(self) -> None:
        """Every figure in the report must be readable out of a run output."""
        report = (STUDY / "report" / "main.tex").read_text(encoding="utf-8")
        results = json.loads(
            (STUDY / "experiments" / "logit-variance" / "results" / "main.json").read_text(encoding="utf-8")
        )
        for row in results["measurements"]:
            for field in ("variance_unscaled", "variance_scaled", "mean_max_prob_unscaled", "mean_max_prob_scaled"):
                with self.subTest(d_k=row["d_k"], field=field):
                    self.assertIn(str(row[field]), report, f"{field} at d_k={row['d_k']} is not in the report")

    @unittest.skipUnless(os.environ.get("SSWA_REPRODUCE") == "1", "set SSWA_REPRODUCE=1 to rerun the experiment")
    def test_experiment_is_deterministic_from_its_seed(self) -> None:
        """Rerun the recorded command and compare bytes.

        This is the claim the experiment README makes to anyone trying to
        reproduce the study, so it should be the repo's problem when it stops
        being true, not the reader's.

        It costs about 105 seconds, so it is opt-in rather than paid on every
        matrix leg: CI runs it once, on Linux. The cheaper hash check above
        still runs everywhere and catches an edited or re-encoded artifact.
        """
        import tempfile

        script = STUDY / "experiments" / "logit-variance" / "run.py"
        expected = (STUDY / "experiments" / "logit-variance" / "results" / "main.json").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "main.json"
            proc = subprocess.run(
                [sys.executable, str(script), "--seed", "20260901", "--out", str(out), "--label", "main measurement"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertEqual(out.read_bytes(), expected, "the recorded run is no longer reproducible")


class RelativizeTests(unittest.TestCase):
    """The portability fix must be a tool, not a thing someone remembered.

    capture_run.py records absolute paths by design. tools/research.py rewrites
    them after every capture; these tests cover the rewrite itself, since a
    dossier that skips it audits on exactly one machine.
    """

    def setUp(self) -> None:
        import shutil
        import tempfile

        self.tmp = Path(tempfile.mkdtemp(prefix="relativize-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.study = self.tmp / "2026-08_demo"
        (self.study / ".research" / "runs" / "run-a").mkdir(parents=True)
        (self.study / "experiments").mkdir()
        self.artifact = self.study / "experiments" / "out.json"
        self.artifact.write_text("{}\n", encoding="utf-8")
        self.manifest = self.study / ".research" / "runs" / "run-a" / "manifest.json"
        self.manifest.write_text(
            json.dumps(
                {
                    "run_id": "run-a",
                    "inputs": [{"path": str(self.artifact.resolve()), "exists": True}],
                    "outputs": [{"path": str(self.artifact.resolve()), "exists": True}],
                    "versions": {str(self.artifact.resolve()): "v1"},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (self.study / ".research" / "experiments.jsonl").write_text(
            json.dumps({"run_id": "run-a", "manifest_path": str(self.manifest.resolve())}) + "\n",
            encoding="utf-8",
        )

    def relativize(self) -> int:
        sys.path.insert(0, str(ROOT / "tools"))
        import research

        return research.relativize(self.study)

    def test_rewrites_manifest_and_ledger_paths(self) -> None:
        changed = self.relativize()
        self.assertGreaterEqual(changed, 4)
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual(manifest["inputs"][0]["path"], "experiments/out.json")
        self.assertEqual(manifest["outputs"][0]["path"], "experiments/out.json")
        self.assertEqual(list(manifest["versions"]), ["experiments/out.json"])
        ledger = jsonl(self.study / ".research" / "experiments.jsonl")
        self.assertEqual(ledger[0]["manifest_path"], ".research/runs/run-a/manifest.json")

    def test_is_idempotent(self) -> None:
        self.relativize()
        self.assertEqual(self.relativize(), 0)

    def test_normalizes_windows_separators_in_an_already_relative_path(self) -> None:
        """capture_run.py can record a relative path with backslashes."""
        ledger = self.study / ".research" / "experiments.jsonl"
        ledger.write_text(
            json.dumps({"run_id": "run-a", "manifest_path": ".research\\runs\\run-a\\manifest.json"}) + "\n",
            encoding="utf-8",
        )
        self.relativize()
        self.assertEqual(
            jsonl(ledger)[0]["manifest_path"], ".research/runs/run-a/manifest.json"
        )

    def test_leaves_paths_outside_the_study_alone(self) -> None:
        """A shared dataset elsewhere on disk cannot be made study-relative."""
        outside = self.tmp / "shared-dataset.bin"
        outside.write_bytes(b"x")
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest["inputs"].append({"path": str(outside.resolve()), "exists": True})
        self.manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        self.relativize()
        rewritten = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual(rewritten["inputs"][1]["path"], str(outside.resolve()))

    def test_writes_lf_so_hashes_stay_stable(self) -> None:
        self.relativize()
        self.assertNotIn(b"\r\n", self.manifest.read_bytes())
        self.assertNotIn(b"\r\n", (self.study / ".research" / "experiments.jsonl").read_bytes())

    def test_check_all_warns_about_absolute_paths(self) -> None:
        sys.path.insert(0, str(ROOT / "tools"))
        import check_all

        offenders = check_all.absolute_recorded_paths(self.study)
        self.assertTrue(offenders)
        self.relativize()
        self.assertEqual(check_all.absolute_recorded_paths(self.study), [])


class LineEndingProtectionTests(unittest.TestCase):
    """Hash-verified artifacts must be exempt from line-ending translation.

    Without this, the recorded sha256 matches on the machine that captured it
    and fails everywhere else, which reads as a tampered dossier rather than
    as a checkout artifact.
    """

    def attributes(self, path: str) -> str:
        proc = subprocess.run(
            ["git", "check-attr", "text", "--", path], cwd=ROOT, capture_output=True, text=True
        )
        return proc.stdout.strip()

    def test_hashed_artifacts_are_marked_unset(self) -> None:
        for path in (
            "examples/2026-08_attention-logit-variance/experiments/logit-variance/run.py",
            "examples/2026-08_attention-logit-variance/experiments/logit-variance/results/main.json",
            "examples/2026-08_attention-logit-variance/.research/runs/run-main-20260902/manifest.json",
        ):
            with self.subTest(path=path):
                self.assertIn("text: unset", self.attributes(path))

    def test_the_rule_also_covers_opted_in_user_studies(self) -> None:
        """studies/ is gitignored, but opting in must not reopen the trap."""
        self.assertIn("text: unset", self.attributes("studies/2026-08_x/experiments/e/run.py"))
        self.assertIn("text: unset", self.attributes("studies/2026-08_x/.research/state.json"))

    def test_prose_is_still_normalized(self) -> None:
        self.assertIn("text: auto", self.attributes("README.md"))


if __name__ == "__main__":
    unittest.main()
