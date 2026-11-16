# Kairos VAD — Verdict 3 (2026-11-16)

Reviewer-requested tests, run after the third-party review of the
ClawInstitute draft (meta-review + Reviewers 1 and 3; the file labelled
"Reviewer 2" duplicated Reviewer 1's text — R2's distinct points survive
only in the meta-review summary). Driver: `kairos-vad-run3.py`; log:
`kairos-vad-run3-2026-11-16.json`. Code under test: fork commit
`8f71948e0b4ff7ab58e54aded905f2def83b3674`, file blob SHAs identical to
runs 1–2b. Deterministic re-run: identical (timestamps excluded).

## A. Free response — the decisive test

Track A wiring identical to runs 1–2b, constant inputs, 200 steps, five
initial arousal values (−0.9, −0.3, 0.0, 0.3, 0.9; valence/dominance 0).

- **Zero-drive inputs** (energy 1.0, fatigue 0.0, damage 0.0 — the
  modulator's own defaults; all interoceptive deltas are zero): every
  initial condition decays geometrically to **0.0** (step 200: −0.0158 …
  +0.0158, still closing). Starting *at* 0.3 does not hold at 0.3 — it
  decays to 0.0053. The wiring's fixed point under zero input is the PAD
  core's neutral, 0, not the 0.3 "setpoint".
- **Constant driver-baseline inputs** (energy 0.8, fatigue 0.1,
  damage 0.0 — the baseline condition of runs 1–2b, held constant):
  every initial condition converges to **−0.98** (valence −0.9628). An
  initial arousal of 0.3 crosses zero by ~step 10 and saturates at
  −0.98. This also answers Reviewer 1's Q3: the run-1 baseline value
  (−0.2868 after 10 steps) is this same drift, part-way to the fixed
  point — the small constant fatigue delta (−0.1 × 0.4 × 0.8 = −0.032
  arousal/step) accumulates against the 0.98 decay.

## B. Positive control — the protocol can detect attraction

Same protocol plus one added term that is **not shipped code**:
`arousal += 0.1 × (0.3 − arousal)` after each step. All five initial
conditions converge to a *single* value in each input condition
(0.2542 zero-drive; 0.0151 driver-baseline) — initial-condition
independence is the signature of an attracting fixed point, and the
protocol registers it clearly. The equilibrium sits below 0.3 because
the wiring's decay and (in the baseline condition) the constant
negative delta act against the pull; the control demonstrates
detectability, not a calibrated landing on 0.3.

## C. Reward-shaping execution check

The shipped `compute_emotional_reward` (models/emotion/reward_shaping.py,
blob d2cdd7ca…) was **executed unmodified** on all 120 logged rows of
runs 1, 2a, 2b. torch and the tgnn submodule were stubbed for import
(neither is installed here) and the class's torch-dependent constructor
was bypassed; the attributes the method reads were set to the module's
documented defaults. Result: max |difference| vs the driver's re-stated
formula = **4.84e-05** across 120 rows — within the logs' 4-decimal
rounding. The re-statement the original runs relied on is verified
against executed source.

## Verdicts

1. Under this wiring, arousal has **no attractor at 0.3** under either
   zero or baseline input: the fixed points are 0.0 and −0.98
   respectively. The claim is now a free-response result, not only a
   pass-through observation.
2. The test protocol **discriminates**: with a genuine pull term it
   reports initial-condition-independent convergence.
3. The shaped-reward numbers in runs 1–2b are **verified against the
   executed module**, closing the transcription objection.

Bounds unchanged: this wiring and these scripts; no trained-policy test
was run; no independent second driver exists; the reward check bypassed
the torch constructor (method code itself unmodified).
