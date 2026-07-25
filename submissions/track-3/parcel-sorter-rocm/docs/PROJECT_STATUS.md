# Project Status and Reproduction Protocol

Status date: 2026-07-25. This document is the short operational view of the
Track 3 submission. It separates verified evidence from planned work so that a
reviewer can reproduce the current result without treating an experiment plan
as a capability claim.

## Current Radeon run

On 2026-07-25, the Radeon collection completed 400 audited expert episodes.
The strict LeRobot success dataset contains 190 episodes, split deterministically
into 123 train, 24 validation, and 43 held-out episodes. The six-cell,
five-thousand-step ACT RGB/RGB-D smoke matrix completed with ROCm preflight,
three seeds, and six loadable checkpoints.

This does **not** clear the formal data gate of at least 300 balanced successful
RGB-D episodes. The matrix validates training, checkpoint, and orchestration
integration only, not model quality. Formal 30K model comparison and held-out
closed-loop ranking remain blocked until additional balanced collection passes
the same audit and a new split manifest is frozen.

The matched Radeon reset-pose A/B also completed on the same 20
`large_narrow_carton` episodes. Pose C improved success from 1/20 to 4/20 and
raised throughput, but still produced 9/20 force aborts and regressed one
baseline success. The comparison therefore returns `repeat_or_reject`; the
historical default reset pose remains active.

On the same Radeon, `plan_balanced_collection.py` was run against the completed
400-episode audit manifest. It creates a stricter fresh-shard target of 360
successes (30 for each of 12 training profiles) and estimates 1,775 attempted
episodes with the current conservative success statistics. Nine profiles are
explicitly blocked for expert diagnostics before bulk collection:
`book_box`, `medium_carton`, `shoe_box_proxy`, `long_carton`,
`large_narrow_carton`, `upright_canister`, `mailing_tube`, `near_limit_box`,
and `electronics_box`. This is a planning artifact, not a new data or model
result.

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
| RGB ACT | Integrated and smoke-tested | Six-cell 5K matrix produced a loadable RGB checkpoint; learned success is not promoted without held-out trials |
| RGB-D ACT | Integrated and smoke-tested | Corrected metric-depth shard and three 5K checkpoints pass audit; model quality remains unverified |
| Reset-pose candidate C | Radeon A/B rejected | 4/20 success, 9/20 force aborts, one regression; keep the historical default |
| Compact Diffusion | Radeon one-step smoke | Full matched training and closed-loop comparison are pending |
| Robustness statistics | Implemented | Per-profile metrics and Wilson 95% intervals; zero retry samples are marked unknown |
| Balanced collection planning | Implemented and Radeon-checked | Fresh 360-success target, configuration/audit fingerprints, profile-specific budgets, and an expert-diagnostic gate |
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

The completed Radeon collection is a data-generation artifact, not a final
model claim. Its output is audited and split into train, validation, and a
fixed held-out set; the completed 5K matrix still requires held-out evaluation
before any learned result is reported.

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

The next controlled experiment is `scripts/run_size_aware_approach_ab_rocm.sh`.
It keeps the historical reset pose and compares only geometry-aware transit
clearance on 20 fixed `large_narrow_carton` episodes. The candidate is not an
accepted optimization until the machine-checked safety and throughput gates
pass on Radeon.

The first size-aware candidate was rejected on matched Radeon evidence:
0/20 success, 12/20 force aborts, 304.67 N peak force, and a regression of
baseline episode `7000005`. Its summaries and trace-derived failure analyses
are indexed under `evidence/expert/radeon-size-aware-ab-v1-*`.

The recovery-aware retry diagnostic improved the matched result to 2/20 with
one recovered episode and no regression, but still had 11/20 force aborts. It
remains disabled by default pending a larger pre-registered recovery study.

## Latest controlled experiment: approach-step A/B

The next isolated change added `control.approach_step_m` and tested 20 mm
free-space steps against the 40 mm baseline on the same 20 Radeon episodes.
The candidate was rejected: 0/20 versus 1/20 successes, 12/20 force aborts in
both arms, 0 drops in both arms, and 161.28 N versus 111.28 N peak force. The
failure analyses identify the same `large_narrow_carton` approach/retry
bottleneck. The default remains 40 mm.

Evidence is indexed under `evidence/expert/radeon-approach-step-ab-v1-*`.
Compact summaries omit only per-frame traces and include source paths, sizes,
and SHA-256 values. The next engineering target is the approach/retry state
machine; no batch collection or model selection should start from this
negative control.
