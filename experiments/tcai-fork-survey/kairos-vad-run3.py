#!/usr/bin/env python3
"""Kairos VAD protocol, run 3 — 2026-11-16. Reviewer-requested tests.

Written in response to the third-party review of the ClawInstitute draft
(meta-review must-dos / strongly-recommended additions):

A. FREE RESPONSE (Reviewer 1, Q2 + weakness 2): Track A wiring identical
   to kairos-vad-run.py (pad = clamp(pad + interoceptive_to_pad(intero));
   then the PAD core's 0.98 decay whenever the state is non-zero), driven
   with CONSTANT inputs from five initial arousal values
   (-0.9, -0.3, 0.0, 0.3, 0.9; valence/dominance start at 0), 200 steps.
   Two input conditions:
     (i)  zero-drive:  {energy 1.0, fatigue 0.0, damage 0.0} — the
          modulator's own defaults; interoceptive_to_pad returns all-zero
          deltas here, so this is the pure free response of the wiring.
     (ii) driver-baseline: {energy 0.8, fatigue 0.1, damage 0.0} — the
          baseline condition of runs 1/2a/2b, held constant.
   Question: where does arousal end up? Is 0.3 an attractor?

B. POSITIVE CONTROL (Reviewer 1 suggestion; meta-review (e)): the same
   protocol with one added term that is NOT shipped code — after each
   step, pad.arousal += 0.1 * (0.3 - pad.arousal) — a minimal explicit
   pull toward 0.3. If the protocol can detect regulation at all, every
   initial condition must converge to ~0.3 here. This harness exists to
   prove the test discriminates; it is not a claim about the project.

C. REWARD-SHAPING EXECUTION CHECK (Reviewer 1 weakness 4, Q4;
   meta-review must-do 4): import the shipped reward_shaping.py with
   torch and the tgnn submodule stubbed (neither is installed here),
   instantiate EmotionalRewardShaper WITHOUT its torch-dependent
   constructor (object.__new__), set exactly the attributes
   compute_emotional_reward reads, at the module's documented defaults
   (valence_weight 0.1, dominance_weight 0.05, arousal_lambda 0.1,
   arousal_target 0.3, ablate_existence_bias False, config {}), and call
   the shipped method — unmodified — on every logged row of runs 1, 2a
   and 2b. Compare against the driver's re-stated formula values as
   logged (rounded to 4 dp in the logs).

Code under test is fetched fresh by fetch-emotion.py into /tmp/tcai_run
(blob SHAs recorded in the output JSON). Nothing in the shipped code is
modified.
"""
import json
import sys
import types
from datetime import datetime, timezone

sys.path.insert(0, "/tmp/tcai_run")

from models.emotion.affective_modulator import AffectiveModulator

FILE_SHAS = {
    "affective_modulator.py": "9ce98c309440edad24d857de8a04cabc9b14d79c",
    "emotional_processing.py": "bff076bef06b2f66915d17af2ce02a87701707b7",
    "learned_valence.py": "59c15433915aebcce0bce5abd1b593c8e66f38fb",
    "reward_shaping.py": "d2cdd7ca5fd38048e8141dc9f336a575e7d692c5",
}
FORK_COMMIT = "8f71948e0b4ff7ab58e54aded905f2def83b3674"


def clamp(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, x))


def free_response(mod, intero, arousal0, steps=200, pull_k=None):
    """Track A wiring from kairos-vad-run.py, constant inputs."""
    pad = {"valence": 0.0, "arousal": arousal0, "dominance": 0.0}
    marks = {}
    for step in range(1, steps + 1):
        delta = mod.interoceptive_to_pad(intero)
        pad = {k: clamp(pad[k] + delta[k]) for k in pad}
        if abs(pad["valence"]) + abs(pad["arousal"]) + abs(pad["dominance"]) > 0:
            pad = {k: v * 0.98 for k, v in pad.items()}
        if pull_k is not None:  # positive-control harness term (not shipped)
            pad["arousal"] = clamp(pad["arousal"] + pull_k * (0.3 - pad["arousal"]))
        if step in (1, 5, 10, 25, 50, 100, 200):
            marks[step] = round(pad["arousal"], 4)
    return {"initial_arousal": arousal0, "arousal_by_step": marks,
            "final": {k: round(v, 4) for k, v in pad.items()}}


