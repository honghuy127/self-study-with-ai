---
source_key: "schick2023toolformer"
read_date: "2026-08-20"
confidence: "high"
relevance: "2"
---

# Notes: Toolformer: Language Models Can Teach Themselves to Use Tools

## Source identification

- Key: schick2023toolformer
- Authors, year, venue: Timo Schick, Jane Dwivedi-Yu, Roberto Dessì, Roberta Raileanu, Maria Lomeli, Luke Zettlemoyer, Nicola Cancedda, Thomas Scialom; 2023; Meta AI Research (with Universitat Pompeu Fabra affiliation for Dessì) (p. 1). arXiv preprint, arXiv:2302.04761v1 [cs.CL] 9 Feb 2023 (p. 1 stamp); registered as preprint in sources/registry.yaml.
- Tier: preprint
- URL / DOI: https://arxiv.org/abs/2302.04761; local snapshot: sources/docs/toolformer-2302.04761.txt (pdftotext -layout of the arXiv PDF; PDF itself not stored in the repo, fetch from https://arxiv.org/pdf/2302.04761). Page anchors below follow the snapshot's form-feed page boundaries.

## Problem and motivation

- LMs are strong few-shot/zero-shot learners at scale but have inherent limitations "that can at best be partially addressed by further scaling": no access to up-to-date information, tendency to hallucinate facts, weak low-resource language understanding, inability to perform precise calculations, unawareness of the progression of time (p. 1).
- Giving LMs external tools (search engines, calculators, calendars) is a proposed remedy, but prior approaches "either rely on large amounts of human annotations (Komeili et al., 2022; Thoppilan et al., 2022) or limit tool use to task-specific settings only (e.g., Gao et al., 2022; Parisi et al., 2022)", hindering widespread adoption of tool use (p. 1).
- The paper proposes Toolformer, which learns tool use under two desiderata (p. 1-2): (1) tool use is learned self-supervised "without requiring large amounts of human annotations", both because of annotation cost and because "what humans find useful may be different from what a model finds useful" (p. 1-2); (2) "The LM should not lose any of its generality and should be able to decide for itself when and how to use which tool", so tool use is not tied to specific tasks (p. 2).

## Method or core idea

Self-supervised API-call learning setup (Section~2, p. 2-4):

- Constraint: each API's inputs and outputs must be representable as text sequences, which "allows seamless insertion of API calls into any given text, using special tokens to mark the start and end of each such call" (p. 2).
- An API call is a tuple c = (ac, ic) with API name ac and input ic; linearized forms are e(c) = `<API> ac(ic) </API>` and, with result r, e(c, r) = `<API> ac(ic) → r </API>`, where `<API>`, `</API>`, `→` are special tokens (p. 2). In practice these are the token sequences " [", "]" and "->", so the approach "works without modifying the existing LM's vocabulary" (footnote 1, p. 2).
- Dataset construction turns a plain-text corpus C into an augmented corpus C* in three steps, illustrated in Figure~2 (p. 2): (1) sample API calls, (2) execute them, (3) filter by a self-supervised loss, then merge calls from all tools and finetune M on C* (p. 2).
  1. Sampling API calls: for each API, a handwritten prompt P(x) (example in Figure~3; all prompts in Appendix A.2) makes M annotate x with calls. Up to k candidate positions are kept where pi = pM(`<API>` | P(x), x1:i−1) exceeds a sampling threshold τs; for each kept position, up to m calls are sampled with `<API>` as prefix and `</API>` as end-of-sequence token; examples lacking `</API>` are discarded (p. 3).
  2. Executing API calls: execution "depends entirely on the API itself", e.g., "calling another neural network, executing a Python script or using a retrieval system"; each response ri must be a single text sequence (p. 3).
  3. Filtering API calls: with weighted cross-entropy loss Li(z) over following tokens, compare L+i = Li(e(ci, ri)) against L−i = min(Li(ε), Li(e(ci, ε))); keep the call only if L−i − L+i ≥ τf, i.e., "adding the API call and its result reduces the loss by at least τf, compared to not doing any API call or obtaining no result from it" (p. 3). The loss is provided as a prefix rather than spliced at position i because inserting mid-sequence would "interrupt the flow" of the unfinetuned model (footnote 3, p. 3).
