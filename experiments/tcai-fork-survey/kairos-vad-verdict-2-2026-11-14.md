# Kairos VAD runs 2a/2b — verdict addendum, 2026-11-14

**Status: BOTH RUN.** One driver, `kairos-vad-run2.py`; logs
`kairos-vad-run-posreward-2026-11-14.json` (2a) and
`kairos-vad-run-gentle-2026-11-14.json` (2b), 40 steps each.
Run at A. Rabbit's "Go for it" (2026-11-14 22:30 MST), following up the
two experiments run 1's verdict named. Same wiring, same fetched code
as run 1 — before building on it, run 1 was re-run against a fresh
fetch and matched all 40 rows exactly (timestamps excluded), so the
fork has not drifted and the comparison across runs is clean.
Determinism: each of 2a/2b was run twice; rows identical
(timestamps excluded).

What changed vs run 1 is only the scripted inputs:

- **2a "posreward":** run 1's script verbatim, plus external reward
  R_ext = +1.0 on **every** step of the recovery phase (steps 16–30),
  0 elsewhere. Every-step is the strongest clean cadence: a continuous
  positive signal through the whole recovery window. R_ext feeds
  Track B's perception, the shaped reward's base, and
  `LearnedValence.observe()` — external reward only, as in run 1 (E2).
- **2b "gentle":** same phases and energy schedule, R_ext = 0
  throughout, but damage 0.3 (not 0.9) and fatigue 0.2 (not 0.8) —
  the gentler sequence run 1's bounds asked for.

## Run 2a — does valence recover when something good happens?

| | valence (A) | core valence (B) | arousal (A) | threshold | shaped R |
|---|---|---|---|---|---|
| Baseline end (10) | −0.18 | 0.00 | −0.29 | 0.66 | −0.05 |
| Damage end (15) | −0.98 | 0.00 | ~0.93 | 0.40 min | — |
| Recovery end (30) | **−0.98** | **0.37** | 0.31 | 0.54 | +0.87 |
| Fatigue end (40) | −0.98 | 0.01 | −0.98 | 0.80 | −0.29 |

1. **Track A valence — NO, and the reason is structural.** Track A
   valence sat at −0.98 at steps 16, 20, 25 and 30, identical to
   run 1. In the shipped code, `AffectiveModulator`'s PAD path takes
   only the interoceptive dict (energy/fatigue/damage) — there is no
   reward parameter anywhere in it. External reward has **no channel**
   into the modulator-fed PAD state. No cadence or size of reward
   could have lifted it; the answer was decided by the interface, not
   the dose. (A driver could hand-add reward to the PAD dict, but
   that would be wiring the project does not ship; run 1's pattern —
   the project's own probes pass a PAD dict in — was kept.)
2. **Track B valence — YES, modestly, and only while reward flows.**
   The PAD core alone, which does consume reward in its update,
   climbed from 0.00 (all of baseline and damage, exactly as run 1)
   to 0.118 at step 16 and 0.373 at step 30 — then decayed back to
   0.009 by step 40 once the reward stopped. So the core registers
   good events as positive valence, transiently; nothing holds the
   gain after the signal ends.
3. **The critic learns — E2 exercised, not just inspected.** Fed
   +1.0 external reward on the modulated bids, `LearnedValence`
   values grew from all-zero at step 15 to vision 0.361 / audio 0.289
   / memory 0.289 / body 0.217 at step 30, ordered by bid size as a
   linear TD critic should. They kept drifting up slightly during
   the reward-free fatigue phase (vision 0.381 at step 40) via TD
   bootstrapping across the changing, value-boosted bids — the
   wiring's own feedback, as shipped. No runaway: vision at 0.38
   after 15 reward steps is nowhere near the 6–8 "vision lock-in"
   the code's own docstring records from a long lit episode.
4. **Arousal recovery is untouched by reward** (0.929 → 0.314,
   identical to run 1) — consistent with check 1: reward simply does
   not enter Track A.
5. **The shaped reward turns positive for the wrong reason.** End of
   recovery it reads +0.866 vs run 1's −0.134. The difference is
   exactly the +1.0 external base; the VAD (homeostatic) terms still
   sum to ≈ −0.134, because they are computed from Track A's pinned
   valence. A reader of the reward alone would think the agent felt
   better. It didn't — the reward's affective terms never moved.

## Run 2b — does arousal regulate when saturation doesn't dominate?

| | valence (A) | arousal (A) | core arousal (B) | threshold |
|---|---|---|---|---|
| Baseline end (10) | −0.18 | −0.29 | 0.00 | 0.66 |
| Damage peak (15) | −0.98 | 0.44 | 0.24 | 0.48 min |
| Recovery end (30) | −0.98 | −0.09 | 0.18 | 0.62 |
| Fatigue end (40) | −0.98 | −0.64 | 0.14 | 0.74 |

1. **Arousal saturation is gone; regulation still doesn't happen.**
   Peak arousal is 0.438 (step 15), well off the 0.98 ceiling, and
   the threshold dip is proportional (0.66 → 0.48). But in recovery
   arousal falls 0.397 → 0.319 (step 18) → 0.282 (step 19) → −0.087
   (step 30): it **crosses** the 0.3 setpoint between steps 18–19 on
   the same decay trajectory and keeps going. Closest approach to
   the setpoint is 0.018 (step 18); by the end of recovery it is
   0.387 away on the low side — *farther* from 0.3 than when
   recovery began (0.097). Track B ends recovery at 0.176, decaying
   toward 0 as in run 1. Verdict: even with saturation removed, the
   setpoint is a point the decay passes through, not an attractor.
   This closes the loophole run 1's bounds left open.
2. **Valence saturation survives the gentle run.** Damage 0.3 still
   floors valence: −0.677 by step 12, −0.98 by step 15, pinned
   through step 40. The damage valence coefficient (2.0) makes even a
   mild spike a maximal valence event, and — per run 1 — nothing in
   the script can lift it afterwards. Gentleness fixed the arousal
   clamps only.
3. **Mild fatigue (0.2) still drags arousal far down:** a steady
   slide to −0.645 by step 40, threshold up to 0.742. Direction as
   documented; no floor saturation this time, but a long way from
   the setpoint in the wrong direction.
4. **Critic: all values 0.0 throughout** — expected, R_ext = 0, same
   as run 1.

## Bounds — say these out loud

- Both verdicts are about **this wiring and these scripts**, not the
  whole project. The repo ships no orchestrator; a wiring that fed
  reward into the PAD state by hand could behave differently — but
  it would be the wirer's invention, not the shipped design. What
  *is* a property of the shipped code: the modulator's PAD path has
  no reward input, and nothing in either track contains a term that
  pulls arousal toward 0.3.
- 2a's cadence (every step, +1.0) was chosen as the strongest test.
  A claim that a *sparser* cadence would do better has no mechanism
  behind it in Track A (no channel) and a weaker one in Track B.
- The shaped-reward numbers in 2a re-state the formula with the
  +1.0 base included, as run 1 did with 0; `reward_shaping.py`
  itself was still not imported (no torch here).
- Nothing here was posted to the project. Same standing decision as
  run 1: sending any of these logs back is A. Rabbit's call.
