# Learning journal

<!--
Append-only. One entry per meaningful exchange. Commit summaries; verbatim
learner attempts stay local unless the learner opts in. Agents never rewrite
past entries.

Help levels:
  0  restate the question only
  1  point to the prerequisite or relevant variable
  2  supply an intermediate equation or counterexample
  3  show the step, then ask the learner to explain it back
-->

## 2026-08-21 Full concept path, heavily scaffolded

- Prompt: traverse the default path from dot-product meaning to the
  assumptions-versus-derivation distinction.
- Learner response: worked through every link with scaffolding. Landed:
  variance of the sum is d_k (standard deviation 8 for d_k = 64),
  normalization pins variance to 1, softmax concentration at large logits,
  and the (b) answer with the three assumptions named after a correction
  that "no big logits" is the result, not an assumption. Shaky: explaining
  E[XY] = E[X]E[Y] back unaided (needed the completed chain twice); the
  k_i = q_i counterexample was missed on first attempt; "half the mass"
  underestimate of softmax concentration.
- Help level: 3 on the variance mechanism, 1-2 elsewhere.
- Outcome: partially landed; the independence split and the
  distribution-versus-realized-value distinction need practice.
- Follow-up: near and transfer practice not yet administered; session
  stopped by the learner before practice.

## 2026-08-22 Targeted rework: independence split and distribution vs realized value (SIMULATION)

- Prompt: two links left shaky last time. First, why does
  Var(q_i k_i) = E[q_i^2]E[k_i^2] when q_i and k_i are independent and
  zero-mean? Second, after dividing by sqrt(d_k), is every realized logit
  bounded, or only the spread of their distribution?
- Learner response: (1) wrote Var(q_i k_i) = E[(q_i k_i)^2] - (E[q_i k_i])^2,
  argued E[q_i k_i] = E[q_i]E[k_i] = 0 by independence and zero means, then
  E[(q_i k_i)^2] = E[q_i^2]E[k_i^2] by independence, landing on
  Var(q_i k_i) = sigma_q^2 sigma_k^2 (=1 under unit variance). Needed one
  prompt to factor E[(q_i k_i)^2] into the product of second moments. (2)
  First answered "every logit becomes small," then self-corrected after the
  tutor asked about a single drawn q, k pair: the division sets the variance
  (spread) of the logit distribution to 1; an individual realized logit can
  still be several sigma from zero. Stated the distribution-versus-realized
  distinction unprompted on the second try.
- Help level: 2 on the independence split (one intermediate prompt), 1 on the
  distribution-versus-realized distinction (a single counterexample question).
- Outcome: both shaky links landed. The learner now supplies the independence
  factorization and the distribution-versus-realized distinction without a
  completed chain. Ready for near and transfer practice.
- Follow-up: administer near and transfer practice unaided, then the mastery
  task at help level none.
- NOTE (SIMULATION): this exchange was generated during the 2026-08-22
  simulated-learner pipeline validation, not produced by the human learner.
