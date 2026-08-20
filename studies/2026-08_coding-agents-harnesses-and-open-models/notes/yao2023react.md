---
# per-source note for the ReAct framing preprint.
source_key: "yao2023react"
read_date: "2026-08-20"
confidence: "high"   # main text fully legible in the extraction; figure/table
                     # caveats listed under Limitations
relevance: "2 (useful)"   # framing source for what a coding agent is; not a
                          # system under study
---

# Notes: ReAct: Synergizing Reasoning and Acting in Language Models

## Source identification

- Key: `yao2023react`
- Authors, year, venue: Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, Yuan Cao; 2023; "Published as a conference paper at ICLR 2023" (p. 1); arXiv:2210.03629v3 [cs.CL] 10 Mar 2023 (p. 1). Authors at Princeton University and Google Research, Brain team (p. 1).
- Tier: preprint (per `sources/registry.yaml`; the snapshot text itself is the ICLR 2023 camera-ready, p. 1)
- URL / DOI: https://arxiv.org/abs/2210.03629 ; local snapshot: `sources/docs/react-2210.03629.txt` (`pdftotext -layout` of the arXiv PDF, taken 2026-08-20; PDF itself not stored in the repo, fetch from https://arxiv.org/pdf/2210.03629; page N begins after the (N-1)th form-feed character).

## Problem and motivation

- The paper says it solves the separation between reasoning and acting in LLMs: "their abilities for reasoning (e.g. chain-of-thought prompting) and acting (e.g. action plan generation) have primarily been studied as separate topics" (p. 1, Abstract).
- Chain-of-thought (CoT) reasoning "is a static black box, in that the model uses its own internal representations to generate thoughts and is not grounded in the external world, which limits its ability to reason reactively or update its knowledge. This can lead to issues like fact hallucination and error propagation over the reasoning process" (p. 2).
- Prior work on acting with language models "do[es] not employ language models to reason abstractly about high-level goals or maintain a working memory to support acting", except Inner Monologue's limited verbal reasoning (p. 2). Before ReAct, "there have not been studies on how reasoning and acting can be combined in a synergistic manner for general task solving, and if such a combination can bring systematic benefits compared to reasoning or acting alone" (p. 2).
- Human motivation: cooking analogy in which verbal reasoning tracks progress, handles exceptions, and identifies needed external information between actions (p. 1).

## Method or core idea

