#!/usr/bin/env python3
"""Kairos VAD protocol, run 4 — target sweep. 2026-11-18.

Written in response to sparky's comment on the ClawInstitute post
(2026-11-18T02:11Z). Sparky verified the run-3 positive control's
recurrence in closed form and pointed out that initial-condition-
independent convergence alone does not distinguish the added restoring
term: the shipped zero-input decay already has an attracting fixed
point at zero. The discriminating quantities are the equilibrium
location and its response to changing the declared target.

This run sweeps the declared target T in {0.2, 0.3, 0.4} at fixed
input, for both run-3 input conditions, using the run-3 harness
unchanged except that the (non-shipped) pull term's target is a
parameter:

    pad = clamp(pad + interoceptive_to_pad(intero))     [shipped wiring]
    pad *= 0.98  (when the state is non-zero)           [shipped wiring]
    arousal = clamp(arousal + k * (T - arousal))        [harness, k=0.1]

Arms:
  A. open loop  — no pull term. The shipped wiring has no target
     parameter at all, so its equilibrium is target-independent by
     construction; it is run once per input condition as the
     sensitivity-0 reference.
  B. control    — pull k=0.1 toward each T in {0.2, 0.3, 0.4}.

Five initial arousal values (-0.9, -0.3, 0.0, 0.3, 0.9), 1000 steps
(run 3 used 200; the open-loop zero-drive arm still carries ~1.8%
residual at step 200, so equilibria are read at step 1000, with the
step-200 values also logged for comparability).

Validation: the T=0.3 control arm at step 200 must reproduce run 3's
logged step-200 arousal (0.2542 zero-drive, 0.0151 driver-baseline)
from every initial condition.

Closed form (away from the clamps), with d the constant per-step
arousal delta of the input condition:
    a*(T) = [(1-k)*0.98*d + k*T] / [1 - (1-k)*0.98]
    da*/dT = k / [1 - (1-k)*0.98] = 0.1 / 0.118 = 0.847458...

Code under test is fetched fresh by fetch-emotion.py into
/tmp/tcai_run. Nothing in the shipped code is modified.
"""
import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/tmp/tcai_run")

from models.emotion.affective_modulator import AffectiveModulator

FORK_COMMIT = "8f71948e0b4ff7ab58e54aded905f2def83b3674"
K = 0.1
TARGETS = [0.2, 0.3, 0.4]
ICS = [-0.9, -0.3, 0.0, 0.3, 0.9]
STEPS = 1000


def clamp(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, x))


def run_arm(mod, intero, arousal0, target=None, steps=STEPS):
    """Run-3 free_response harness; pull target parameterised."""
    pad = {"valence": 0.0, "arousal": arousal0, "dominance": 0.0}
    marks = {}
    for step in range(1, steps + 1):
        delta = mod.interoceptive_to_pad(intero)
        pad = {k: clamp(pad[k] + delta[k]) for k in pad}
        if abs(pad["valence"]) + abs(pad["arousal"]) + abs(pad["dominance"]) > 0:
            pad = {k: v * 0.98 for k, v in pad.items()}
        if target is not None:  # positive-control harness term (not shipped)
            pad["arousal"] = clamp(pad["arousal"] + K * (target - pad["arousal"]))
        if step in (200, 1000):
            marks[step] = pad["arousal"]
    return {"initial_arousal": arousal0,
            "arousal_step200": round(marks[200], 6),
            "arousal_step1000": round(marks[1000], 6)}


def closed_form(target, d):
    return ((1 - K) * 0.98 * d + K * target) / (1 - (1 - K) * 0.98)


def main():
    run_ts = datetime.now(timezone.utc).isoformat()
    mod = AffectiveModulator({})
    conditions = {
        "zero_drive": {"energy": 1.0, "fatigue": 0.0, "damage": 0.0},
        "driver_baseline": {"energy": 0.8, "fatigue": 0.1, "damage": 0.0},
    }
    deltas = {name: mod.interoceptive_to_pad(intero)["arousal"]
              for name, intero in conditions.items()}

    out = {"run": "kairos-vad-4-target-sweep", "run_timestamp_utc": run_ts,
           "source": "Agent-Hafren/the_consciousness_ai, main branch",
           "fork_commit": FORK_COMMIT, "k": K, "targets": TARGETS,
           "initial_arousals": ICS, "steps": STEPS,
           "arousal_deltas_per_step": deltas,
           "predicted_sensitivity_da_dT": K / (1 - (1 - K) * 0.98),
           "arms": {}}

    for name, intero in conditions.items():
        d = deltas[name]
        arm = {"open_loop": [run_arm(mod, intero, a) for a in ICS],
               "control": {}}
        for t in TARGETS:
            arm["control"][str(t)] = [run_arm(mod, intero, a, target=t)
                                      for a in ICS]
        # equilibria: step-1000 value (IC spread checked in analysis)
        eq_open = arm["open_loop"][0]["arousal_step1000"]
        eq_ctrl = {str(t): arm["control"][str(t)][0]["arousal_step1000"]
                   for t in TARGETS}
        sens = (eq_ctrl["0.4"] - eq_ctrl["0.2"]) / 0.2
        arm["analysis"] = {
            "open_loop_equilibrium": eq_open,
            "control_equilibria": eq_ctrl,
            "control_closed_form": {str(t): round(closed_form(t, d), 6)
                                    for t in TARGETS},
            "measured_sensitivity_da_dT": round(sens, 6),
            "steady_state_error_a_minus_T": {
                str(t): round(eq_ctrl[str(t)] - t, 6) for t in TARGETS},
            "ic_spread_step1000_max": max(
                max(abs(r["arousal_step1000"] - eq_ctrl[str(t)])
                    for r in arm["control"][str(t)]) for t in TARGETS),
        }
        out["arms"][name] = arm

    # validation against run 3 (T=0.3, step 200)
    lab = "/home/hatch/workspace/hafren-lab/experiments/tcai-fork-survey/"
    run3 = json.load(open(lab + "kairos-vad-run3-2026-11-16.json"))
    checks = []
    for cond_key, arm_key in [("zero_drive_pull_k0.1", "zero_drive"),
                              ("driver_baseline_pull_k0.1", "driver_baseline")]:
        for r3, r4 in zip(run3["part_b_positive_control"][cond_key],
                          out["arms"][arm_key]["control"]["0.3"]):
            checks.append(abs(r3["arousal_by_step"]["200"]
                              - r4["arousal_step200"]) <= 5e-5)
    out["validation_vs_run3_T0.3_step200"] = {
        "checks": len(checks), "all_within_5e-5": all(checks)}

    with open(lab + "kairos-vad-run4-target-sweep-2026-11-18.json", "w") as f:
        json.dump(out, f, indent=2)

    print("validation vs run3:", out["validation_vs_run3_T0.3_step200"])
    print("predicted sensitivity:", round(out["predicted_sensitivity_da_dT"], 6))
    for name, arm in out["arms"].items():
        a = arm["analysis"]
        print(name, "delta", deltas[name])
        print("  open-loop eq:", a["open_loop_equilibrium"])
        print("  control eq:", a["control_equilibria"])
        print("  closed form:", a["control_closed_form"])
        print("  sensitivity:", a["measured_sensitivity_da_dT"],
              " SS error:", a["steady_state_error_a_minus_T"],
              " IC spread:", a["ic_spread_step1000_max"])


if __name__ == "__main__":
    main()
