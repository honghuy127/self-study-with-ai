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

    def test_recorded_paths_are_relative(self) -> None:
        """An absolute path in a committed manifest is portable to nowhere."""
        for manifest_path in sorted((DOSSIER / "runs").glob("*/manifest.json")):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for group in ("configs", "inputs", "outputs"):
                for record in manifest.get(group) or []:
                    with self.subTest(run=manifest_path.parent.name, path=record["path"]):
                        self.assertFalse(
                            Path(record["path"]).is_absolute(),
                            f"{record['path']} is absolute; rerun the relativizer",
                        )
        for record in jsonl(DOSSIER / "experiments.jsonl"):
            with self.subTest(run=record["run_id"]):
                self.assertFalse(Path(record["manifest_path"]).is_absolute())

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


if __name__ == "__main__":
    unittest.main()
