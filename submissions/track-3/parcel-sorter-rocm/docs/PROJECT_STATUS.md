# Project Status and Reproduction Protocol

Status date: 2026-07-25. This document is the short operational view of the
Track 3 submission. It separates verified evidence from planned work so that a
reviewer can reproduce the current result without treating an experiment plan
as a capability claim.

## Hard constraints

- One AMD Radeon GPU, one visible device, and ROCm/PyTorch HIP execution.
- Open-source simulator, code, model implementation, and legally usable data.
- Physics, rendering, training, inference, and benchmarking run on the same
  Radeon device for the competition path.
- Every reported comparison fixes the dataset split, episode IDs, safety limit,
  random seeds, and artifact hashes before model selection.

## Capability ledger

| Area | Current status | Evidence or boundary |
| --- | --- | --- |
| Physics simulation | Verified | Genesis + Franka Panda + Box/Cylinder + two bins |
| Sensors | Verified | RGB, metric depth, depth-RGB view, joints, end-effector pose, target, contact force |
| Expert control | Verified as baseline | IK/PD, gripper ramp, contact verification, retry, release check, 35 N abort |
| Closed loop | Verified for the expert path | Detection -> approach -> grasp -> lift -> transfer -> release -> recovery |
| RGB ACT | Integrated and smoke-tested | Training/save/load/evaluation adapter; learned success is not promoted without held-out trials |
| RGB-D ACT | Integrated and smoke-tested | Corrected metric-depth shard passes audit; one-step closed loop is interface evidence only |
| Compact Diffusion | Radeon one-step smoke | Full matched training and closed-loop comparison are pending |
| Robustness statistics | Implemented | Per-profile metrics and Wilson 95% intervals; zero retry samples are marked unknown |
| Industry-size cartons | Evaluation-only profiles | Current parallel gripper cannot claim suction handling |
| Cylindrical parcel handling | Partial/unresolved | Scoped rolling physics and contact controls exist; a cradle end-effector is still required |
| VLA | Not in the result path | VLA-Adapter remains a license and ROCm compatibility spike |
| ROS 2 / cloud service | Not implemented | Add only after the simulator-policy contract is stable |

## Recommended run order

```text
1. preflight_radeon.sh
2. bootstrap_radeon.sh (only when dependencies are absent)
3. python -m unittest discover -s tests -q
4. run_expert.py --config configs/catalog_v2.toml --record-sensors --lerobot
5. audit_dataset.py --require-depth-rgb
6. train ACT RGB and ACT RGB-D on the same split and three seeds
7. evaluate_policy.py on a fixed held-out episode manifest
8. compare_expert_runs.py / summarize_act_evaluations.py
9. run the compact Diffusion matched comparison
10. package source, lock files, logs, metrics, and reproduction commands
```

The running Radeon collection is a data-generation job, not a final model
claim. Its output must be audited and split into train, validation, and a fixed
held-out set before training results are reported.

`scripts/build_dataset_split.py` is the reproducibility boundary. It maps the
original audit episode IDs to LeRobot's compact successful-episode indices,
stratifies each parcel profile, and emits the exact episode list used by both
ACT and Diffusion training. A missing `summary.json`, metadata/count mismatch,
or multi-task dataset is rejected by design.

watch_and_train_rocm.sh can wait for the collection summary, create the
manifest, and launch the sequential ACT matrix. It never starts training from
an incomplete dataset and writes a separate orchestration log.

## Optimization gates

1. **Data gate:** at least 300 successful, profile-balanced RGB-D episodes;
   immutable manifest and hashes.
2. **Model gate:** ACT RGB, ACT RGB-D, and compact Diffusion use identical
   splits, three seeds, and an explicitly logged budget.
3. **Task gate:** at least 30 held-out closed-loop episodes per candidate and a
   final fixed comparison set of at least 60 episodes.
4. **Safety gate:** no candidate may exceed 35 N contact force or increase drop
   rate; report first-attempt, recovery, drop, and profile-stratified results.
5. **Performance gate:** report synchronized mean/P95 inference latency,
   samples/s, peak VRAM, and GPU utilization on the same Radeon.
6. **Extension gate:** add VLA, suction, cradle, point-cloud, or ROS 2 only
   after the preceding gates pass and the new dependency/license audit is
   complete.

## Evidence policy

An implementation smoke proves that an interface runs. It does not prove task
generalization. The technical report must link the exact command, environment,
episode manifest, summary JSON, failure traces, and checkpoint hash for every
capability claim. Rejected candidates remain in `evidence/` as negative
controls, never as hidden changes to the baseline.

For the rationale and learning-oriented record, see:

- `ENGINEERING_DECISION_LOG.md`
- `DEVELOPMENT_JOURNAL.md`
- `OPTIMIZATION_ROADMAP.md`
- `RESEARCH_AND_MODEL_MATRIX.md`
- `DATASET_CARD.md` and `MODEL_CARD.md`
