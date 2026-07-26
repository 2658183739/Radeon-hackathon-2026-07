# Grasp Scorer V2 Model Selection Protocol

The machine-readable source of truth is
`configs/grasp_candidate_model_selection_v2.toml`. It was frozen after the
training objectives and promotion gate were committed, but before the complete
train dataset, either formal checkpoint, or any development rollout existed.

Two capacity-matched candidates are allowed: the unchanged pointwise MLP and
the groupwise safety-first objective. Both use the same 28 features,
6,276-parameter network, 2,000 steps, learning rate `1e-3`, weight decay
`1e-4`, seed 42, and single Radeon GPU. No learning-rate, width, seed, or loss
weight sweep is permitted after development is observed.

Train collection must finish first. Both checkpoints are then trained and
hash-frozen from train only. Development collection may start only after those
checkpoints exist. Evaluation requires all 16 groups and four groups for each
of the four profiles. A candidate fails if any profile adds a safety abort, if
it does not improve aggregate safety or success over static rank, or if a
six-candidate warm Radeon batch has P95 latency at or above 5 ms.

Eligible candidates are ordered by safety aborts, successes, mean selected
force, mean duration, Radeon P95, and fixed candidate name. If neither passes,
no scorer is promoted, development is not reused for tuning, and holdout is
not opened. If one is selected, its checkpoint and all hyperparameters are
frozen before the single holdout execution.

## Executable phases

After the 32-group train collection is complete, run the frozen training phase
with the ROCm environment:

```bash
cd /workspace/parcel-sorter-opt-v1
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/run_grasp_scorer_v2_pipeline.py train
```

The command refuses to run if development or holdout manifests already exist.
It builds the hash-bound train dataset, trains both exact recipes, validates
all hyperparameters and AMD/HIP metadata, hashes both checkpoints, and writes
`outputs/grasp-scorer-v2/model-selection/train-freeze-manifest.json`.

Only after that manifest exists may development be collected. When the
development collection is complete, run:

```bash
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/run_grasp_scorer_v2_pipeline.py development
```

This phase verifies frozen checkpoint hashes, builds the combined dataset,
evaluates both models, applies the preregistered selection rule, and leaves
holdout closed regardless of whether a model is promoted.
