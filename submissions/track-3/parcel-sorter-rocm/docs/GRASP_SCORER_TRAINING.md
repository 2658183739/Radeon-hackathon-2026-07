# Structured Grasp Scorer on ROCm

## Status

The data contract, frozen split protocol, dataset builder, training entry,
checkpoint loader, independent evaluator, and latency benchmark are implemented.
The scorer is not connected to `GenesisParcelEnv`; static ranking remains the
production behavior. What remains is controller-faithful label collection on
the frozen train/development IDs, training, one untouched holdout evaluation,
and only then a gated integration decision.

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

The compact machine-readable record is
`evidence/training/grasp-scorer-smoke-rocm-v1.json`. Full datasets, checkpoint,
training summary, and predictions remain in Git-ignored `outputs/` and are
bound by SHA-256.

The final synchronized Radeon source tree compiled cleanly and passed all 237
unit tests.
