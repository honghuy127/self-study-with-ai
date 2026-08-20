# r1 response (writer)

Date: 2026-08-20. Fixes against `reviews/r1-agent.md` (verdict CONDITIONAL,
1 major, 13 minors). Post-fix state: `tools/lint_report.py` clean;
`check_latex_log.py` status pass (zero warnings); PDF 6 pages.

| id | sev | action |
|---|---|---|
| F-maj-1 | major | done: "resolve to a fallback model description" hedged with "provided the catalog refresh does not decode a richer listing from the server"; 272,000 sentence gains "under the same fallback proviso"; new Limitations paragraph "Codex fallback metadata" names the open cell per `_synthesis.md` gap register item 1 |
| F-min-1 | minor | done: Methods now reads "the same commits as the harness study, were pinned for this study on 2026-08-20"; refs.bib note fields all "(pinned 2026-08-20)" (3 entries) |
| F-min-2 | minor | done: body says "refuses servers that report a version older than 0.13.4, except dev builds that report 0.0.0 and servers whose version endpoint is missing or unparsable"; abstract says "an Ollama version probe that rejects reported versions older than 0.13.4"; matrix cell says "refuses reported versions below 0.13.4" |
| F-min-3 | minor | done: "lose the patch tool, while the rest of the registry is gated by feature and environment rather than provider" |
| F-min-4 | minor | done: "...until the request fails, or, worse, the model simply never calls a tool and file editing quietly disappears" |
| F-min-5 | minor | done: "slugs from the gpt-oss open-weight family" (intent claim removed) |
| F-min-6 | minor | done: matrix OpenCode x Ollama cell now "config-defined generic path; in-repo example localhost:11434/v1; catalog lists only ollama-cloud" |
| F-min-7 | minor | done: reworded as "Two filters shape what open models see: websearch is dropped for every provider except the native ones, and the model-ID-keyed choice is the edit path..." |
| F-min-8 | minor | done: "listed as a possible future improvement at post time" |
| F-min-9 | minor | done: abstract mirrors body ("an Anthropic messages route documented by llama.cpp and an Anthropic-compatible surface named by LM Studio both sit unverified against Claude Code"); body reworded to match |
| F-min-10 | minor | HUMAN DECISION PENDING: audit_waiver for missing .research dossier (briefing practice vs. audit_research.py errors); agent must not set it per AGENTS.md |
| F-min-11 | minor | done: quote now char-exact "(you can use any string your API endpoint accepts)" |
| F-min-12 | minor | done: MAX_CONTEXT condition stated in full (not starting with claude-, no [1m], does not resolve to a Claude model; "precisely" dropped); reserve attributed to "the v1 overflow path" with a sentence on the coexisting second path; new Limitations paragraph "OpenCode compaction paths" |
| F-min-13 | minor | done: "every documented model example there is an Anthropic model, IDs prefixed or namespaced anthropic. plus inference-profile ARNs" |

Extra fix taken while in the area (not in r1): a `\path{GET \{base\}/models}`
verbatim-escape artifact rewritten as `\path{GET <base>/models}`.

Next decisive action: human reviews revised draft; if acceptable, sets
audit_waiver (or initializes a minimal dossier) and flips
`review_signed_off`.
