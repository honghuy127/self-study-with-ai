from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import knowledge  # noqa: E402

UNIT = """---
id: {id}
question: {question}
prerequisites: {prereqs}
source_ids: []
tags: {tags}
review:
  next_due: "{due}"
superseded_by: "{superseded}"
---

# {title}

## Answer

{body}
"""


def write_unit(directory: Path, unit_id: str, question: str = "Why?", prereqs: str = "[]",
               tags: str = "[]", due: str = "", superseded: str = "", body: str = "Because.") -> Path:
    path = directory / f"{unit_id.replace('.', '-')}.md"
    path.write_text(
        UNIT.format(id=unit_id, question=question, prereqs=prereqs, tags=tags, due=due,
                    superseded=superseded, title=unit_id, body=body),
        encoding="utf-8",
    )
    return path


def quiet(fn, *args, **kwargs):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = fn(*args, **kwargs)
    return code, out.getvalue()


class KnowledgeBaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="knowledge-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.base = self.tmp / "knowledge"
        self.base.mkdir()
        self._old = knowledge.KNOWLEDGE
        knowledge.KNOWLEDGE = self.base
        self.addCleanup(setattr, knowledge, "KNOWLEDGE", self._old)

    def test_loads_units_and_reads_frontmatter(self) -> None:
        write_unit(self.base, "attention.scale", question="Why 1/sqrt(d_k)?")
        units = knowledge.load_units(self.base)
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].id, "attention.scale")
        self.assertEqual(units[0].question, "Why 1/sqrt(d_k)?")

    def test_index_writes_both_views_and_check_detects_staleness(self) -> None:
        write_unit(self.base, "attention.scale")
        code, _ = quiet(knowledge.main, ["index"])
        self.assertEqual(code, 0)
        self.assertTrue((self.base / "INDEX.md").is_file())
        payload = json.loads((self.base / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["units"][0]["id"], "attention.scale")

        code, _ = quiet(knowledge.main, ["index", "--check"])
        self.assertEqual(code, 0)
        write_unit(self.base, "softmax.saturation")
        code, out = quiet(knowledge.main, ["index", "--check"])
        self.assertEqual(code, 1)
        self.assertIn("stale", out)

    def test_generated_files_are_not_treated_as_units(self) -> None:
        write_unit(self.base, "attention.scale")
        quiet(knowledge.main, ["index"])
        self.assertEqual([u.id for u in knowledge.load_units(self.base)], ["attention.scale"])

    def test_link_check_reports_dangling_prerequisites(self) -> None:
        write_unit(self.base, "attention.scale", prereqs="[linear.algebra]")
        code, out = quiet(knowledge.main, ["link"])
        self.assertEqual(code, 1)
        self.assertIn("linear.algebra", out)

    def test_link_check_reports_dangling_wikilinks(self) -> None:
        write_unit(self.base, "attention.scale", body="See [[nowhere.at.all]].")
        code, out = quiet(knowledge.main, ["link"])
        self.assertEqual(code, 1)
        self.assertIn("nowhere.at.all", out)

    def test_link_check_reports_duplicate_ids(self) -> None:
        write_unit(self.base, "attention.scale")
        (self.base / "copy.md").write_text(
            (self.base / "attention-scale.md").read_text(encoding="utf-8"), encoding="utf-8"
        )
        code, out = quiet(knowledge.main, ["link"])
        self.assertEqual(code, 1)
        self.assertIn("duplicate id", out)

    def test_link_check_passes_on_a_resolvable_graph(self) -> None:
        write_unit(self.base, "linear.algebra")
        write_unit(self.base, "attention.scale", prereqs="[linear.algebra]", body="See [[linear.algebra]].")
        code, _ = quiet(knowledge.main, ["link"])
        self.assertEqual(code, 0)

    def test_search_ranks_the_question_above_the_body(self) -> None:
        write_unit(self.base, "attention.scale", question="Why divide by sqrt of the key dimension?")
        write_unit(self.base, "unrelated.topic", question="What is a tokenizer?", body="mentions dimension once")
        code, out = quiet(knowledge.main, ["search", "key", "dimension", "--json"])
        self.assertEqual(code, 0)
        results = json.loads(out)
        self.assertEqual(results[0]["id"], "attention.scale")

    def test_search_reports_nothing_when_the_base_is_empty(self) -> None:
        code, out = quiet(knowledge.main, ["search", "anything"])
        self.assertEqual(code, 0)
        self.assertIn("no existing unit", out)

    def test_new_rejects_duplicate_ids(self) -> None:
        quiet(knowledge.main, ["new", "attention.scale", "--question", "Why?"])
        with self.assertRaises(SystemExit):
            knowledge.main(["new", "attention.scale", "--question", "Why again?"])

    def test_new_rejects_invalid_ids(self) -> None:
        with self.assertRaises(SystemExit):
            knowledge.main(["new", "Attention Scale", "--question", "Why?"])

    def test_supersede_marks_the_old_unit_and_keeps_it(self) -> None:
        write_unit(self.base, "old.unit")
        write_unit(self.base, "new.unit")
        code, _ = quiet(knowledge.main, ["supersede", "old.unit", "new.unit"])
        self.assertEqual(code, 0)
        units = knowledge.by_id(knowledge.load_units(self.base))
        self.assertEqual(units["old.unit"].superseded_by, "new.unit")
        code, _ = quiet(knowledge.main, ["link"])
        self.assertEqual(code, 0)

    def test_supersede_requires_the_replacement_to_exist(self) -> None:
        write_unit(self.base, "old.unit")
        with self.assertRaises(SystemExit):
            knowledge.main(["supersede", "old.unit", "does.not.exist"])

    def test_dir_flag_redirects_every_command(self) -> None:
        other = self.tmp / "elsewhere"
        other.mkdir()
        write_unit(other, "over.there")
        code, out = quiet(knowledge.main, ["--dir", str(other), "search", "over", "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)[0]["id"], "over.there")


class ShippedKnowledgeBaseTests(unittest.TestCase):
    """The example study must demonstrate its own done-time contract.

    AGENTS.md says a finished study with no knowledge unit has produced a
    document, not knowledge. examples/ is the one study that ships, so it is
    the only place a reader can see that step, and the only knowledge base CI
    can validate on a fresh clone.
    """

    BASE = ROOT / "examples" / "knowledge"

    def test_the_example_study_distilled_into_a_unit(self) -> None:
        units = knowledge.load_units(self.BASE)
        self.assertTrue(units, "examples/knowledge holds no units")
        for unit in units:
            with self.subTest(unit=unit.id):
                self.assertTrue(unit.id)
                self.assertTrue(unit.question)

    def test_units_name_the_study_they_came_from(self) -> None:
        for unit in knowledge.load_units(self.BASE):
            with self.subTest(unit=unit.id):
                studies = unit.list_field("studies")
                self.assertTrue(studies, f"{unit.id} does not say which study produced it")
                for study_id in studies:
                    self.assertTrue(
                        (ROOT / "examples" / study_id).is_dir(),
                        f"{unit.id} names study {study_id}, which does not ship",
                    )

    def test_units_cite_sources_the_study_registered(self) -> None:
        import yaml

        for unit in knowledge.load_units(self.BASE):
            for study_id in unit.list_field("studies"):
                registry = ROOT / "examples" / study_id / "sources" / "registry.yaml"
                data = yaml.safe_load(registry.read_text(encoding="utf-8"))
                registered = {e["key"] for e in data["sources"]}
                for source in unit.list_field("source_ids"):
                    with self.subTest(unit=unit.id, source=source):
                        self.assertIn(source, registered)

    def test_index_is_current(self) -> None:
        code, out = quiet(knowledge.main, ["--dir", str(self.BASE), "index", "--check"])
        self.assertEqual(code, 0, out)

    def test_links_resolve(self) -> None:
        code, out = quiet(knowledge.main, ["--dir", str(self.BASE), "link", "--check"])
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
