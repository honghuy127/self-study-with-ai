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
