#!/usr/bin/env python3
"""Single source of truth for the study contracts.

The mode dimensions, lifecycle states, transition graphs, entry gates, and
intent contracts live here and nowhere else. `study.py` enforces them,
`new_study.py` scaffolds from them, `check_all.py` validates against them,
`lint_report.py` checks intent-required sections, and `docsgen.py` renders
the README and AGENTS.md tables from them. When a contract changes, it
changes once and every consumer follows.

This module is standard-library only so every tool can import it cheaply.
"""
from __future__ import annotations

from dataclasses import dataclass, field

SCHEMA_VERSION = 2

MODES = ("interactive", "delegated", "paper-reading")
INTENTS = ("understand", "solve", "build", "compare", "decide", "refresh", "survey")
ASSURANCES = ("quick", "grounded", "audited")
METHODOLOGIES = ("source-only", "static-code", "experimental", "mixed")
DELIVERABLES = ("learning-note", "implementation", "decision-brief", "report", "slides", "none")
REPORT_STYLES = ("neurips", "plain")
VERDICTS = ("PASS", "CONDITIONAL", "FAIL", "BLOCKED", "NOT_ASSESSED")

EXPERIMENTAL_METHODOLOGIES = ("experimental", "mixed")
DEPRECATED_FIELDS = ("track", "depth")

# Ordered pipelines, used for docs and for the `status` next-action hints.
STATES = {
    "interactive": ("scoped", "diagnosing", "learning", "practicing", "assessing", "retained"),
    "delegated": ("proposed", "gathering", "summarizing", "experimenting", "drafting", "review", "done"),
    "paper-reading": ("proposed", "gathering", "analyzing", "presenting", "review", "done"),
}

MODE_GATES = {
    "delegated": ("sources_approved", "notes_approved", "experiments_approved", "draft_approved", "review_signed_off"),
    "interactive": ("scope_approved", "evidence_approved", "experiments_approved", "mastery_approved"),
    "paper-reading": ("paper_approved", "analysis_approved", "deck_approved", "review_signed_off"),
}

# One state engine, three allowed transition graphs. Backward edges exist on
# purpose: assessment can return to practice, review can return to drafting,
# and a finished non-interactive study can reopen into review for refresh work.
TRANSITIONS = {
    "delegated": {
        "proposed": {"gathering"},
        "gathering": {"summarizing", "proposed"},
        "summarizing": {"experimenting", "drafting", "gathering"},
        "experimenting": {"drafting", "summarizing"},
        "drafting": {"review", "summarizing", "experimenting"},
        "review": {"done", "gathering", "summarizing", "experimenting", "drafting"},
        "done": {"review"},
    },
    "interactive": {
        "scoped": {"diagnosing"},
        "diagnosing": {"learning", "scoped"},
        "learning": {"practicing", "diagnosing"},
        "practicing": {"assessing", "learning"},
        "assessing": {"retained", "practicing", "learning"},
        "retained": set(),
    },
    "paper-reading": {
        "proposed": {"gathering"},
        "gathering": {"analyzing", "proposed"},
        "analyzing": {"presenting", "gathering"},
        "presenting": {"review", "analyzing"},
        "review": {"done", "gathering", "analyzing", "presenting"},
        "done": {"review"},
    },
}

# Gates that must be approved before entering a state. The experiments gate
# only binds when the methodology runs experiments (see study.py).
ENTRY_GATES = {
    "delegated": {
        "drafting": ("sources_approved", "notes_approved"),
        "review": ("draft_approved",),
        "done": ("review_signed_off",),
    },
    "interactive": {
        "diagnosing": ("scope_approved",),
        "learning": ("evidence_approved",),
        "retained": ("mastery_approved",),
    },
    "paper-reading": {
        "analyzing": ("paper_approved",),
        "presenting": ("analysis_approved",),
        "review": ("deck_approved",),
        "done": ("review_signed_off",),
    },
}

GATE_ALIASES = {
    "sources": "sources_approved",
    "notes": "notes_approved",
    "experiments": "experiments_approved",
    "draft": "draft_approved",
    "review": "review_signed_off",
    "scope": "scope_approved",
    "evidence": "evidence_approved",
    "mastery": "mastery_approved",
    "paper": "paper_approved",
    "analysis": "analysis_approved",
    "deck": "deck_approved",
}