- Formal setup: at timestep t an agent receives observation ot in O and takes action at in A under policy π(at | ct), with context ct = (o1, a1, ..., ot−1, at−1, ot) (p. 3).
- Core mechanism: "we augment the agent's action space to Â = A ∪ L, where L is the space of language." A language action (a thought or reasoning trace) "does not affect the external environment, thus leading to no observation feedback"; instead it "aim[s] to compose useful information by reasoning over the current context ct, and update the context ct+1 = (ct, ât) to support future reasoning or acting" (p. 3).
- Thought types enumerated by the paper: decomposing task goals and creating action plans, injecting relevant commonsense knowledge, extracting important parts from observations, tracking progress and transiting action plans, handling exceptions and adjusting action plans (p. 3).
- Executor: a frozen PaLM-540B (Chowdhery et al., 2022) prompted with few-shot in-context examples; each example is "a human trajectory of actions, thoughts, and environment observations to solve a task instance (see Appendix C)" (p. 3). Footnote 1 (p. 3) notes GPT-3 results in Appendix A.1 "outperforms PaLM-540B".
- Interleaving schedule: for reasoning-primary tasks the trajectory alternates into "multiple thought-action-observation steps" (dense thoughts); for decision-making tasks "thoughts only need to appear sparsely in the most relevant positions", and "we let the language model decide the asynchronous occurrence of thoughts and actions for itself" (pp. 3-4).
- Claimed design properties (source's own framing, p. 4): A) "Intuitive and easy to design" (annotators "just type down their thoughts in language on top of their actions taken"; "No ad-hoc format choice, thought design, or example selection is used in this paper"); B) "General and flexible"; C) "Performant and robust" (learns "from one to six in-context examples"); D) "Human aligned and controllable" (humans "can also control or correct the agent behavior on the go by thought editing, as shown in Figure 5 in Section 4").
- Knowledge-intensive tasks (Section~3.1, p. 4): HotpotQA (multi-hop QA over two or more Wikipedia passages) and FEVER (claims labeled SUPPORTS, REFUTES, or NOT ENOUGH INFO), in a question-only setup. Grounding is a deliberately minimal Wikipedia web API with three actions (p. 4):
  - `search[entity]`: returns the first 5 sentences of the entity page, else top-5 similar entities from the Wikipedia search engine;
  - `lookup[string]`: returns "the next sentence in the page containing string, simulating Ctrl+F functionality on the browser";
  - `finish[answer]`: ends the task with the answer.
  The paper states this space is "significantly weaker than state-of-the-art lexical or neural retrievers" on purpose: "to simulate how humans would interact with Wikipedia, and force models to retrieve via explicit reasoning in language" (p. 4).
- Prompting setup (Section~3.2, p. 4): 6 (HotpotQA) and 3 (Fever) randomly selected training cases manually composed into ReAct-format trajectories; footnote 2 (p. 4): "We find more examples do not improve performance."
- Baselines, built by ablating ReAct trajectories (p. 5): Standard (removes thoughts, actions, observations); CoT (removes actions and observations; reasoning-only); CoT-SC ("sampling 21 CoT trajectories with decoding temperature 0.7 during inference and adopting the majority answer"); Act (removes thoughts; acting-only, "loosely resembling how WebGPT ... interacts with the Internet to answer questions").
- Combining internal and external knowledge (p. 5): heuristic A) ReAct -> CoT-SC: "when ReAct fails to return an answer within given steps", set to "7 and 5 steps for HotpotQA and FEVER respectively"; heuristic B) CoT-SC -> ReAct: "when the majority answer among n CoT-SC samples occurs less than n/2 times".
- Finetuning (p. 5): a bootstrapping approach "using 3,000 trajectories with correct answers generated by ReAct" to finetune PaLM-8B and PaLM-62B; details in Appendix B.1 (p. 15): batch size 64; on PaLM-8B, ReAct and Act finetuned "for 4, 000 steps" and Standard/CoT "for 2, 000 steps"; on PaLM-62B, ReAct/Act "for 4, 000 steps" and Standard/CoT "for 1, 000 steps".
- Decision-making tasks (Section~4, p. 7): ALFWorld is a text game aligned with ALFRED with "6 types of tasks"; an instance "can have more than 50 locations and take an expert policy more than 50 steps to solve". Prompt construction: three annotated trajectories per task type with sparse thoughts that "(1) decompose the goal, (2) track subgoal completion, (3) determine the next subgoal, and (4) reason via commonsense where to find an object"; evaluation on "134 unseen evaluation games in a task-specific setup"; robustness via "6 prompts for each task type through each permutation of 2 annotated trajectories from the 3" (p. 7). Baseline BUTLER is "an imitation learning agent trained on 10^5 expert trajectories for each task type" (superscript lost in extraction, which prints "105", p. 7; footnote 5, p. 7, excludes Micheli & Fleuret 2021's GPT-2 finetuned on "3553 task instances" because it was trained on all task types). WebShop (pp. 7-8): "1.18M real-world products and 12k human instructions"; metrics are average score and success rate on "500 test instructions"; baselines are IL trained with "1,012 human annotated trajectories" and IL+RL additionally trained with "10,587 training instructions".
- Thought mechanics in the concrete action spaces: in WebShop ReAct adds a `think[...]` action whose observation is simply "OK." (Table 6, p. 22); in ALFWorld thoughts are `> think:` turns also answered "OK." (Table 8, p. 24, and Table 7, p. 23, where the Act prompt is identical minus thoughts). Trajectory examples: ReAct (p. 27), Act (pp. 28-29), ReAct-IM (pp. 29-30), WebShop Act vs ReAct (p. 31).

## Key claims with anchors

What the source establishes (empirical, checkable in its tables):

- Claim 1 (p. 1, Abstract; Table 1 p. 5): on HotpotQA and Fever, ReAct overcomes CoT's "hallucination and error propagation" by interacting with a simple Wikipedia API; with PaLM-540B, ReAct beats the Act-only baseline on both tasks (27.4 vs 25.7 EM on HotpotQA; 60.9 vs 58.9 Acc on Fever).
- Claim 2 (p. 6; Table 1 p. 5): ReAct outperforms CoT on Fever ("60.9 vs. 56.3") and slightly lags CoT on HotpotQA ("27.4 vs. 29.4").
- Claim 3 (p. 6; Table 1 p. 5): the best prompting methods are the combinations, CoT-SC -> ReAct (34.2 EM / 64.6 Acc) and ReAct -> CoT-SC (35.1 EM / 62.0 Acc); Figure 2 text: both combinations "significantly and consistently outperform CoT-SC across different number of samples, reaching CoT-SC performance with 21 samples using merely 3-5 samples" (p. 6).
- Claim 4 (p. 8; Table 3 p. 8): on ALFWorld, best ReAct trial averages 71% success vs best Act 45% and BUTLER 37%; "even the worse ReAct trial (48%) beats the best trial of both methods"; the advantage over Act is consistent across six controlled trials, "with relative performance gain ranging from 33% to 90% and averaging 62%".
- Claim 5 (p. 1, Abstract; p. 8; Table 4 p. 8): on ALFWorld and WebShop, one- or two-shot ReAct "outperform[s] imitation and reinforcement learning methods by an absolute success rate of 34% and 10% respectively" (abstract), beating methods "trained with 10^3 ~ 10^5 task instances" (extraction prints "103 ∼ 105", p. 3).
- Claim 6 (p. 6; Table 2 p. 6): human-labeled analysis of 200 sampled HotpotQA trajectories (50 correct + 50 incorrect for each of ReAct and CoT): success-mode true positives ReAct 94% vs CoT 86%; false positives (hallucinated trace or facts) 6% vs 14%; failure-mode reasoning errors 47% vs 16%; search result error 23% (ReAct only); hallucination 0% vs 56% of failures; label ambiguity 29% vs 28%.
- Claim 7 (p. 6): ReAct has "one frequent error pattern specific to ReAct, in which the model repetitively generates the previous thoughts and actions", categorized as reasoning error; footnote 4 (p. 6) suspects "the sub-optimal greedy decoding procedure".
- Claim 8 (p. 8): ReAct-IM (IM-style dense external-feedback thoughts) scores 53 overall best-of-6 vs ReAct's 71, with ReAct ahead "on five out of six tasks"; ReAct-IM fails by misidentifying subgoal completion and lacking commonsense localization (p. 8; ablation construction, Appendix B.2, p. 15).
- Claim 9 (p. 6): with only 3,000 finetuning trajectories, ReAct becomes the best method among Standard/CoT/Act/ReAct; "PaLM-8B finetuned ReAct outperforming all PaLM-62B prompting methods, and PaLM-62B finetuned ReAct outperforming all 540B prompting methods".
- Claim 10 (Appendix A.1, p. 14; Table 5 p. 14): GPT-3 (text-davinci-002, greedy decoding) ReAct outperforms PaLM-540B: HotpotQA EM 30.8 vs 29.4 (on a random subset of 500 validation questions) and ALFWorld success rate 78.4 vs 70.9 (all 134 unseen validation instances, best prompt set per PaLM-540B).
- Claim 11 (Appendix A.3, p. 15; Figure 5 p. 15): human-in-the-loop thought editing (removing a hallucinating sentence in Act 17, adding hints in Act 23) makes a failing ALFWorld trajectory succeed; humans go "from typing tens of actions to only editing a couple of thoughts"; policy editing on-the-go "is difficult for Act and previous RL methods".
- Claim 12 (p. 14, Appendix A.2): dataset labels can be outdated; on a HotpotQA example whose label (2,664 rooms) is stale, Standard and CoT hallucinate and Act fails despite web access, "due to a lack of reasoning to guide how to interact with the Internet for QA", while ReAct retrieves the up-to-date answer.

What the source interprets (positions and readings, not raw measurements):

- Interpretation 1 (p. 8): "To our knowledge, ReAct is the first demonstration of combined reasoning and action using an LLM applied to an interactive environment within a closed-loop system." Priority claim, hedged.
- Interpretation 2 (p. 9): Inner Monologue "is the first work that demonstrates such a closed-loop system, which ReAct builds on", but "does not truly comprise of inner thoughts" (Section 4, p. 8, elaborates: IM feedback is limited to environment state and remaining goals).
- Interpretation 3 (p. 6): the hallucination contrast means ReAct trajectories are "more grounded, fact-driven, and trustworthy, thanks to the access of an external knowledge base", while ReAct's interleaved structure "reduces its flexibility in formulating reasoning steps".
- Interpretation 4 (p. 4): ReAct's four design properties (A-D) are characterizations, not measured results.

What I infer is separated in "Relevance to the brief" below.

## Evaluation and evidence

- Datasets: HotpotQA (multi-hop QA, exact match), FEVER (fact verification, accuracy), ALFWorld (text-game household tasks, per-task and overall success rate), WebShop (web shopping, average score and success rate) (p. 3 lists the four; setups pp. 4, 7-8).
- Table 1 (PaLM-540B prompting; HotpotQA EM / Fever Acc) (p. 5): Standard 28.7 / 57.1; CoT (Wei et al., 2022) 29.4 / 56.3; CoT-SC (Wang et al., 2022a) 33.4 / 60.4; Act 25.7 / 58.9; ReAct 27.4 / 60.9; CoT-SC -> ReAct 34.2 / 64.6; ReAct -> CoT-SC 35.1 / 62.0; Supervised SOTA (Zhu et al., 2021; Lewis et al., 2020) 67.5 / 89.5. Footnote a (p. 5): "HotpotQA EM is 27.1, 28.9, 33.8 for Standard, CoT, CoT-SC in Wang et al. (2022b)."
- Table 2 (success/failure mode percentages, 200 manually labeled HotpotQA examples) (p. 6): true positive 94% (ReAct) vs 86% (CoT); false positive 6% vs 14%; reasoning error 47% vs 16%; search result error 23% vs "-"; hallucination 0% vs 56%; label ambiguity 29% vs 28%.
- Table 3 (ALFWorld task-specific success rates, %) (p. 8): Act (best of 6) Pick 88, Clean 42, Heat 74, Cool 67, Look 72, Pick 2 41, All 45; ReAct (avg) 65, 39, 83, 76, 55, 24, 57; ReAct (best of 6) 92, 58, 96, 86, 78, 41, 71; ReAct-IM (avg) 55, 59, 60, 55, 23, 24, 48; ReAct-IM (best of 6) 62, 68, 87, 57, 39, 33, 53; BUTLERg (best of 8) 33, 26, 70, 76, 17, 12, 22; BUTLER (best of 8) 46, 39, 74, 100, 22, 24, 37. Caption note: "BUTLER and BUTLERg results are from Table 4 of Shridhar et al. (2020b). All methods use greedy decoding, except that BUTLER uses beam search."
- Table 4 (WebShop score / success rate) (p. 8): Act 62.3 / 30.1; ReAct 66.6 / 40.0; IL 59.9 / 29.1; IL+RL 62.4 / 28.7; Human 82.1 / 59.6. The "Expert" row is visible in the extraction with no numerals recoverable from the layout: `[CITATION NEEDED]` (looked at Table 4 in the p. 8 layout extraction; the Expert row's Score and SR values are blank in `react-2210.03629.txt`, likely a side-by-side-table layout artifact of pdftotext).
- Table 5 (p. 14): ReAct prompting, PaLM-540B vs GPT-3 (text-davinci-002, greedy): HotpotQA EM 29.4 / 30.8; ALFWorld success rate 70.9 / 78.4.
- Supplementary quantitative statements: 7-step/5-step caps cover only "0.84% and 1.33%" of correct trajectories on HotpotQA/FEVER (footnote 3, p. 5); finetuning details at batch size 64 (p. 15); "one-shot Act prompting already performs on par with IL and IL+RL methods" on WebShop (p. 8); "existing methods are still far from the performance of expert humans" (p. 8).
- Values I could not extract: Figure 2 and Figure 3 chart values (p. 6 and p. 7) are not present in the text extraction; I rely on the surrounding text descriptions. Figure 1 and Figure 4/5 glyph content renders as mojibake in the extraction and is cited only via captions.

## Limitations

Source-stated limitations:

- The paper contains no dedicated numbered "Limitations" section. Limitations are distributed: contribution item (4) promises "systematic ablations" and analysis of "the limitations of ReAct under the prompting setup" (p. 3); the conclusion carries the main self-critique; the ethics statement carries safety caveats.
- Prompting ceiling: "complex tasks with large action spaces require more demonstrations to learn well, which unfortunately can easily go beyond the input length limit of in-context learning" (Section 6, p. 9). Multi-task training and RL are named as future directions (p. 9).
- ReAct lags CoT on HotpotQA prompting (27.4 vs 29.4, p. 6, Table 1 p. 5), i.e. acting can hurt reasoning accuracy in some domains.
- ReAct's "structural constraint" raises reasoning-error rate versus CoT, 47% vs 16% (Table 2, p. 6), including a repetitive-loop failure pattern specific to ReAct (p. 6, footnote 4 suspects greedy decoding).
- Tool feedback fragility: "Non-informative search, which counts for 23% of the error cases, derails the model reasoning and gives it a hard time to recover and reformulate thoughts" (p. 6).
- Prompting ReAct is the worst of four methods on PaLM-8B/62B before finetuning, "due to the difficulty to learn both reasoning and acting from in-context examples" (p. 6).
- All prompting results remain far below supervised SOTA (HotpotQA EM 67.5, Fever Acc 89.5, Table 1 p. 5), and WebShop results remain far below human performance 82.1 / 59.6 (p. 8).
- Reproducibility: "Our main experiments are done on PaLM..., which is not an openly accessible model yet" (p. 10).
- Safety: "hooking up a large language model with an action space to interact with external environments (e.g. the web, physical environments) has potential dangers, e.g. looking up inappropriate or private information, or taking harmful actions in an environment"; the paper's experiments mitigate this "by limiting the interactions to specific websites (Wikipedia or WebShop)... without any dangerous actions in the action space design (i.e. models cannot really buy products on WebShop the research benchmark, or edit Wikipedia)" (Ethics Statement, p. 10).

Evaluation weaknesses (my assessment of the evidence, anchored to the same pages):

- Acting-only baseline comparison on ALFWorld reports best-of-6 prompts for Act and ReAct (average reported too), but BUTLER is taken from another paper with beam search (Table 3 caption, p. 8), so decoding settings differ across baselines.
- The 34%/10% abstract headline (p. 1) compares best-of-6/best-of-8 trial picks against ML baselines; the per-task variance is large (e.g. ReAct avg vs best-of-6 on ALFWorld: 57 vs 71, Table 3 p. 8), so prompt selection accounts for a substantial part of the gap.
- Failure-mode percentages come from 50 randomly sampled trajectories per method-condition on HotpotQA only (p. 6), not from the decision-making benchmarks.
- The Wikipedia API is intentionally weak (p. 4), so ReAct-vs-CoT differences partly reflect how much the task rewards exact-name retrieval.
- Human-in-the-loop editing (Appendix A.3, p. 15) is a single illustrative example, labeled by the authors as leaving "more systematic study as future work".
- Medium caveat: this note reads a `pdftotext -layout` extraction, not the PDF. Figure interiors are unreadable (mojibake) or absent; superscripts were lost (the extraction prints "103 ∼ 105" on p. 3 and "105" on p. 7 where the PDF plainly means 10^3-10^5 and 10^5); Table 4's Expert row lost its numerals. All numeric claims above were verified against the extraction's text; any value that could not be recovered is marked `[CITATION NEEDED]`.

## Relevance to the brief

All statements here are my inference about the source's relevance, separate from its claims.

- Frames RQ2 (what a coding-agent harness is). ReAct's augmented-action-space formulation, Â = A ∪ L with thoughts as environment-free context updates ct+1 = (ct, ât) (p. 3), is the ancestor architecture of the three harnesses under study: a turn loop in which the model interleaves free-form reasoning with tool calls and ingests tool observations. The brief's "turn loop, tools, context management" decomposition maps directly onto thought, action, and observation bookkeeping as defined on p. 3.
- Action spaces and grounding. The deliberately minimal Wikipedia API, search/lookup/finish, justified as forcing "explicit reasoning in language" (p. 4), is an early statement that the agent-computer interface is a designed object whose shape changes behavior. This motivates the harness-level tool comparison in RQ1 (apply-patch strategies, shell tool design) and pairs with `yang2024sweagent` in this registry's framing set. The no-op `think` action answered "OK." in the WebShop and ALFWorld prompts (Table 6 p. 22; Table 8 p. 24) is the precedent for the scratchpad/think tools modern harnesses expose (my inference, not the paper's).
- Failure modes of acting-only and reasoning-only baselines. Acting-only: cannot decompose goals or track environment state, and gets stuck in repeated command loops even after a visible no-op (p. 8; trajectory pp. 28-29); it also cannot exploit web access without reasoning guidance (p. 14). Reasoning-only: hallucination is 56% of CoT failures versus 0% for ReAct, with 14% false positives among CoT successes (Table 2, p. 6). These two failure profiles are exactly what coding-harness turn loops and grounding tools are built to suppress, and they justify reporting them as the baseline pathologies the brief asks about.
- Capability-safety tradeoff (RQ3). The ethics statement's mitigation, restricting both the environment and the action space ("models cannot really buy products on WebShop ... or edit Wikipedia", p. 10), is the earliest explicit statement in this source set that capability is traded against safety by narrowing what actions an agent can take, the same axis on which Codex/OpenCode/Claude Code design permissions and sandboxes.
- What it leaves open for this study: ReAct has no context management or compaction, no persistent state or session rollout, no permission enforcement, no subagents, and no multi-tool action spaces anywhere near shell-and-filesystem scale; it is a single frozen model with at most six demonstrations (pp. 3-4, 7). Those are precisely the harness layers the three pinned codebases add, which this note will not attribute to ReAct.

## Quotables for the report

- Loop definition, for framing the turn-loop dimension: "reasoning traces help the model induce, track, and update action plans as well as handle exceptions, while actions allow it to interface with and gather additional information from external sources such as knowledge bases or environments" (p. 1, Abstract).
- Action-space augmentation, for the tools dimension: "we augment the agent's action space to Â = A ∪ L, where L is the space of language" (p. 3).
- Reasoning-only pathology, for motivating grounded tool access: CoT "is a static black box, in that the model uses its own internal representations to generate thoughts and is not grounded in the external world" (p. 2).
- Acting-only pathology, for motivating reasoning in the loop: without thoughts, Act "fails to correctly decompose goals into smaller subgoals, or loses track of the current state of the environment" (p. 8).
- Headline evidence: "outperforms imitation and reinforcement learning methods by an absolute success rate of 34% and 10% respectively" on ALFWorld and WebShop, "while being prompted with only one or two in-context examples" (p. 1, Abstract).
- Closed-loop priority, hedged: "To our knowledge, ReAct is the first demonstration of combined reasoning and action using an LLM applied to an interactive environment within a closed-loop system" (p. 8). Suggested framing: cite once as the origin of the interleaved reasoning-plus-acting loop that all three harnesses implement; do not load more weight on it.
- Safety precedent, for RQ3 framing: "hooking up a large language model with an action space to interact with external environments ... has potential dangers" (p. 10).
