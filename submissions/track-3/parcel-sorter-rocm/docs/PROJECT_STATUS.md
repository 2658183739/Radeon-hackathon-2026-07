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

## Latest controlled experiment: approach contact-brake A/B

The candidate commanded at most 10 mm of separation after observing at least
20 N during `MOVE_PREGRASP`. On the fixed 20 Radeon episodes it matched the
baseline at 1/20 successes, 12/20 force aborts, and zero drops. Peak force
worsened from 111.28 N to 467.31 N. Throughput was 1.047x baseline, but both
absolute task and safety gates failed. The critical trace jumped from 0 N on
the previous frame directly to the 467.31 N abort frame, showing that the
current 30 Hz reactive force path cannot prevent the first collision impulse.

The candidate is rejected and disabled. Evidence is indexed under
`evidence/expert/radeon-contact-brake-ab-v1-*`. The next controlled intervention
is a pre-contact geometric-distance guard or a higher-rate compliant/impedance
controller. The 35 N hard limit, balanced-data gate, and formal model-ranking
block remain unchanged.

## Latest controlled experiment: vertical-barrier recovery A/B

The candidate froze horizontal motion below the transit height and allowed a
120 mm vertical recovery step. It reduced one dangerous episode from 56.76 N
to 32.99 N peak force, but regressed successful episode `7000005` to a 42.43 N
force abort. Overall candidate results were 0/20 successes, 12/20 force
aborts, and zero drops versus baseline 1/20, 12/20, and zero drops. Candidate
throughput was zero, so it is rejected and disabled.

Evidence is indexed under `evidence/expert/radeon-approach-barrier-ab-v1-*`.
The next engineering step is a pre-contact geometric filter using Genesis
finger `get_AABB()`; balanced collection and model ranking remain blocked.

## Latest controlled experiment: pre-contact AABB guard

The candidate enabled `control.precontact_aabb_guard_distance_m=0.040` and
filtered only pre-descent `MOVE_PREGRASP` actions whose nominal target moved
toward the parcel. It triggered 65 times over 6,003 AABB samples, with 1.625 ms
mean synchronized AABB measurement cost and a 16-step maximum active span.

Matched Radeon results: baseline 1/20 successes, 12/20 force aborts, 0 drops,
111.28 N peak force; candidate 0/20, 12/20, 0 drops, 111.28 N. Approach
timeouts increased from 7 to 8, `7000005` regressed, and candidate throughput
was zero. The machine comparison rejected the candidate; the default remains
disabled. Evidence is indexed under
`evidence/expert/radeon-approach-aabb-ab-v1-*`, with compact summaries retaining
the safety aggregate and source hashes.

The next engineering target is not threshold tuning. It is a higher-rate,
geometry-aware compliant/impedance layer or a redesigned recovery state machine,
followed by a new pre-registered Radeon A/B. Balanced 360-success collection,
formal ACT/Diffusion ranking, VLA integration, and ROS 2 packaging remain
blocked by the expert safety gate.

## Latest controlled experiment: approach compliance A/B

The candidate scaled arm Kp to 0.50 and arm Kv to `sqrt(0.50)` only while
executing `MOVE_PREGRASP`; finger gains and the default 1.0 path were unchanged.
On the fixed single-Radeon `large_narrow_carton` episodes `7000000`--`7000019`,
baseline and candidate both achieved 1/20 successes and zero drops. Candidate
force aborts fell from 12/20 to 10/20 and P95 peak force fell from 98.12 N to
71.07 N, but approach timeouts rose from 7 to 9, throughput fell to 0.751x, and
maximum force stayed 111.28 N. The machine comparison rejected it; the default
remains `approach_stiffness_scale=1.0`.

Evidence is indexed under `evidence/expert/radeon-approach-compliance-ab-v1-*`.
The next controller target is contact-near Cartesian velocity/impedance with an
explicit recovery state. Balanced RGB-D collection and learned-policy ranking
remain blocked until the expert safety gates pass.

## Latest controlled experiment: operational-space approach velocity

The candidate replaced only `MOVE_PREGRASP` IK position commands with a
bounded, weighted damped-least-squares velocity controller using the Genesis
Jacobian. Isolated Radeon checks proved both the Jacobian convention and
`control_dofs_velocity()` path; the formal comparison accepted only
`control.approach_velocity_control_enabled` as a difference.

On fixed episodes `7000000`--`7000019`, baseline produced 1/20 successes,
12/20 force aborts, zero drops, and 17.80 parcels/hour. The candidate produced
0/20, 13/20 force aborts, zero drops, and zero throughput. It regressed
`7000005`; maximum force remained 111.28 N despite a lower P95. The controller
is rejected and remains disabled. Evidence is indexed under
`evidence/expert/radeon-approach-velocity-ab-v1-*`.

The measured stall identifies hand/carton geometry as the next boundary.
Balanced 360-success RGB-D collection, ACT/Diffusion/3D ranking, VLA, and ROS 2
remain blocked. The next candidate must redesign the grasp pose and recovery
state around explicit geometry, then pass the same fixed Radeon elimination
protocol before broader evaluation.

## Latest controlled experiment: collision-checked reset

Link-level 240 Hz diagnostics found that failed episode `7000001` started with
a hand/carton collision at physics substep zero, whereas successful episode
`7000005` started collision free. A disabled candidate therefore checked
robot/parcel collision pairs before integration and selected one fixed fallback
qpos only for colliding scenes.

On the matched single-Radeon episodes `7000000`--`7000019`, the candidate used
the fallback in 14/20 episodes and verified zero collision pairs afterward.
Success rose from 1/20 to 5/20 and force aborts fell from 12/20 to 8/20, with
no regressions or drops. It still failed the 90% success and 5% force-abort
gates, so the feature remains disabled. Evidence is indexed under
`evidence/expert/radeon-contact-link-diagnostic-v1-*` and
`evidence/expert/radeon-collision-checked-reset-ab-v1-*`.

Balanced RGB-D collection and learned-policy ranking remain blocked. The next
candidate must generate reset and grasp poses that are feasible for each
sampled parcel geometry, then pass the same safety gate before ACT, Diffusion,
3D policy, VLA, or ROS 2 work resumes.

## Latest eliminated candidate: surface-aware pregrasp capture

A sequential Radeon probe tested whether high-carton approach stalls could be
accepted as valid side grasps. V1 regressed successful `7000005` to a 56.50 N
abort. V2 restricted the rule to cartons at least 150 mm high, preserved that
success, but converted timeout `7000000` into a 66.22 N force abort after two
retries. The candidate was stopped before formal A/B and remains disabled.

This closes the tolerance-based branch. The next candidate must synthesize an
IK- and collision-feasible pose rather than loosen completion semantics.
Balanced collection, policy training/ranking, VLA, and ROS 2 remain gated on
the expert reaching the fixed task and force thresholds.
