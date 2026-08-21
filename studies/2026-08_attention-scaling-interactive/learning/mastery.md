# Mastery record

<!--
Administered only after practice, with tutoring disabled. The learner
completes the mastery task at help level none; the evaluator records, for
each declared capability, whether it was demonstrated, with the learner's
own words or derivation as evidence. No point tally: the verdict is
demonstrated or needs practice. This record is never rewritten; later
reviews append below.

SIMULATION: administered during the 2026-08-22 simulated-learner pipeline
validation. The evidence below is a simulated learner performance, NOT the
human's real unaided demonstration. A genuine mastery claim requires the
human to complete this task.
-->

## Mastery task

Restated from the brief: unaided, (1) reconstruct the attention equation and
define d_k; (2) derive Var(q dot k) and the normalization under unit-variance
assumptions; (3) explain how logit scale affects softmax concentration and
gradient magnitude without claiming the paper provides an ablation; (4)
separate what the paper states, what follows from the simplified assumptions,
and what remains empirically unverified; (5) solve the changed-variance
transfer problem.

- Administered: 2026-08-22
- Help level: none
- Evaluator: tutor agent; the evaluator knows the intended answers. Learner
  performance is SIMULATED for pipeline validation.

## Capabilities

| Capability | Demonstrated unaided | Evidence |
|---|---|---|
| Reconstruct equation, define d_k | yes | "Attention(Q,K,V) = softmax(QK^T / sqrt(d_k)) V; d_k is the dimension of the query and key vectors." |
| Derive Var(q dot k), normalization | yes | "q dot k sums d_k independent terms q_i k_i, each variance 1, so Var = d_k, std = sqrt(d_k); dividing by sqrt(d_k) pins the variance to 1." |
| Scale vs softmax concentration/gradients | yes | "Large logits push softmax toward one-hot, dropping entropy and shrinking gradients; scaling keeps the spread near one so gradients stay usable. The paper says this as motivation, it does not ablate it." |
| State vs derive vs unverified | yes | "The paper states the suspicion; the derivation adds the variance mechanism under independent zero-mean unit-variance coordinates; trained-model behavior is still unverified here." |
| Changed-variance transfer | yes | "With variances sigma_q^2, sigma_k^2 the std is sqrt(d_k) sigma_q sigma_k, so the unit-variance scale is 1/(sqrt(d_k) sigma_q sigma_k), which reduces to 1/sqrt(d_k) at unit variance." |

## Verdict

pass (SIMULATED). All five capabilities demonstrated unaided at help level
none in the simulated run, so the criterion is met in this validation. This
verdict reflects the simulated learner and does not certify that the human can
perform the capability; the human must complete the task for a real verdict.

## Reviews

<!-- Append one block per delayed review; never edit earlier blocks. -->

### 2026-08-22 (SIMULATION: first review scheduled, not yet administered)

- next_due was: first delayed review, scheduled at the simulated mastery date
- Result: pending; administer without displaying the learning note, then append
  the result here as a new block
- Next due: 2026-08-29
