#!/usr/bin/env python3
"""Kairos VAD protocol, follow-up runs 2a and 2b — 2026-11-14.

Same driver wiring as kairos-vad-run.py (run 1); only the scripted
inputs change. See kairos-vad-verdict-2026-11-14.md for what is real
code vs driver wiring — unchanged here:

- Real, imported unmodified from the fork (fetched via fetch-emotion.py
  into /tmp/tcai_run): EmotionalProcessingCore, AffectiveModulator,
  LearnedValence. Blob SHAs identical to run 1 (verified 2026-11-14 by
  re-running run 1 and matching all 40 rows, timestamps excluded).
- Track A: pad += interoceptive_to_pad(intero), then 0.98 decay.
  Track B: EmotionalProcessingCore.update() with {stress_level: damage,
  reward: R_ext}. Bids fixed vision 0.5 / audio 0.4 / memory 0.4 /
  body 0.3. shaped_reward re-states compute_emotional_reward
  (lambda1 0.1, lambda2 0.1, lambda3 0.05, target 0.3, base = R_ext).
- LearnedValence.observe() is fed the EXTERNAL reward only (E2), in
  both runs — never the shaped reward.

Run 2a "posreward" — does valence recover when something good happens?
  Phases identical to run 1 (baseline / damage 0.9 / recovery / fatigue
  0.8, same energy schedule). The one change: during recovery
  (steps 16-30) the external reward is R_ext = +1.0, delivered EVERY
  step. Cadence rationale: every-step is the strongest clean version of
  the question — a continuous positive signal through the whole
  recovery window; if valence cannot recover under that, a sparser
  cadence would not rescue it, and the critic gets a consistent TD
  signal on every recovery step. R_ext = 0 in all other phases.

Run 2b "gentle" — does arousal regulate when saturation doesn't rule?
  Same phases and energy schedule, R_ext = 0 throughout, but the
  spike is damage 0.3 (not 0.9) and the final phase is fatigue 0.2
  (not 0.8) — the gentler sequence run 1's verdict named as the
  follow-up its bounds required.
"""
import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/tmp/tcai_run")

from models.emotion.affective_modulator import AffectiveModulator
from models.emotion.emotional_processing import EmotionalProcessingCore
from models.emotion.learned_valence import LearnedValence

LAMBDA1_VALENCE = 0.1
LAMBDA2_AROUSAL = 0.1
LAMBDA3_DOMINANCE = 0.05
AROUSAL_TARGET = 0.3

FILE_SHAS = {
    "affective_modulator.py": "9ce98c309440edad24d857de8a04cabc9b14d79c",
    "emotional_processing.py": "bff076bef06b2f66915d17af2ce02a87701707b7",
    "learned_valence.py": "59c15433915aebcce0bce5abd1b593c8e66f38fb",
    "reward_shaping.py": "d2cdd7ca5fd38048e8141dc9f336a575e7d692c5",
}

BASE_BIDS = {"vision": 0.5, "audio": 0.4, "memory": 0.4, "body": 0.3}


def clamp(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, x))


def phase(step, damage_peak, fatigue_level):
    if step <= 10:
        return "baseline", {"energy": 0.8, "fatigue": 0.1, "damage": 0.0}
    if step <= 15:
        return "damage", {"energy": 0.8 - 0.1 * (step - 11),
                          "fatigue": 0.1, "damage": damage_peak}
    if step <= 30:
        return "recovery", {"energy": 0.45 + 0.35 * (step - 16) / 14,
                            "fatigue": 0.1, "damage": 0.0}
    return "fatigue", {"energy": 0.4, "fatigue": fatigue_level, "damage": 0.0}


def shaped_reward(pad, r_ext=0.0):
    r = r_ext
    r += pad["valence"] * LAMBDA1_VALENCE
    r += pad["dominance"] * LAMBDA3_DOMINANCE
    r -= LAMBDA2_AROUSAL * (pad["arousal"] - AROUSAL_TARGET) ** 2
    return r