NEXT_ACTION = {
    "delegated": {
        "proposed": "fill brief.md, then /gather and stop for sources approval",
        "gathering": "register sources, then stop for sources approval",
        "summarizing": "note every registered source, then stop for notes approval",
        "experimenting": "run the approved experiments, then stop for experiments approval",
        "drafting": "synthesize and draft the report, then stop for draft approval",
        "review": "independent review, then stop for review sign-off",
        "done": "merge shared/ knowledge, then tools/cleanup_study.py; reopen later via study.py reopen",
    },
    "interactive": {
        "scoped": "record the unaided baseline in learning/baseline.md, then approve scope",
        "diagnosing": "plan the concept path in learning/map.md from the baseline",
        "learning": "tutor one link at a time; journal every exchange in learning/journal.md",
        "practicing": "administer near and transfer practice (study practice)",
        "assessing": "administer the mastery task unaided (study assess), then approve mastery",
        "retained": "distill outputs/learning-note.md and schedule the delayed review (study revisit)",
    },
    "paper-reading": {
        "proposed": "fill the exact target-paper and talk contracts, then /read-paper",
        "gathering": "verify one target paper and context packet, then stop for paper approval",
        "analyzing": "produce the anchored paper analysis, then stop for analysis approval",
        "presenting": "storyboard, build, lint, and render the deck, then stop for deck approval",
        "review": "independently audit slide claims and rendered output, then stop for review sign-off",
        "done": "merge reusable knowledge, then tools/cleanup_study.py; reopen later via study.py reopen",
    },
}

MODE_PURPOSE = {
    "interactive": "the agent tutors you to an unaided mastery demonstration",
    "delegated": "agents investigate and return a traceable report",
    "paper-reading": "agents analyze one approved paper into a comprehensive deck",
}


@dataclass(frozen=True)
class IntentContract:
    """What an intent obliges the study to produce.

    `shape` states how the question and synthesis are organized; agents read
    it from `study.py status`. `brief_questions` seeds the brief's Questions
    section at scaffold time. `required_sections` is what
    `lint_report.py` enforces in the deliverable: a pair of (label, regex)
    where the regex is searched case-insensitively against the LaTeX source.
    An intent with no required sections makes no structural promise.
    """

    shape: str
    brief_questions: tuple[str, ...]
    required_sections: tuple[tuple[str, str], ...] = field(default=())


INTENT_CONTRACTS = {
    "understand": IntentContract(
        shape="explain a mechanism from first principles; the answer is a derivation or causal account",
        brief_questions=(
            "- Primary question: [what mechanism must you be able to explain, in one sentence]",
            "- What would count as understanding it: [the account you could not give today]",
        ),
    ),
    "solve": IntentContract(
        shape="resolve one concrete problem; the answer is an approach with its failure conditions",
        brief_questions=(
            "- Primary question: [the problem to solve, stated so a solution is checkable]",
            "- Constraints the solution must respect: [budget, latency, compatibility, ...]",
        ),
        required_sections=(("approach or solution", r"\\section\*?\{[^}]*(solution|approach)"),),
    ),
    "build": IntentContract(
        shape="produce something runnable; the answer is an implementation plus what it was verified against",
        brief_questions=(
            "- Primary question: [what must exist and work at the end]",
            "- Acceptance check: [how you will know the build is correct]",
        ),
        required_sections=(("implementation", r"\\section\*?\{[^}]*implementation"),),
    ),
    "compare": IntentContract(
        shape="place systems side by side on fixed dimensions; the answer is a matrix, not a narrative",
        brief_questions=(
            "- Primary question: [what choice or contrast is being resolved]",
            "- Comparison dimensions: [the fixed axes every system is scored on]",
        ),
        required_sections=(
            ("comparison section", r"\\section\*?\{[^}]*(comparison|compar)"),
            ("comparison table", r"\\begin\{(tabular|tabularx|longtable)"),
        ),
    ),
    "decide": IntentContract(
        shape="reach a defensible decision; the answer names the option taken and what would reverse it",
        brief_questions=(
            "- Primary question: [the decision to be made, with the options on the table]",
            "- Reversal condition: [what evidence would change the decision later]",
        ),
        required_sections=(("recommendation", r"\\section\*?\{[^}]*(recommendation|decision)"),),
    ),
    "refresh": IntentContract(
        shape="re-establish something you once knew; the answer is a delta against prior understanding",
        brief_questions=(
            "- Primary question: [what you once knew and need current again]",
            "- Prior understanding to check against: [shared/knowledge page or earlier study]",
        ),
    ),
    "survey": IntentContract(
        shape="map a literature or landscape; the answer is organized coverage with its limits stated",
        brief_questions=(
            "- Primary question: [what the landscape must be mapped for]",
            "- Coverage boundary: [venues, years, and what is deliberately excluded]",
        ),
        required_sections=(("coverage or scope", r"\\section\*?\{[^}]*(coverage|scope|method)"),),
    ),
}