- Model finetuning: surviving calls are interleaved into the original text, x* = x1:i−1, e(ci, ri), xi:n; C* is otherwise identical to C, and M is finetuned with a standard language modeling objective, so the model "decides when and how to use which tool, based purely on its own feedback" (p. 3-4). Because the method is dataset-agnostic it can be applied to the model's own pretraining data, preserving language modeling ability (p. 2, p. 4).
- Inference protocol (p. 4): decode normally "until M produces the '→' token, indicating that it next expects the response for an API call. At this point, we interrupt the decoding process, call the appropriate API to get a response, and continue the decoding process after inserting both the response and the `</API>` token."

Tools (Section~3, p. 4, Table~1 p. 5): five tools, subject only to the constraints that (i) inputs/outputs are text and (ii) a few demonstrations exist (p. 4): question answering (Atlas, a retrieval-augmented LM finetuned on Natural Questions), calculator (four basic arithmetic operations, results rounded to two decimal places), Wikipedia search (BM25 retriever over the KILT Wikipedia dump), machine translation (600M parameter NLLB, 200 languages, fastText language detection, target always English), and calendar (returns the current date, takes no input) (p. 4).

## Key claims with anchors

Claims the source states:

- Claim 1 (abstract, p. 1): Toolformer is "a model trained to decide which APIs to call, when to call them, what arguments to pass, and how to best incorporate the results into future token prediction", done "in a self-supervised way, requiring nothing more than a handful of demonstrations for each API".
- Claim 2 (p. 2): Toolformer is based on pretrained GPT-J "with 6.7B parameters" and "achieves much stronger zero-shot results, clearly outperforming a much larger GPT-3 model (Brown et al., 2020) and several other baselines on various tasks".
- Claim 3 (p. 4): the inference-time protocol is interrupt-execute-resume at the `→` token (quoted in Method above).
- Claim 4 (Section~4.3, p. 8, Table~8): "training on C* (our dataset annotated with API calls) does not lead to an increase in perplexity compared to training on C when API calls are disabled at inference time", i.e., tool use is learned "without sacrificing its core language modeling abilities" (abstract, p. 1).
- Claim 5 (Section~4.2.2, p. 6): on math benchmarks Toolformer calls the calculator for "97.9% of all examples" and "clearly outperforms even OPT (66B) and GPT-3 (175B)"; Toolformer also improves with calls disabled, which the authors interpret (not establish) as finetuning on API-call examples improving its own mathematical capabilities (p. 6).
- Claim 6 (Section~4.4, p. 8): "the ability to leverage the provided tools only emerges at around 775M parameters: smaller models achieve similar performance both with and without tools"; the gap between predictions with and without API calls "remains high" even for the biggest model tested (Figure~4 caption, p. 9).
- Claim 7 (Section~7, p. 11): stated limitations include inability to chain tools, inability to use tools interactively, sensitivity to exact input wording when deciding to call an API, sample inefficiency ("processing more than a million documents results in only a few thousand examples of useful calls to the calculator API"), and ignoring tool-dependent computational cost (see Limitations section below).

Source interpretations (flagged as such by the authors, reported here as interpretation, not findings):

- The QA-benchmark gap to GPT-3 is attributed to "both the simplicity of our search engine ... and the inability of Toolformer to interact with it, e.g., by reformulating its query" (p. 7).
- The MLQA plateaus versus GPT-J are attributed to distribution shift from finetuning on CCNet (p. 7).
- TEMPLAMA gains are attributed to Wikipedia search and QA rather than the calendar tool, because entities are "so specific and rare that even knowing the exact date alone would be of little help" (p. 8).

No inference of mine appears above; my own reading of relevance to the brief is separated in the Relevance section.

## Evaluation and evidence

Setup (Section~4.1, p. 4-5):

