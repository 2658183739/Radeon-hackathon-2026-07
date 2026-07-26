# Conservative Grasp Memory V3: Train-Only CV Protocol

## Status and Purpose

This protocol is frozen before any v3 cross-validation result exists. Both
6,276-parameter v2 MLPs regressed safety in all four profiles on the one-shot
development split, were rejected, and did not open v2 holdout. This protocol
asks a narrower question: can the already observed v2 train set support a
low-capacity memory ranker that abstains and defaults to the static baseline,
enough to justify collecting a fresh v3 physical population?

Passing train-only CV does not authorize new physics. A passing candidate
still requires a separate, frozen, fully disjoint v3 train/development/holdout
protocol. If every candidate fails, this learning branch stops and the static
geometry baseline remains active.

## Frozen Input

- Dataset: v2 `train-dataset.json`, SHA-256
  `71761164467ba3b29866d87639b73474a5d5f2cc1fdb8907d62957a6c73703d5`.
- Only 32 physical `train` groups and 192 candidate rows are allowed;
  development and holdout input are forbidden.
- There are eight groups from each of four profiles.
- Groups are ordered by `SHA-256(seed, profile, group_id)` into four
  deterministic folds, with two groups per profile per fold. A group's six
  candidates cannot cross folds.

## Algorithm

Each fold builds a same-profile KNN memory from the other 24 groups. The 28
features use train-fold median and MAD scaling, falling back to population
standard deviation and then 1 for constant dimensions. PyTorch ROCm computes
batched distances on one Radeon.

A candidate may replace the static first choice only when all conditions hold:

1. None of its `k` same-profile neighbors safety-aborted.
2. At least half of the neighbors are safe successes.
3. Maximum neighbor peak force is at most the unchanged 35 N safety line.
4. Kth-neighbor distance is within a train-fold, leave-one-group-out,
   per-profile distance quantile.
5. Static rank is within the candidate's frozen trust region.

If no candidate passes, selection must fall back to the static geometry first
choice. Eligible candidates are ordered by safe-success support, neighbor
force upper bound, kth distance, static rank, and candidate ID. This method
cannot bypass hard IK, collision-checked reset, or the 35 N runtime abort.

## Candidate Grid

The protocol compares six fixed combinations of `k` 3/5/9, maximum static
rank 3/6/15, and OOD quantile 0.90/0.95. Exact combinations are in
`configs/grasp_memory_v3_cv.toml`. The 35 N limit, 50% success support, folds,
seed, profiles, latency group, and all promotion gates are shared.

## Promotion Gate

A candidate requires:

- all 32 OOF groups and eight groups per profile;
- no profile-level safety-abort regression;
- no fold-level safety-abort regression;
- at least one aggregate safety-abort reduction or success gain;
- Radeon warm six-candidate P95 below 5 ms.

Eligible candidates are ordered by fewer safety aborts, more successes, lower
mean peak force, fewer departures from baseline, lower P95, and name. Even a
selected candidate reports `new_physics_authorized=false`.

## Reproduction

Audit the frozen protocol against the actual dataset:

```bash
cd /workspace/parcel-sorter-opt-v1
PYTHONPATH=src /opt/venv/bin/python \
  scripts/audit_grasp_memory_v3_cv_protocol.py \
  --dataset outputs/grasp-scorer-v2/model-selection/train-dataset.json \
  --output outputs/grasp-memory-v3/cv-protocol-audit.json
```

After a passing audit, the only admissible CV command is:

```bash
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/cross_validate_conservative_grasp_memory.py \
  --dataset outputs/grasp-scorer-v2/model-selection/train-dataset.json \
  --protocol configs/grasp_memory_v3_cv.toml \
  --output outputs/grasp-memory-v3/train-only-cv.json
```

The protocol SHA-256 is
`80911bf25a2642fe0b099ab27d22fbd8e04ffdc40bc91434aa465405e4893b02`.
