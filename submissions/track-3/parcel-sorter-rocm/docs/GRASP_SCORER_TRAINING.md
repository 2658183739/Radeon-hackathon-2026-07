# Structured Grasp Scorer on ROCm

## Status

The frozen train and development phases are complete. Four of 12 train episodes
and one of six development episodes activated the formal reset-fallback gate;
the other episodes were recorded as structured non-label skips. The scorer is
not connected to `GenesisParcelEnv`, static ranking remains production behavior,
and holdout remains locked. The single applicable development group did not
support promotion, so opening holdout would not be justified model selection.

## Why this model

The formal counterfactual showed that static IK/collision rank and idealized
direct-IK transport can both miss a production failure. A VLA is unnecessarily
large for this low-level choice and cannot replace hard safety. The first model
is therefore a 6,276-parameter MLP trained with PyTorch/ROCm. Deterministic IK,
collision feasibility, and the 35 N supervisor stay outside the model.

Each candidate has 28 versioned features covering parcel size, estimated mass
and friction, spawn pose, action delay, destination side, candidate pose,
offsets, wrist/IK seed, manipulability, joint distance, collision clearance,
and static rank. Four outputs learn safety abort, task success, peak force, and
duration. Selection is lexicographic: predicted safety risk, success, force,
duration, then static rank.

## Frozen protocol

`configs/grasp_candidate_learning_v1.toml` was written before any new episode
was executed. It reserves 12 train episodes, six development episodes, and six
holdout episodes across `medium_carton`, `shoe_box_proxy`, and
`large_narrow_carton`. The already observed `4120001` is explicitly isolated
as `smoke` and can never contribute to a generalization claim.

The holdout gate is fixed before collection:

1. no new safety abort and no per-profile paired regression versus static rank;
2. at least one static-ranking task failure recovered on holdout; and
3. warm batch P95 below 5 ms on the single Radeon GPU.

Preview and start the frozen training collection with:

```bash
python scripts/run_grasp_candidate_collection.py \
  --protocol configs/grasp_candidate_learning_v1.toml \
  --split train --output-dir outputs/grasp-scorer-v1/collection --dry-run

python scripts/run_grasp_candidate_collection.py \
  --protocol configs/grasp_candidate_learning_v1.toml \
  --split train --output-dir outputs/grasp-scorer-v1/collection --resume
```

Each episode runs in a new Python process to isolate Genesis global state.
The manifest records the exact command, status, and source hash. Holdout is
locked unless `--unlock-holdout` is explicitly supplied after model selection.

An inactive reset-fallback gate emits `skipped_inactive_reset_gate` with no
rollout labels. The dataset builder consumes a manifest, ignores only this
explicit status, and verifies every accepted source hash. A known Genesis
interpreter-cleanup `SIGSEGV/139` is accepted only after a complete output passes
identity, controller-contract, repeat-count, and rollout-count postconditions.

## Frozen train and development result

Train collection produced 24 rows from four applicable groups: two
`large_narrow_carton`, two `medium_carton`, and no `shoe_box_proxy` groups.
Eight other train episodes did not enter the controller branch being learned.
The labels contain three successful rollouts and 14 safety aborts. A fixed
seed-42, 2,000-step Radeon fit took 2.502 s. In-sample reconstruction preserved
one success and reduced selected safety aborts from 3/4 to 0/4; this is training
fit, not generalization evidence.

Development produced only one applicable group, `large_narrow_carton:7140001`.
All six candidates exceeded 35 N and none succeeded. Static rank and the model
both selected an aborted failure; the model-selected rollout measured 35.896 N,
while the minimum observed candidate measured 35.521 N and still aborted.
Consequently the model showed no development utility or safety recovery. It is
not promoted, no controller integration is enabled, and holdout remains unseen.

The explicitly selected real six-candidate development batch measured 0.901 ms
P50 and 0.921 ms P95 after ten warmups, passing the 5 ms latency-only gate. A
latency pass cannot override the failed behavior and coverage gates.

## Radeon smoke result

Six controller-faithful candidate labels from the observed mechanism episode
formed one smoke group with 28 features. Training 1,000 full-batch steps took
1.715 s on the AMD Radeon GPU using PyTorch 2.9.1 and HIP 7.2. Final training
loss was 0.000293. Offline reconstruction selected a safe successful candidate
where static rank selected the known task failure. This is expected in-sample
fit and is not evidence of held-out improvement.

Independent checkpoint loading measured a 308.53 ms cold batch. After ten
warmups, 100 six-candidate batches measured 0.883 ms P50 and 0.902 ms P95,
or 0.147/0.150 ms per candidate. Cold and steady latency remain separate in
all reports.

## Reproduction

```bash
export PYTHONPATH=/workspace/parcel-sorter-opt-v1/src
python scripts/build_grasp_candidate_dataset.py \
  --protocol configs/grasp_candidate_learning_v1.toml \
  --input outputs/counterfactual-grasp-v1/4120001-static-first.json \
  --input outputs/counterfactual-grasp-v1/4120001-alternatives.json \
  --output outputs/grasp-scorer-v1/smoke-dataset.json

python scripts/train_grasp_scorer_rocm.py \
  --dataset outputs/grasp-scorer-v1/smoke-dataset.json \
  --output-dir outputs/grasp-scorer-v1/smoke-train \
  --train-split smoke --steps 1000 --device cuda

python scripts/evaluate_grasp_scorer.py \
  --dataset outputs/grasp-scorer-v1/smoke-dataset.json \
  --checkpoint outputs/grasp-scorer-v1/smoke-train/grasp_scorer.pt \
  --split smoke --device cuda --warmup 10 --benchmark-repeats 100 \
  --output outputs/grasp-scorer-v1/smoke-train/evaluation.json
```

Frozen train/development reproduction uses manifests rather than manual globs:

```bash
python scripts/build_grasp_candidate_dataset.py \
  --protocol configs/grasp_candidate_learning_v1.toml \
  --manifest outputs/grasp-scorer-v1/collection/train/manifest.json \
  --manifest outputs/grasp-scorer-v1/collection/development/manifest.json \
  --output outputs/grasp-scorer-v1/train-development-dataset.json

python scripts/train_grasp_scorer_rocm.py \
  --dataset outputs/grasp-scorer-v1/train-dataset.json \
  --output-dir outputs/grasp-scorer-v1/train-v1 \
  --train-split train --steps 2000 --device cuda

python scripts/evaluate_grasp_scorer.py \
  --dataset outputs/grasp-scorer-v1/train-development-dataset.json \
  --checkpoint outputs/grasp-scorer-v1/train-v1/grasp_scorer.pt \
  --split development --device cuda \
  --latency-group-id large_narrow_carton:7140001 \
  --warmup 10 --benchmark-repeats 100 \
  --output outputs/grasp-scorer-v1/train-v1/development-evaluation.json
```

The compact machine-readable record is
`evidence/training/grasp-scorer-smoke-rocm-v1.json`. Frozen train/development
evidence is `evidence/training/grasp-scorer-train-development-rocm-v1.json`.
Full datasets, checkpoint, manifests, and predictions remain in Git-ignored
`outputs/` and are bound by SHA-256.

The final synchronized Radeon source tree compiled cleanly and passed all 247
unit tests.