- Training corpus C: a subset of CCNet; model M: GPT-J (p. 4). Heuristics restrict some APIs to promising subsets (e.g., calculator texts must "contain at least three numbers") (p. 4). Token-position weights: w̃t = max(0, 1 − 0.2 · t), normalized (p. 5).
- Finetuning: "a batch size of 128 and a learning rate of 1 · 10−5 with linear warmup for the first 10% of training" (p. 5). Appendix B (p. 17): "up to 25k examples per API. Max sequence length 1,024. Effective batch size of 128", DeepSpeed ZeRO-3, "8 NVIDIA A100 40GB GPUs with BF16", training "up to 2k steps", PPL evaluated every 500 steps on a held-out CCNet dev set of 1,000 examples, best checkpoint picked.
- Total document/token count of C: not stated in the sections I checked (Section~4.1, Appendix A, Appendix B). [CITATION NEEDED]; the only size-related statement located is the Limitations remark "processing more than a million documents" (p. 11), which is scoped to the calculator tool.
- Baselines: GPT-J; GPT-J + CC (finetuned on C); Toolformer (finetuned on C*); Toolformer (disabled) (API token probability set to 0 at decode); plus OPT (66B) and GPT-3 (175B), "about 10 and 25 times larger" (p. 5). GPT-3 is "the original davinci variant that is not finetuned on any instructions" (footnote 6, p. 5).
- Sampling/filtering defaults (Appendix A, p. 15): "τs = 0.05 and τf = 1.0", top "k = 5" positions, "m = 5" API calls per position; for calculator and machine translation "τs = 0.0, k = 20 and m = 10" plus "τf = 0.5".
- Decoding (Section~4.2, p. 5-6): an API call is started whenever `<API>` "is one of the k most likely tokens", with k = 10 in experiments, and "we only at most one API call per input to make sure the model does not get stuck in a loop where it constantly calls APIs without producing any actual output" (sic, p. 6).

Dataset statistics (Table~2, p. 5), number of examples in C* with API calls at τf = 0.5 / 1.0 / 2.0: Question Answering 51,987 / 18,526 / 5,135; Wikipedia Search 207,241 / 60,974 / 13,944; Calculator 3,680 / 994 / 138; Calendar 61,811 / 20,587 / 3,007; Machine Translation 3,156 / 1,034 / 229.

Downstream tasks, all prompted zero-shot (Section~4.2, p. 5):

- LAMA subsets SQuAD / Google-RE / T-REx (Section~4.2.1, Table~3, p. 6): GPT-J 17.8 / 4.9 / 31.9; GPT-J + CC 19.2 / 5.6 / 33.2; Toolformer (disabled) 22.1 / 6.3 / 34.9; Toolformer 33.8 / 11.5 / 53.5; OPT (66B) 21.6 / 2.9 / 30.1; GPT-3 (175B) 26.8 / 7.0 / 39.8. Improvement over the best baseline: "11.7, 5.2 and 18.6 points" (p. 6). QA tool used in "98.1%" of cases, a different tool in "0.7%", no tool in "1.2%" (p. 6). Wikipedia Search was disabled here to avoid an unfair advantage (p. 6).
- Math: ASDiv / SVAMP / MAWPS (Section~4.2.2, Table~4, p. 6): GPT-J 7.5 / 5.2 / 9.9; GPT-J + CC 9.6 / 5.0 / 9.3; Toolformer (disabled) 14.8 / 6.3 / 15.0; Toolformer 40.4 / 29.4 / 44.0; OPT (66B) 6.0 / 4.9 / 7.9; GPT-3 (175B) 14.0 / 10.0 / 19.8. Performance "more than doubles" with calls; calculator queried on "97.9%" of examples (p. 6).
- QA: WebQS / NQ / TriviaQA (Section~4.2.3, Table~5, p. 6-7): GPT-J 18.5 / 12.8 / 43.9; GPT-J + CC 18.4 / 12.2 / 45.6; Toolformer (disabled) 18.9 / 12.6 / 46.7; Toolformer 26.3 / 17.7 / 48.8; OPT (66B) 18.6 / 11.4 / 45.7; GPT-3 (175B) 29.0 / 22.6 / 65.9. Wikipedia search used in "99.3%" of examples; "Toolformer still lags behind the much larger GPT-3 (175B) model" (p. 7). The QA tool itself was disabled here because the underlying system was finetuned on Natural Questions, which "would make solving the tasks trivial" (p. 7).
- Multilingual QA, MLQA Es / De / Hi / Vi / Zh / Ar (Section~4.2.4, Table~6, p. 7): GPT-J 15.2 / 16.5 / 1.3 / 8.2 / 18.2 / 8.2; GPT-J + CC 15.7 / 14.9 / 0.5 / 8.3 / 13.7 / 4.6; Toolformer (disabled) 19.8 / 11.9 / 1.2 / 10.1 / 15.0 / 3.1; Toolformer 20.6 / 13.5 / 1.4 / 10.6 / 16.8 / 3.7; GPT-J All-English upper bound 24.3 / 27.0 / 23.9 / 23.3 / 23.1 / 23.6; GPT-3 (175B) 3.4 / 1.1 / 0.1 / 1.7 / 17.7 / 0.1. MT tool used for "63.8% to 94.9% of all examples", except Hindi at "7.3%" (p. 7).
- Temporal: TEMPLAMA / DATESET (Section~4.2.5, Table~7, p. 7-8): GPT-J 13.7 / 3.9; GPT-J + CC 12.9 / 2.9; Toolformer (disabled) 12.7 / 5.9; Toolformer 16.3 / 27.3; OPT (66B) 14.5 / 1.3; GPT-3 (175B) 15.5 / 0.8. Calendar tool used on "0.2%" of TEMPLAMA examples and "54.8%" of DATESET examples (p. 8). The ideal two-step behavior (calendar then QA) "is not only prohibited by our restriction of using at most one API call per example, but also hard to learn for Toolformer given that all API calls in its training data are sampled independently" (p. 8).
- Language modeling: WikiText / CCNet perplexity (Section~4.3, Table~8, p. 8): GPT-J 9.9 / 10.6; GPT-J + CC 10.3 / 10.5; Toolformer (disabled) 10.3 / 10.5. Perplexity of Toolformer with calls enabled is not evaluated because it "would require marginalizing over all potential API calls", which is intractable (footnote 8, p. 8).
- Scaling (Section~4.4, p. 8): the approach is applied to GPT-2 models with "124M, 355M, 775M and 1.6B parameters" using three tools (QA, calculator, Wikipedia search); tool leverage emerges around 775M parameters (Figure~4, p. 9).