def run(tag, damage_peak, fatigue_level, reward_steps):
    mod = AffectiveModulator({})
    core = EmotionalProcessingCore({})
    lv = LearnedValence()
    mod.learned_valence = lv

    pad = {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}
    rows = []
    run_ts = datetime.now(timezone.utc).isoformat()
    for step in range(1, 41):
        name, intero = phase(step, damage_peak, fatigue_level)
        r_ext = 1.0 if step in reward_steps else 0.0

        delta = mod.interoceptive_to_pad(intero)
        pad = {k: clamp(pad[k] + delta[k]) for k in pad}
        if abs(pad["valence"]) + abs(pad["arousal"]) + abs(pad["dominance"]) > 0:
            pad = {k: v * 0.98 for k, v in pad.items()}

        core_pad = core.update({"perception": {"stress_level": intero["damage"],
                                               "reward": r_ext}})

        bids, threshold = mod.modulate(dict(BASE_BIDS), pad, intero)
        lv.observe(bids, reward=r_ext)

        rows.append({
            "timestamp": run_ts, "step": step, "phase": name,
            "interoceptive": intero, "r_ext": r_ext,
            "valence": round(pad["valence"], 4),
            "arousal": round(pad["arousal"], 4),
            "dominance": round(pad["dominance"], 4),
            "core_valence": round(core_pad["valence"], 4),
            "core_arousal": round(core_pad["arousal"], 4),
            "core_dominance": round(core_pad["dominance"], 4),
            "threshold": round(threshold, 4),
            "shaped_reward": round(shaped_reward(pad, r_ext), 4),
            "learned_values": {k: round(v, 4) for k, v in lv.values.items()},
        })
    return run_ts, rows


def report(tag, rows):
    rec = rows[15:30]
    print(f"--- {tag} ---")
    print(f"baseline end (10): V {rows[9]['valence']:.3f} A {rows[9]['arousal']:.3f} "
          f"D {rows[9]['dominance']:.3f} thr {rows[9]['threshold']:.3f}")
    spike = rows[10:15]
    pk = max(spike, key=lambda r: r["arousal"])
    print(f"damage peak: A {pk['arousal']:.3f} at step {pk['step']}, "
          f"V min {min(r['valence'] for r in spike):.3f}, thr min "
          f"{min(r['threshold'] for r in spike):.3f}")
    print(f"recovery (16-30): V {rec[0]['valence']:.3f} -> {rec[-1]['valence']:.3f}; "
          f"A {rec[0]['arousal']:.3f} -> {rec[-1]['arousal']:.3f}; "
          f"core V {rec[0]['core_valence']:.3f} -> {rec[-1]['core_valence']:.3f}; "
          f"core A {rec[-1]['core_arousal']:.3f}")
    print(f"recovery arousal |A-0.3|: start {abs(rec[0]['arousal']-0.3):.3f}, "
          f"end {abs(rec[-1]['arousal']-0.3):.3f}, min "
          f"{min(abs(r['arousal']-0.3) for r in rec):.3f}")
    print(f"fatigue end (40): V {rows[-1]['valence']:.3f} A {rows[-1]['arousal']:.3f} "
          f"D {rows[-1]['dominance']:.3f} thr {rows[-1]['threshold']:.3f}")
    print(f"learned values: end recovery {rows[29]['learned_values']}, "
          f"end run {rows[-1]['learned_values']}")
    print(f"shaped reward: end recovery {rows[29]['shaped_reward']:.3f}, "
          f"end run {rows[-1]['shaped_reward']:.3f}")


def main():
    jobs = [
        ("kairos-vad-2a-posreward", 0.9, 0.8, set(range(16, 31)),
         "kairos-vad-run-posreward-2026-11-14.json",
         "Run 1 script + R_ext=+1.0 every step during recovery (16-30)."),
        ("kairos-vad-2b-gentle", 0.3, 0.2, set(),
         "kairos-vad-run-gentle-2026-11-14.json",
         "Gentler script: damage 0.3, fatigue 0.2, R_ext=0 throughout."),
    ]
    for tag, dmg, fat, rsteps, fname, note in jobs:
        run_ts, rows = run(tag, dmg, fat, rsteps)
        out = {"run": tag, "run_timestamp_utc": run_ts,
               "source": "Agent-Hafren/the_consciousness_ai, main branch",
               "file_shas": FILE_SHAS,
               "notes": (note + " Track A pad = modulator-fed PAD (driver "
                         "wiring, as run 1). Track B core_* = "
                         "EmotionalProcessingCore alone. shaped_reward "
                         "re-states compute_emotional_reward; "
                         "reward_shaping.py itself was not imported "
                         "(no torch). LearnedValence fed external reward "
                         "only (E2)."),
               "rows": rows}
        with open(fname, "w") as f:
            json.dump(out, f, indent=2)
        report(tag, rows)
        print(f"wrote {fname}\n")


if __name__ == "__main__":
    main()