DIMENSIONS = (
    ("Intent", INTENTS, "Question and synthesis shape; enforced by lint_report.py where it promises a section"),
    ("Assurance", ASSURANCES, "Verification depth; `audited` adds a claims dossier and independent review"),
    ("Methodology", METHODOLOGIES, "What counts as evidence; only experimental and mixed enter `experimenting`"),
    ("Deliverables", DELIVERABLES, "Outputs to scaffold"),
)


def gates_for(mode: str) -> tuple[str, ...]:
    return MODE_GATES[mode]


def states_for(mode: str) -> tuple[str, ...]:
    return STATES[mode]


def allowed_targets(mode: str, status: str) -> set[str]:
    return TRANSITIONS.get(mode, {}).get(status, set())


def required_gates(mode: str, target: str, methodology: str, gates: dict) -> list[str]:
    """Gates that must already be true before entering `target`.

    The experiments gate binds on entry to delegated drafting only when the
    methodology runs experiments, and on entry to interactive `retained`
    whenever the study carries a live (non-`n_a`) experiments gate.
    """
    required = list(ENTRY_GATES.get(mode, {}).get(target, ()))
    if target == "drafting" and methodology in EXPERIMENTAL_METHODOLOGIES:
        required.append("experiments_approved")
    if target == "retained" and gates.get("experiments_approved") != "n_a":
        required.append("experiments_approved")
    return required


# --- markdown rendering, consumed by docsgen.py ------------------------------


def _pipeline(mode: str) -> str:
    return " --> ".join(STATES[mode])


def render_pipelines() -> str:
    width = max(len(m) for m in MODES)
    lines = ["```text"]
    for mode in ("interactive", "delegated", "paper-reading"):
        lines.append(f"{mode + ':':{width + 1}} {_pipeline(mode)}")
    lines.append("```")
    return "\n".join(lines)


def render_modes_table() -> str:
    rows = ["| Mode | What it does | Gates, in order |", "|---|---|---|"]
    for mode in MODES:
        gates = ", ".join(f"`{g}`" for g in MODE_GATES[mode])
        rows.append(f"| `{mode}` | {MODE_PURPOSE[mode]} | {gates} |")
    return "\n".join(rows)


def render_dimensions_table() -> str:
    rows = ["| Dimension | Values | Controls |", "|---|---|---|"]
    for name, values, controls in DIMENSIONS:
        rendered = ", ".join(f"`{v}`" for v in values)
        rows.append(f"| {name} | {rendered} | {controls} |")
    return "\n".join(rows)


def render_intent_table() -> str:
    rows = ["| Intent | Shape of the answer | Deliverable must contain |", "|---|---|---|"]
    for name in INTENTS:
        contract = INTENT_CONTRACTS[name]
        required = ", ".join(label for label, _ in contract.required_sections) or "no structural requirement"
        rows.append(f"| `{name}` | {contract.shape} | {required} |")
    return "\n".join(rows)


def render_transitions_list() -> str:
    lines = []
    for mode in MODES:
        edges = []
        for source in STATES[mode]:
            targets = sorted(TRANSITIONS[mode].get(source, set()))
            if targets:
                edges.append(f"`{source}`->{'|'.join(targets)}")
        lines.append(f"- **{mode}**: " + ", ".join(edges))
    return "\n".join(lines)


def render_entry_gates_list() -> str:
    lines = []
    for mode in MODES:
        parts = []
        for target, gates in ENTRY_GATES[mode].items():
            parts.append(f"`{target}` needs {', '.join(gates)}")
        extra = {
            "delegated": "; `drafting` also needs `experiments_approved` on experimental and mixed methodologies",
            "interactive": "; `retained` also needs `experiments_approved` whenever that gate is not `n_a`",
            "paper-reading": "",
        }[mode]
        lines.append(f"- **{mode}**: " + "; ".join(parts) + extra)
    return "\n".join(lines)


BLOCKS = {
    "pipelines": render_pipelines,
    "modes": render_modes_table,
    "dimensions": render_dimensions_table,
    "intents": render_intent_table,
    "transitions": render_transitions_list,
    "entry-gates": render_entry_gates_list,
}