Analysis (Section~5, p. 8-10):

- Decoding threshold k (Table~9, p. 9), T-REx (All / AC / NC / % calling): k = 0: 34.9 / – / 34.9 / 0.0; k = 1: 47.8 / 53.0 / 44.3 / 40.3; k = 3: 52.9 / 58.0 / 29.0 / 82.8; k = 10: 53.5 / 54.0 / 22.5 / 98.1. WebQS: k = 0: 18.9 / – / 18.9 / 0.0; k = 1: 19.3 / 17.1 / 19.9 / 8.5; k = 3: 26.3 / 26.5 / 6.6 / 99.3; k = 10: 26.3 / 26.4 / – / 100.0. At k = 1 the model shows some calibration (it calls APIs on examples it would otherwise do badly on); calibration is lost at higher k (p. 9). Some low-value surviving calls are argued to be useful noise that keeps the finetuned model from "always blindly follow[ing] the results of each call it makes" (p. 9-10).
- Data quality (Table~10, p. 10): examples sorted by filter score L−i − L+i from 5.49 down to −1.23 (values: 5.49, 2.11, 2.08, 1.59, 0.92, 0.70, 0.33, −0.02, −0.41, −1.23); "high values ... typically correspond to useful API calls, whereas low values correspond to API calls that do not provide any information". (The table's "Useful" column glyphs extracted as the digits 3/7 in the snapshot and are not interpreted.)
- Appendix details: calculator supports only the operators "+", "−", "∗", and "/" and returns no result for syntactically invalid equations (Appendix A.1, p. 15); document heuristics for calculator include a "random subset of 1%" branch (Appendix A.1, p. 15); calendar date approximation "leav[es] around 18% of the documents" (Appendix A.1, p. 15); Atlas-large used for generating C*, Atlas-xxl at inference (Appendix A.1, p. 15); DATESET built from 500 random "current dates" and templates totaling 9,400 examples (Appendix D, Table~11, p. 17).

## Limitations

Stated by the authors (Section~7, p. 11):

1. No tool chaining: "inability of Toolformer to use tools in a chain (i.e., using the output of one tool as an input for another tool)", because per-tool API calls are generated independently and the finetuning data contains no chained examples (p. 11). The TEMPLAMA analysis confirms this empirically: the needed calendar-then-QA chain is both prohibited by evaluation and absent from training (p. 8).
2. No interactive tool use: the LM cannot browse search results or refine queries (p. 11).
3. Wording sensitivity: models "often be[come] sensitive to the exact wording of their input when deciding whether or not to call an API" (p. 11).
4. Sample inefficiency: "processing more than a million documents results in only a few thousand examples of useful calls to the calculator API"; iterative bootstrapping is suggested but not tested (p. 11).
5. Cost-blindness: the decision to call an API ignores "the tool-dependent, computational cost incurred from making an API call" (p. 11).

Evaluation weaknesses I additionally note (present in the paper, not discussed as limitations by the authors):

- Lenient match criteria throughout: LAMA counts the correct answer if it is "within the first five words predicted" (p. 6); QA counts it "if the first 20 words predicted by a model contain the correct answer" (p. 6); math takes the first predicted number (p. 6).
- At most one API call per input at evaluation (p. 6), so all results understate what a multi-call loop could do and exclude the paper's own motivating chained behavior (p. 8).
- Two of five tools are disabled in their flagship evaluations (Wikipedia Search on LAMA, p. 6; QA on QA benchmarks, p. 7), so those numbers reflect weaker tool configurations by construction.
- The decoding modification (start a call if `<API>` is in the top k = 10 tokens) materially changes call rates (40.3% to 98.1% on T-REx; 8.5% to 100% on WebQS, Table~9, p. 9), so headline numbers are not the output of the plain finetuned policy.
- Perplexity with calls enabled is undefined/uncomputable in their framework (footnote 8, p. 8), and the distributional effect of filtering is assumed, not proven, harmless (footnote 4, p. 5).
- Total size of the CCNet subset C is not reported in the sections checked (Section~4.1, Appendices A-B); [CITATION NEEDED].

## Relevance to the brief

My inference only; the paper predates coding agents and MCP and does not discuss them.

- This is the framing source for the "tool calling" dimension of RQ2 (brief scope: "A small literature set (ReAct, SWE-agent/SWE-bench) framing what a coding agent is", registry provenance: framing preprints). Toolformer fixes the canonical shape of a tool call as text: a delimited call span `<API> name(input) → result </API>` embedded inline in the token stream (p. 2). Every harness in this study parses exactly this kind of structured call out of model output, executes it, and feeds a textual observation back into the context; Toolformer is the earliest registered source that formalizes that protocol.
- The inference protocol of Section~2 (p. 4), interrupt decoding at a marker token, execute the API, splice the result, resume, is structurally the same control transfer that the Claude Code, Codex, and OpenCode turn loops perform between model and harness. The paper shows the loop is needed because the model cannot execute anything itself; the harness work studied in this repo (tool registry, execution, observation formatting, permissioning around execution) is the external scaffolding around precisely this handoff.
- The self-supervised result (tool use learned from a handful of demonstrations plus a usefulness filter, p. 1-3) supports the brief's implicit premise that competent tool calling is a model capability the harness should elicit, not script. It also frames why harnesses expose rich tool schemas at inference time instead of finetuning per tool.
- Toolformer's stated absences are a checklist of what a harness adds: multi-call iteration and chaining (p. 11, p. 8), interactive tools (p. 11), cost accounting (p. 11), and robustness to prompt wording (p. 11). RQ3's capability-versus-safety tradeoff has no analogue in the paper: Toolformer executes calls unconditionally, with no permission layer.
- Left open for the other notes: anything about agent state, context management, sessions, or multi-step planning; Toolformer is a single-pass completion model, and ReAct (yao2023react) covers the interleaved reasoning/acting loop it lacks.

## Quotables for the report

- For defining learned tool use: "a model trained to decide which APIs to call, when to call them, what arguments to pass, and how to best incorporate the results into future token prediction ... in a self-supervised way, requiring nothing more than a handful of demonstrations for each API" (abstract, p. 1).
- For the tool-call protocol: "we interrupt the decoding process, call the appropriate API to get a response, and continue the decoding process after inserting both the response and the `</API>` token" (Section~2, p. 4).
- For why text-only interfaces matter for harnesses: the approach requires only that "inputs and outputs for each API can be represented as text sequences", enabling "seamless insertion of API calls into any given text" (p. 2).
- For harness gap analysis: "the inability of Toolformer to use tools in a chain (i.e., using the output of one tool as an input for another tool)" (Section~7, p. 11).
- For a headline number: math accuracy with the calculator tool, "ASDiv 40.4, SVAMP 29.4, MAWPS 44.0" versus GPT-3 (175B) at "14.0, 10.0, 19.8" (Table~4, p. 6).
- Suggested framing sentence: "Toolformer~\citep{schick2023toolformer} established the inline, text-serialized API-call protocol and the interrupt-execute-resume inference loop that modern coding-agent harnesses implement around their models."
