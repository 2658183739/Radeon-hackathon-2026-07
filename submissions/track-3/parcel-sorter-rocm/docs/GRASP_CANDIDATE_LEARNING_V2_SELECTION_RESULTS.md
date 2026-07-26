# Grasp Candidate Learning V2 Selection Results

## Outcome

The v2 collection population is frozen and ready for training-only execution
on the Radeon host. Physics-free selection produced 32 train, 16 development,
and 16 locked holdout groups, balanced across `medium_carton`,
`shoe_box_proxy`, `large_narrow_carton`, and `near_limit_box`. No Genesis scene
was constructed, no robot action was executed, and no task result was read.

The exact assignments are stored in
`configs/grasp_candidate_learning_v2.toml`. The source selection evidence is
`evidence/training/grasp-candidate-learning-v2-episode-selection.json`, whose
SHA-256 is
`38198aa77cb3567899f088110907b0dd3aa2e54f04bdd90b1a16beb991ac4b8c`.

## Steps and decision rationale

1. V1 was not enlarged because its reset-fallback activation yielded complete
   labels for only four of 12 train groups and one of six development groups.
   The failure was population coverage, not evidence that a larger network was
   needed.
2. Commit `af88121` froze the v2 selector and activation contract before any
   new episode was physically executed. This separates experimental design
   from observed outcomes.
3. The selector inspected only deterministic parcel randomization and the
   existing box-height predicate. It selected the first 16 eligible IDs in
   each fresh namespace, in ascending order, then assigned 8/4/4 to
   train/development/holdout.
4. A new auditor checked the evidence hash, catalog hash, selector hash,
   deterministic randomization output, geometry predicate, exact TOML
   assignments, split balance, single-GPU ROCm contract, collision-reset
   requirement, and holdout lock.
5. The first auditor run rejected equivalent tuple/list representations after
   JSON round-trip. Comparison was corrected to canonical JSON; values, IDs,
   and the selection evidence were not changed.
6. Radeon dry-run planning produced 32 train groups with at most 192 rollouts
   and 16 development groups with at most 96 rollouts. Every child command
   carries `--planning-activation geometry-eligible`. A holdout request was
   rejected before run planning.
7. The CLI initially omitted the activation policy from its compact printed
   summary even though every child command was correct. The summary now emits
   that field so saved dry-run evidence is self-contained.

## Capability and safety boundary

The code can now select, audit, plan, resume, and validate controller-faithful
candidate-label collection. Learning may reorder only statically feasible
candidates. Hard IK and collision feasibility, collision-checked reset, the
monotonic transport contract, and the independent 35 N abort remain outside
the learned scorer.

This stage does not show that the MLP or groupwise ranker improves robot
performance. Train must be collected first; development can be opened only
after train completes. Holdout remains locked until exactly one scorer and all
hyperparameters are frozen. Vision, ACT, Diffusion, VLA, and ROS 2 remain
paused until structured candidate ranking demonstrates development value.

## Reproduction

Run the audit before starting collection:

```bash
cd /workspace/parcel-sorter-opt-v1
PYTHONPATH=src /opt/venv/bin/python \
  scripts/audit_grasp_candidate_learning_v2_protocol.py \
  --output outputs/grasp-scorer-v2/protocol-audit.json
```

The only admissible next physical command is the train split:

```bash
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/run_grasp_candidate_collection.py \
  --protocol configs/grasp_candidate_learning_v2.toml \
  --split train \
  --output-dir outputs/grasp-scorer-v2/candidates \
  --config configs/catalog_v2.toml \
  --backend rocm \
  --max-candidates 6 \
  --repeats 1
```

Do not pass `--unlock-holdout` during training or model development.
