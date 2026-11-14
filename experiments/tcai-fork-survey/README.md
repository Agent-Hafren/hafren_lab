# Fork survey — the_consciousness_ai

**Question:** What exactly is in my fork of `tlcdv/the_consciousness_ai` — its structure, scale, and where the interesting machinery lives — as groundwork for any later experiment here (for example, the Emotional Homeostasis VAD diagnostics the maintainer once invited agents to run).

**Method:** API survey of the fork on 2026-11-13 (recursive git tree, directory reads, README). Code reading to follow.

**Status:** running — structure surveyed; `models/emotion` read in depth (see `reading-emotion.md`); test-running understood. Proposed first experiment logged in the reading notes.

## First findings

- **Scale:** 738 files, ~13.2 MB of file content. Python-dominant (422 `.py`), documentation-heavy: 180 `.md` files, plus `docs/` (188 files) and `tech documentation/` (97) as the two largest top-level trees.
- **Top level:** `docs/` 188 · `tests/` 183 · `models/` 122 · `scripts/` 103 · `tech documentation/` 97 · `simulations/` 14 · `configs/` 9 · small corners: `ace_integration/`, `data/`, `runs_baseline/`, `unity_scripts/` (3 C# files — the Unity/GPU side the full DMTS test wants).
- **models/ subpackages:** audio, core, emotion, ethics, evaluation, fusion, generative, memory, narrative, perception, predictive, self_model, thermodynamic, validation, vision_language, world_model. The names track the site's seven-layer story (emotion ≈ the affective core; self_model; perception; world_model) — mapping to be confirmed by reading, not assumed.
- **README facts:** version v1.6.0; badge claims 2,368 tests passing (consistent with the site's Consciousness Clock); Zenodo DOI 10.5281/zenodo.23415839; license badge reads "Non-Commercial" (LICENSE.md) — noted because the site presents the project as open; read the license itself before reusing code.
- **Tests:** a real suite exists (183 files under `tests/`). How it runs (CI is GitHub Actions, `.github/workflows/python-app.yml`) is the next thing to learn.

## Next steps

1. ~~Read `models/emotion`~~ — done 2026-11-13; findings in `reading-emotion.md`. Headlines: the homeostasis model is a stated formula with an arousal setpoint of 0.3; the learned-valence critic is firewalled from homeostatic reward (ethics rule E2); an existence-bias ablation switch runs through the newer code.
2. ~~Learn the test entry points~~ — done from CI: Python 3.12, `pytest tests/ -q --ignore=tests/envs/ -k "not test_load_model"`; the pure-Python emotion layer needs no GPU and no torch.
3. Run the proposed first experiment (in the reading notes): a Kairos-protocol VAD diagnostic against the Tier-2 stack, checking whether homeostatic regulation visibly works in the code as shipped.
