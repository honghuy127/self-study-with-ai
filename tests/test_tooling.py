"""Tests for the repo's own machinery: generated docs, generated runtimes,
the Claude Code write guard, and the build wrapper.

These exist because each of these tools replaced something that used to be
kept in sync by hand and drifted.
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build  # noqa: E402
import contracts  # noqa: E402
import docsgen  # noqa: E402
import sync_runtimes  # noqa: E402


def quiet(fn, *args, **kwargs):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = fn(*args, **kwargs)
    return code, out.getvalue()


class ContractsTests(unittest.TestCase):
    def test_every_mode_has_states_gates_and_transitions(self) -> None:
        for mode in contracts.MODES:
            with self.subTest(mode=mode):
                self.assertIn(mode, contracts.STATES)
                self.assertIn(mode, contracts.MODE_GATES)
                self.assertIn(mode, contracts.TRANSITIONS)
                self.assertIn(mode, contracts.NEXT_ACTION)

    def test_transition_targets_are_all_valid_states(self) -> None:
        for mode, graph in contracts.TRANSITIONS.items():
            states = set(contracts.STATES[mode])
            for source, targets in graph.items():
                self.assertIn(source, states)
                for target in targets:
                    with self.subTest(mode=mode, edge=f"{source}->{target}"):
                        self.assertIn(target, states)

    def test_next_action_covers_every_state(self) -> None:
        for mode, states in contracts.STATES.items():
            for state in states:
                with self.subTest(mode=mode, state=state):
                    self.assertIn(state, contracts.NEXT_ACTION[mode])

    def test_entry_gates_reference_real_gates(self) -> None:
        for mode, entries in contracts.ENTRY_GATES.items():
            for target, gates in entries.items():
                self.assertIn(target, contracts.STATES[mode])
                for gate in gates:
                    with self.subTest(mode=mode, gate=gate):
                        self.assertIn(gate, contracts.MODE_GATES[mode])

    def test_gate_aliases_resolve(self) -> None:
        all_gates = {gate for gates in contracts.MODE_GATES.values() for gate in gates}
        for alias, resolved in contracts.GATE_ALIASES.items():
            with self.subTest(alias=alias):
                self.assertIn(resolved, all_gates)

    def test_every_intent_has_a_contract(self) -> None:
        for intent in contracts.INTENTS:
            with self.subTest(intent=intent):
                contract = contracts.INTENT_CONTRACTS[intent]
                self.assertTrue(contract.shape)
                self.assertTrue(contract.brief_questions)


class DocsGenerationTests(unittest.TestCase):
    def test_repo_docs_are_current(self) -> None:
        """README.md and AGENTS.md must match tools/contracts.py."""
        code, out = quiet(docsgen.main, ["--check"])
        self.assertEqual(code, 0, out)

    def test_rewrite_fills_a_marked_region(self) -> None:
        text = "before\n<!-- BEGIN GENERATED: modes -->\nstale\n<!-- END GENERATED: modes -->\nafter\n"
        new_text, names = docsgen.rewrite(text)
        self.assertEqual(names, ["modes"])
        self.assertNotIn("stale", new_text)
        self.assertIn("`delegated`", new_text)
        self.assertTrue(new_text.startswith("before\n"))
        self.assertTrue(new_text.endswith("after\n"))

    def test_rewrite_is_idempotent(self) -> None:
        text = "<!-- BEGIN GENERATED: dimensions -->\n\n<!-- END GENERATED: dimensions -->\n"
        once, _ = docsgen.rewrite(text)
        twice, _ = docsgen.rewrite(once)
        self.assertEqual(once, twice)

    def test_unknown_block_name_is_refused(self) -> None:
        with self.assertRaises(SystemExit):
            docsgen.rewrite("<!-- BEGIN GENERATED: nonsense -->\n<!-- END GENERATED: nonsense -->\n")

    def test_generated_tables_mention_every_mode_and_intent(self) -> None:
        modes = contracts.render_modes_table()
        for mode in contracts.MODES:
            self.assertIn(f"`{mode}`", modes)
        intents = contracts.render_intent_table()
        for intent in contracts.INTENTS:
            self.assertIn(f"`{intent}`", intents)


class RuntimeSyncTests(unittest.TestCase):
    def test_generated_runtimes_are_current(self) -> None:
        code, out = quiet(sync_runtimes.main, ["--check"])
        self.assertEqual(code, 0, out)

    def test_every_source_renders_into_both_harnesses(self) -> None:
        generated = sync_runtimes.generate()
        sources = sorted((sync_runtimes.SOURCE / "agents").glob("*.md"))
        for path in sources:
            for directory in (sync_runtimes.OPENCODE / "agents", sync_runtimes.CLAUDE / "agents"):
                with self.subTest(agent=path.stem, harness=directory.parent.name):
                    self.assertIn(directory / path.name, generated)

    def test_opencode_agent_carries_per_glob_edit_rules(self) -> None:
        meta, body = sync_runtimes.parse(sync_runtimes.SOURCE / "agents" / "summarizer.md")
        rendered = sync_runtimes.render_opencode_agent(meta, body)
        self.assertIn('"*": deny', rendered)
        self.assertIn('"studies/**/notes/**": allow', rendered)
        self.assertIn("mode: subagent", rendered)

    def test_claude_agent_carries_the_zone_in_prose(self) -> None:
        meta, body = sync_runtimes.parse(sync_runtimes.SOURCE / "agents" / "summarizer.md")
        rendered = sync_runtimes.render_claude_agent(meta, body)
        self.assertIn("name: summarizer", rendered)
        self.assertIn("Write zone", rendered)
        self.assertIn("`studies/**/notes/**`", rendered)

    def test_claude_tools_follow_the_neutral_permissions(self) -> None:
        self.assertNotIn("WebFetch", sync_runtimes.claude_tools({"webfetch": "deny", "websearch": "deny"}))
        self.assertIn("WebFetch", sync_runtimes.claude_tools({"webfetch": "allow", "websearch": "deny"}))
        self.assertIn("Bash", sync_runtimes.claude_tools({"bash": "ask"}))
        self.assertNotIn("Bash", sync_runtimes.claude_tools({"bash": "deny"}))

    def test_descriptions_with_colons_survive_the_round_trip(self) -> None:
        """The old hand-written command frontmatter was not valid YAML."""
        import yaml

        for path in sorted((sync_runtimes.CLAUDE / "commands").glob("*.md")):
            with self.subTest(command=path.stem):
                parts = path.read_text(encoding="utf-8").split("---", 2)
                meta = yaml.safe_load(parts[1])
                self.assertIsInstance(meta, dict)
                self.assertTrue(meta.get("description"))


class ZoneGuardTests(unittest.TestCase):
    def run_guard(self, tool: str, file_path: str) -> subprocess.CompletedProcess:
        payload = json.dumps({"tool_name": tool, "tool_input": {"file_path": file_path}})
        return subprocess.run(
            [sys.executable, str(ROOT / "tools" / "zone_guard.py")],
            input=payload,
            capture_output=True,
            text=True,
        )

    def test_blocks_editing_study_manifest(self) -> None:
        result = self.run_guard("Edit", "studies/2026-08_x/study.yaml")
        self.assertEqual(result.returncode, 2)
        self.assertIn("tools/study.py", result.stderr)

    def test_blocks_editing_events_log(self) -> None:
        self.assertEqual(self.run_guard("Write", "studies/2026-08_x/events.jsonl").returncode, 2)

    def test_blocks_editing_archive_record(self) -> None:
        self.assertEqual(self.run_guard("Edit", "examples/2026-08_x/archive.yaml").returncode, 2)

    def test_blocks_writing_a_pdf(self) -> None:
        self.assertEqual(self.run_guard("Write", "studies/2026-08_x/sources/pdfs/paper.pdf").returncode, 2)

    def test_allows_normal_study_files(self) -> None:
        for path in (
            "studies/2026-08_x/notes/source.md",
            "studies/2026-08_x/report/main.tex",
            "studies/2026-08_x/learning/journal.md",
            "shared/knowledge/attention-scale.md",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.run_guard("Edit", path).returncode, 0)

    def test_ignores_non_write_tools(self) -> None:
        self.assertEqual(self.run_guard("Read", "studies/2026-08_x/study.yaml").returncode, 0)

    def test_handles_windows_separators(self) -> None:
        self.assertEqual(self.run_guard("Edit", r"studies\2026-08_x\study.yaml").returncode, 2)

    def test_survives_malformed_input(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "zone_guard.py")],
            input="not json",
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)


class BuildWrapperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="build-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_missing_main_tex_is_reported(self) -> None:
        (self.tmp / "report").mkdir()
        self.assertEqual(build.build(self.tmp, "report"), 1)

    def test_missing_study_dir_is_reported(self) -> None:
        self.assertEqual(build.main(["report", str(self.tmp / "nope")]), 2)

    def test_slides_fall_back_to_the_report_bibliography(self) -> None:
        (self.tmp / "slides").mkdir()
        (self.tmp / "report").mkdir()
        (self.tmp / "report" / "refs.bib").write_text("", encoding="utf-8")
        self.assertEqual(build.bib_search_path(self.tmp, "slides"), str((self.tmp / "report").resolve()))

    def test_slides_prefer_their_own_bibliography(self) -> None:
        (self.tmp / "slides").mkdir()
        (self.tmp / "slides" / "refs.bib").write_text("", encoding="utf-8")
        (self.tmp / "report").mkdir()
        (self.tmp / "report" / "refs.bib").write_text("", encoding="utf-8")
        self.assertEqual(build.bib_search_path(self.tmp, "slides"), str((self.tmp / "slides").resolve()))

    def test_report_does_not_borrow_a_slides_bibliography(self) -> None:
        (self.tmp / "slides").mkdir()
        (self.tmp / "slides" / "refs.bib").write_text("", encoding="utf-8")
        (self.tmp / "report").mkdir()
        self.assertIsNone(build.bib_search_path(self.tmp, "report"))


class NoShellScriptsTests(unittest.TestCase):
    def test_repo_ships_no_shell_scripts(self) -> None:
        """The build and dossier wrappers are Python so Windows works too."""
        found = [p.relative_to(ROOT).as_posix() for p in ROOT.glob("tools/**/*.sh")]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