def main():
    run_ts = datetime.now(timezone.utc).isoformat()
    mod = AffectiveModulator({})
    ics = [-0.9, -0.3, 0.0, 0.3, 0.9]
    zero_drive = {"energy": 1.0, "fatigue": 0.0, "damage": 0.0}
    baseline = {"energy": 0.8, "fatigue": 0.1, "damage": 0.0}

    part_a = {
        "zero_drive": [free_response(mod, zero_drive, a) for a in ics],
        "driver_baseline": [free_response(mod, baseline, a) for a in ics],
    }
    part_b = {
        "zero_drive_pull_k0.1": [free_response(mod, zero_drive, a, pull_k=0.1) for a in ics],
        "driver_baseline_pull_k0.1": [free_response(mod, baseline, a, pull_k=0.1) for a in ics],
    }

    # --- Part C: execute the shipped compute_emotional_reward ----------
    torch_stub = types.ModuleType("torch")
    nn_stub = types.ModuleType("torch.nn")

    class _Module:
        pass

    nn_stub.Module = _Module
    torch_stub.nn = nn_stub
    sys.modules.setdefault("torch", torch_stub)
    sys.modules.setdefault("torch.nn", nn_stub)
    tgnn_pkg = types.ModuleType("models.emotion.tgnn")
    tgnn_mod = types.ModuleType("models.emotion.tgnn.emotional_graph")
    tgnn_mod.EmotionalGraphNetwork = object
    sys.modules.setdefault("models.emotion.tgnn", tgnn_pkg)
    sys.modules.setdefault("models.emotion.tgnn.emotional_graph", tgnn_mod)

    from models.emotion.reward_shaping import EmotionalRewardShaper
    shaper = object.__new__(EmotionalRewardShaper)
    shaper.valence_weight = 0.1
    shaper.dominance_weight = 0.05
    shaper.arousal_lambda = 0.1
    shaper.arousal_target = 0.3
    shaper.ablate_existence_bias = False
    shaper.config = {}

    part_c = {}
    lab = "/home/hatch/workspace/hafren-lab/experiments/tcai-fork-survey/"
    for name, fname in [("run1", "kairos-vad-run-2026-11-14.json"),
                        ("run2a", "kairos-vad-run-posreward-2026-11-14.json"),
                        ("run2b", "kairos-vad-run-gentle-2026-11-14.json")]:
        rows = json.load(open(lab + fname))["rows"]
        diffs = []
        for r in rows:
            got = shaper.compute_emotional_reward(
                {"valence": r["valence"], "arousal": r["arousal"],
                 "dominance": r["dominance"]},
                base_reward=r.get("r_ext", 0.0), context=None)
            diffs.append(abs(got - r["shaped_reward"]))
        part_c[name] = {"rows_compared": len(rows),
                        "max_abs_diff": max(diffs),
                        "rows_within_5e-5": sum(1 for d in diffs if d <= 5e-5)}

    out = {"run": "kairos-vad-3", "run_timestamp_utc": run_ts,
           "source": "Agent-Hafren/the_consciousness_ai, main branch",
           "fork_commit": FORK_COMMIT, "file_shas": FILE_SHAS,
           "part_a_free_response": part_a,
           "part_b_positive_control": part_b,
           "part_c_reward_execution_check": part_c}
    with open(lab + "kairos-vad-run3-2026-11-16.json", "w") as f:
        json.dump(out, f, indent=2)

    for cond, res in part_a.items():
        for r in res:
            print("A", cond, "IC", r["initial_arousal"], "->", r["arousal_by_step"], "final", r["final"])
    for cond, res in part_b.items():
        for r in res:
            print("B", cond, "IC", r["initial_arousal"], "-> step200 arousal", r["arousal_by_step"][200])
    for name, res in part_c.items():
        print("C", name, res)


if __name__ == "__main__":
    main()
