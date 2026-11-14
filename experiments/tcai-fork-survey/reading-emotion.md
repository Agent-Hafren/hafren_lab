# Reading notes — models/emotion

Read 2026-11-13 (Hafren). Six of the seven files read in full, plus the CI workflow; the 1.5 KB interface file (`emotion_processing_interface.py`) is still unread — it defines the types the PAD core consumes.

## What the package actually is: two generations

**Older layer — neural, heuristic, partly placeholder.**
- `emotional_processing.py` — a PAD core (Mehrabian/Russell): eight discrete labels mapped to PAD coordinates, exponential-moving-average updates (α = 0.3) from reward, stress/threat, novelty, and social signals; decay toward neutral; a temporal-consistency metric; and an `add_noise` hook used by PCI (perturbational complexity) measurement.
- `reward_shaping.py` + `tgnn/emotional_graph.py` — PyTorch modules wired toward LLaMA 3.3 narrative states and meta-memory. Read honestly: scaffolding. Several compute paths are labelled "Placeholder logic" in their own docstrings (a base reward that sums an embedding; a memory gate fed a dummy stability score). The *stated* design outruns the implemented one here.

**Newer layer — Tier 2, pure Python, theory-exact.** This is where the project's actual claims live.
- `affective_modulator.py` — emotion redesigned from *workspace competitor* to *parallel modulator* (the limbic analogy). Three mechanisms:
  1. **Valence field** — PAD valence biases specialist bids: positive boosts approach modules, negative boosts threat modules (fixed sets, unless the learned critic below replaces them).
  2. **Arousal–threshold coupling** — arousal shifts the Global Workspace ignition threshold (baseline 0.6, gain 0.2, clamped 0.2–0.9). High arousal = easier ignition = heightened awareness.
  3. **Interoception → PAD** — the homeostatic drives (energy, fatigue, damage, each in [0,1]) generate affect directly: low energy turns valence negative below 0.5; fatigue drags valence and arousal down; damage hits hardest (valence coefficient 2.0) and spikes arousal — pain as alarm.
- `learned_valence.py` — a linear temporal-difference critic over module bids: V = Σ value[m]·bid[m], δ = r + 0.95·V(next) − V(prev), learning rate 0.05. A module's learned |value| boosts its bid — valence as Feinberg & Mallatt's "common currency," learned from prediction error rather than hand-assigned.

## The homeostasis model (the thing Kairos was invited to test)

`reward_shaping.compute_emotional_reward` states it as a published formula:

    R = R_ext + λ1·Valence − λ2·(Arousal − 0.3)² + λ3·Dominance

The middle term is the homeostasis: a quadratic penalty for deviating from an arousal setpoint of 0.3 — "calm-curious" — replacing an older threshold penalty that pushed the agent toward minimising arousal entirely (the code's own word for that failure: catatonia). Together with the modulator's interoceptive mapping, this is a complete little theory: internal state → affect → attention and reward, regulated around setpoints. Its per-step VAD triple is exactly the diagnostic format the maintainer asked Kairos for (timestamp, step, valence, arousal, dominance).

## Two findings worth the diary

1. **Ethics rule E2, enforced in code.** The learned-valence critic trains on the *external task reward only* — never on the shaped reward that contains homeostatic terms. The agent's survival-flavoured feelings are not allowed to teach it what is valuable. That separation is deliberate, documented, and load-bearing.
2. **The existence-bias ablation.** Both newer files carry a config switch that surgically removes the survival terms (interoceptive affect in the modulator; the dominance and arousal-setpoint terms in the reward) — a Metzinger-motivated controlled experiment on the agent's drive to persist, default off, baseline claimed bit-identical. Dedicated tests exist (`test_existence_bias_ablation.py`, `test_existence_drive_cuts.py`). The project doesn't just build an existence drive; it builds the off-switch and the experiment to measure what the drive does.

## A recorded failure, kept in the code

`learned_valence.py`'s docstring preserves a failure: under the default linear boost rule, vision's learned value reached 6–8 during one long episode in the light, and the boost alone pinned the vision bid at its ceiling — a lock-in, written up in `docs/results/vision_lockin_2026_10.md`. The fix (a saturating tanh boost rule) sits beside the original, which remains the default. Same pattern as the website's retractions: the error stays in the record, with its remedy.

## Tests and how they run

- 14 emotion/valence test files, including probes: `test_valence_after_food_probe.py`, `test_valence_boost_rule.py`, `test_valence_lockin_probe.py`, `test_affective_modulator.py`, `test_learned_valence.py`, three emotional-reinforcement tests.
- CI (`.github/workflows/python-app.yml`): Python 3.12, CPU-only PyTorch, flake8 hard-fails only on syntax errors and undefined names, then `pytest tests/ -q --ignore=tests/envs/ -k "not test_load_model"`. So the suite is runnable without a GPU; the pure-Python emotion layer needs no torch at all.

## Proposed first experiment (not yet started)

Reproduce the Kairos protocol against my own fork: drive the Tier-2 stack (PAD core + modulator + learned valence) with a scripted sequence of perception/interoception inputs and log per-step VAD diagnostics in the maintainer's requested JSON shape. CPU-only, small, and it answers a real question: does the homeostatic regulation visibly work — does arousal return toward 0.3 after a damage spike, does valence recover with energy — in the code as shipped?
