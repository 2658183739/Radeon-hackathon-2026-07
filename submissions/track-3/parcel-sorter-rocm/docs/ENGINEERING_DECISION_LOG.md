# Engineering Decision and Learning Log

## Preface

This document is an auditable engineering rationale, not a transcript of hidden
private chain-of-thought. It records the information that a reviewer, teammate,
or learner can verify: problem statements, evidence, alternatives, selection
criteria, decisions, trade-offs, code boundaries, tests, and conditions for
revisiting a decision.

The format combines three current practices:

- **Architecture Decision Records (ADR):** document consequential choices and
  their consequences.
- **Reproducible ML experiment records:** bind code, data, seeds, hardware,
  metrics, and artifacts.
- **Test-driven risk control:** add tests and acceptance thresholds in
  proportion to behavioural risk.

## How to read each step

Every step contains:

1. **Question:** what needed to be decided.
2. **Evidence:** facts available before the decision.
3. **Alternatives:** credible options, not straw men.
4. **Decision and reason:** the selected option and explicit trade-off.
5. **Code capability:** the engineering technique demonstrated.
6. **Verification:** how the result is checked.
7. **Revisit trigger:** evidence that would justify changing the decision.

## Step 1: translate the competition rules into system invariants

**Question.** What is mandatory, and what is optional?

**Evidence.** The track requires AMD Radeon and ROCm, open-source simulation and
models, one-GPU execution, source and reproduction instructions. Simulation,
learning, robustness, closed loop, GPU optimization, and multimodal sensing are
capability categories; a submission does not need to maximize all six equally.

**Alternatives.** Build a broad six-feature demo, or build one complete
manipulation workflow with measurable depth.

**Decision and reason.** Choose one end-to-end parcel-sorting application and
make the Radeon/ROCm path an executable invariant. Depth produces stronger
evidence than six disconnected demonstrations.

**Code capability.** Requirements decomposition, invariant design, CLI
preflight validation, and traceable competition-to-component mapping.

**Verification.** `preflight_radeon.sh` rejects non-HIP PyTorch and anything
other than one visible GPU. The report maps components and evidence to scores.

**Revisit trigger.** Only expand scope after the primary task has a stable
held-out success rate and a reproducible training pipeline.

## Step 2: choose the robot form and application

**Question.** Should the project use a humanoid, mobile robot, or arm?

**Evidence.** Time is limited; parcel sorting needs contact-rich interaction,
clear business value, visible task success, and available open robot assets.

**Alternatives.** Humanoid whole-body manipulation, mobile navigation plus arm,
or a fixed Franka workcell.

**Decision and reason.** Use a Franka Panda for a fixed two-bin parcel sorter.
It isolates the manipulation problem, has mature MJCF assets, and allows the
submission to invest in sensing, recovery, learning, and GPU evidence. A
humanoid would add balance and locomotion failure modes without improving the
core parcel-handling evidence in the available schedule.

**Code capability.** Scope control and selection of a robot morphology that
matches task risk.

**Verification.** The complete pick, lift, transport, release, and bin-check
sequence runs in Genesis and produces MP4 evidence.

**Revisit trigger.** Add a mobile base only when the fixed workcell exceeds its
task target and navigation is required by a new application scenario.

## Step 3: select and pin the open-source stack

**Question.** Which simulator and learning framework minimize platform risk?

**Evidence.** Genesis exposes `gs.amdgpu`; LeRobot provides standardized robot
datasets and ACT; PyTorch ROCm is installed on the competition image.

**Alternatives.** MuJoCo with custom GPU integration, Genesis, or a proprietary
simulator; custom policy code or LeRobot.

**Decision and reason.** Use Genesis, LeRobot, and PyTorch ROCm, pinning exact
source revisions. The choice gives an AMD-native simulation path and avoids
reimplementing a policy/data ecosystem. Pinning prevents an upstream update
from changing behaviour during judging.

**Code capability.** Dependency locking, license review, bootstrapping, and
reproducible Docker design.

**Verification.** `UPSTREAM_LOCK.json`, `THIRD_PARTY_NOTICES.md`, bootstrap
scripts, and a versioned ROCm Docker base image.

**Revisit trigger.** Update a dependency only in a separate branch after the
same smoke tests, unit tests, and task regression set pass.

## Step 4: define contracts before simulator details

**Question.** How can expert, ACT, future VLA, dataset, and simulator code remain
replaceable?

**Evidence.** Learned policies and scripted control need different internals but
share observation and action semantics.

**Alternatives.** Pass raw simulator objects throughout the code, or define
small immutable application contracts.

**Decision and reason.** Define `RobotState`, `Observation`, `ControlDecision`,
`CartesianAction`, `TrajectoryFrame`, and `PolicyContext`. Immutable typed
contracts reduce accidental coupling and make unit tests possible without GPU.

**Code capability.** Interface segregation, dataclasses, protocol-based policy
substitution, and testable architecture.

**Verification.** Dataset, policy, runner, and state-machine tests construct the
same contracts without importing Genesis.

**Revisit trigger.** Version the contracts when a new sensor or action changes
stored data compatibility; do not silently change vector order.

## Step 5: build deterministic domain randomization

**Question.** How can robustness be tested while every failure remains
reproducible?

**Evidence.** Global random state makes a failed scene difficult to replay.

**Alternatives.** Fixed scenes, untracked global randomness, or a deterministic
sample generated from a project seed and episode index.

**Decision and reason.** Make each parcel sample a pure function of
`seed + episode_index * 1_000_003`. Randomize size, mass, friction, pose, camera,
delay, and destination within config-defined ranges.

**Code capability.** Deterministic random generation, configuration validation,
and failure replay.

**Verification.** Unit tests check repeatability and ranges; all summaries store
the sampled values and episode index.

**Revisit trigger.** Add a random dimension only with a realistic range and a
schema-compatible record in the summary.

## Step 6: build the simulator and multimodal observation path

**Question.** Which signals are needed for control, learning, and audit?

**Evidence.** Parcel manipulation needs visual geometry, robot state, target,
contact, and physical outcome. Genesis depth is returned in millimetres.

**Alternatives.** State-only control, RGB only, or RGB-D plus proprioception and
contact.

**Decision and reason.** Capture RGB, metric depth, nine joint positions,
end-effector pose, target, contact force, and privileged parcel pose. Convert
depth to metres immediately. Keep parcel pose out of learned policy input.

**Code capability.** Sensor-rate coordination, unit conversion, privileged-data
separation, and multimodal dataset schemas.

**Verification.** Shape/unit tests, dataset metadata, and a no-privileged-state
ACT feature declaration.

**Revisit trigger.** Add wrist sensing only if overhead-camera failure analysis
shows occlusion or pose ambiguity that depth cannot resolve.

## Step 7: put a deterministic supervisor around all policies

**Question.** Should a learned model own task progression and safety?

**Evidence.** Early policies are unreliable; contact, retries, release, and force
limits have deterministic semantics.

**Alternatives.** End-to-end raw torque policy, open-loop action replay, or a
learned Cartesian policy inside a deterministic supervisor.

**Decision and reason.** Use detect, approach, grasp, verify, lift, place,
release, complete, and abort stages. Keep retries and hard safety outside the
model. This hybrid design permits learning without allowing a malformed output
to bypass safety.

**Code capability.** Explicit state machines, defensive control, retry budgets,
and terminal-state modelling.

**Verification.** Tests cover success, failed grasp, retry exhaustion, contact
loss, release, and safety abort paths.

**Revisit trigger.** A learned supervisor may be tested later, but it must be
shadowed against the deterministic boundary before it can control safety.

## Step 8: create a geometry-aware expert

**Question.** How should demonstrations be generated before a visual model is
available?

**Evidence.** The simulator provides parcel truth; top grasps can exploit
parallel-jaw symmetry; direct diagonal motion can collide with the table.

**Alternatives.** Manually recorded teleoperation, direct point-to-point IK, or
a scripted transit/alignment/descent expert.

**Decision and reason.** Use a three-phase safe approach, canonicalize grasp yaw,
bound Cartesian steps, solve IK, execute arm PD, and ramp gripper force. The
expert may use truth to create labels, while the learned policy may not.

**Code capability.** Geometry, quaternion handling, IK integration, PD control,
force control, and separation between teacher privilege and student input.

**Verification.** Geometry tests, nominal GPU runs, randomized summaries, force
metrics, and video inspection.

**Revisit trigger.** Change grasp geometry only when failures are stratified by
size/yaw/position and the new method improves the same episodes.

## Step 9: retain success data and failure evidence separately

**Question.** Should failed trajectories enter imitation learning?

**Evidence.** Naive behaviour cloning treats recorded actions as targets; failed
expert actions can teach failure. Removing failure records would hide the most
useful engineering evidence.

**Alternatives.** Train on all attempts, delete failures, or train on successful
episodes while retaining every attempt in an audit format.

**Decision and reason.** Write successful episodes to LeRobotDataset and every
attempt to JSONL. This keeps imitation targets clean and preserves failures for
hard-example analysis.

**Code capability.** Dual-writer data pipelines, episode manifests, schema
validation, and failure provenance.

**Verification.** The formal run contains 120 audit episodes and 96 successful
LeRobot episodes with 11,753 RGB-D frames.

**Revisit trigger.** Failed data may be used later for value, recovery, or
preference learning, but not silently mixed into behaviour-cloning targets.

## Step 10: establish a task baseline before training

**Question.** When is the system ready for learning?

**Evidence.** Training cannot fix broken IK, contact detection, unit conversion,
or bin geometry.

**Alternatives.** Start model training immediately, or gate it behind a working
deterministic task.

**Decision and reason.** Require a successful nominal pipeline, randomized
expert metrics, correct RGB-D data, and reproducible failures before training.

**Code capability.** Staged delivery gates, smoke tests, metrics, and evidence-
based readiness criteria.

**Verification.** Radeon nominal, fixed-seed, 120-episode, video, and dataset
artifacts were generated before formal ACT training.

**Revisit trigger.** Pause model work whenever an environment or label bug is
found; regenerate affected data after fixing it.

## Step 11: choose ACT as the first learned policy

**Question.** Should the first model be a large VLA or a compact imitation
policy?

**Evidence.** The task has one instruction and continuous manipulation actions;
the dataset is small; the single Radeon must run training and inference.

**Alternatives.** ACT, Diffusion Policy, a large VLA, or a custom transformer.

**Decision and reason.** Start with LeRobot ACT. Action chunking is appropriate
for manipulation, implementation and checkpoints are available, and 52M
parameters fit comfortably. A VLA has little semantic work to perform in a
single-instruction task and would make data/debugging harder.

**Code capability.** Framework integration, feature declarations, mixed-
precision training, checkpointing, and safe policy adapters.

**Verification.** A 5,000-step ROCm run completed without NaN, saved checkpoints,
reloaded weights, and executed model-driven Genesis episodes.

**Revisit trigger.** Compare Diffusion or a lightweight VLA only after ACT has a
stable 30+ episode evaluation and the task includes meaningful language variety.

## Step 12: measure Radeon performance without confusing it with capability

**Question.** Which GPU measurements are meaningful?

**Evidence.** High simulation throughput does not imply successful robot
control; asynchronous timing can under-report inference latency.

**Alternatives.** Report a single peak number, or report separate physics,
training, inference, utilization, and task metrics.

**Decision and reason.** Sweep environment count, compare training precision and
batch size, synchronize inference timing, and retain `rocm-smi` snapshots.

**Code capability.** Benchmark design, device synchronization, P95 statistics,
and runtime provenance.

**Verification.** 128 environments reached 46,582 env-steps/s; AMP batch 32
reached 80 samples/s; ACT P95 was approximately 8 ms on measured ranges.

**Revisit trigger.** Optimize a component only after a full-frame profile shows
that it is material to end-to-end latency.

## Step 13: prevent biased checkpoint evaluation

**Question.** How should learned checkpoints be compared?

**Evidence.** The initial evaluator always started at episode zero; episode zero
is difficult. Step 4,000 and 5,000 also rank differently by task success and
offline loss.

**Alternatives.** Use final loss, evaluate one convenient seed range, or evaluate
deterministic disjoint ranges and aggregate exact task metrics.

**Decision and reason.** Add `--start-episode`, store the evaluated range, reject
overlapping ranges in aggregation, and rank success before latency. The model is
selected for the task it must execute.

**Code capability.** Evaluation protocol design, unbiased deterministic splits,
metric aggregation, overlap detection, and ranking rules.

**Verification.** Tests cover non-overlap, duplicate rejection, and success-
first ranking. Evidence includes identical episode 10-19 comparisons.

**Revisit trigger.** Increase evaluation size as model success rises; add
confidence intervals before making small percentage-point claims.

## Step 14: respond to the measured force failure

**Question.** How should 22 force-safety aborts be reduced?

**Evidence.** The failure concentration points to the final approach, while
raising the hard threshold would hide rather than solve impact.

**Alternatives.** Raise 35 N, slow all motion, reduce PD gains globally, or add a
phase-specific approach limit.

**Candidate and reason.** Add `final_approach_step_m = 0.01` only after
horizontal alignment. This is a narrow causal change and preserves free-space
speed.

**Code capability.** Phase-aware control, configuration invariants, narrowly
scoped behavioural changes, and regression tests.

**Verification.** Unit tests prove the slow limit activates only in final
approach. The same 120 Radeon episodes showed 75.0% success versus 80.0%, 25
versus 22 force aborts, and 73.6% throughput retention.

**Final decision.** Reject 0.01 m as the default and restore 0.04 m. Keep the
parameter and raw evidence so the failed hypothesis remains reproducible.

**Revisit trigger.** If force remains high, sweep the step limit and then add
force-aware velocity shaping; do not relax safety first.

## Step 15: treat image augmentation as an experiment

**Question.** Should generic image transforms be enabled by default?

**Evidence.** Synthetic data already has controlled appearance and camera
randomization. Some transforms can break action-label geometry.

**Alternatives.** Always on, always off, or configurable controlled ablation.

**Decision and reason.** Default off and expose `ACT_IMAGE_TRANSFORMS`. This
creates a falsifiable experiment rather than assuming that augmentation always
improves generalization.

**Code capability.** Experiment parameterization and single-variable ablation.

**Verification.** Train matched multi-seed runs and compare held-out closed-loop
success, not only loss.

**Revisit trigger.** Enable only the transforms that improve the held-out task;
record their exact parameters.

## Step 16: package the submission without hiding limitations

**Question.** What belongs in Git and what belongs in release storage?

**Evidence.** Source and small evidence fit Git; model and optimizer files exceed
normal GitHub limits; primary submission materials must be English.

**Alternatives.** Commit everything, omit evidence, or commit source/small raw
evidence and publish hashed large artifacts separately.

**Decision and reason.** Commit source, tests, bilingual docs, pinned container,
raw summaries, and logs. Keep large datasets/checkpoints out of Git and require
SHA-256 plus release links before the final PR. Report ACT's low success rate and
expert failure modes explicitly.

**Code capability.** Repository hygiene, artifact provenance, licensing,
technical writing, Git branching, and submission compliance.

**Verification.** Clean-directory Radeon tests, remote commit hash comparison,
sensitive-data scan, file-size scan, and a final checklist.

**Revisit trigger.** The final PR must be cut only after team identity, artifact
links, hashes, video, and a tagged-commit rerun are complete.

## Coding capabilities demonstrated

| Capability | Where it appears | General lesson |
| --- | --- | --- |
| Requirements engineering | preflight, report mapping | Convert prose rules into executable checks |
| Configuration design | `config.py`, TOML | Validate invariants at startup |
| Robotics control | expert, IK, PD, force ramp | Separate planning, control, and safety |
| State-machine design | `state_machine.py` | Make recovery and terminal paths explicit |
| Simulation integration | `genesis_env.py` | Isolate vendor APIs behind an application boundary |
| Dataset engineering | `dataset.py` | Preserve units, shapes, episodes, and provenance |
| ML integration | Generic LeRobot adapter and train scripts | Keep privileged truth out of model inputs |
| Evaluation science | metrics and aggregation | Use held-out task outcomes and detect overlap |
| Performance engineering | benchmarks and ROCm evidence | Profile end to end and time asynchronous devices correctly |
| Test engineering | `tests/` | Test deterministic logic without requiring a GPU |
| Reproducibility | locks, evidence, Docker | Bind claims to exact code, data, hardware, and hashes |
| Technical communication | bilingual reports and roadmap | Separate implemented facts, results, plans, and limitations |

## Standard workflow for the next change

1. State one measurable problem from evidence.
2. Write the baseline and acceptance threshold.
3. List credible alternatives and the smallest causal change.
4. Update config/contracts before scattering constants through code.
5. Add a deterministic unit or integration test.
6. Run the smallest smoke test.
7. Run the same-seed comparison on Radeon.
8. Inspect safety, task, and performance metrics separately.
9. Keep, reject, or repeat the change; record why.
10. Commit code, config, evidence, and documentation together.

This process is more valuable than copying a final patch because it explains
how to produce the next reliable patch independently.

## Implementation session record: 2026-07-24 optimization revision

| Sequence | Change or event | Decision / correction | Verification state |
| --- | --- | --- | --- |
| 1 | Audited 120-episode failures | Prioritize force aborts over a larger model | Evidence: 22/24 failures |
| 2 | Added `final_approach_step_m` | Limit only aligned descent; preserve transit speed | Unit test added |
| 3 | Added `ACT_IMAGE_TRANSFORMS` | Default off; require matched ablation | Shell syntax checked |
| 4 | Added checkpoint aggregator | Reject overlapping episodes and rank task success first | Three unit tests added |
| 5 | Added bilingual report, roadmap, log, and document pairs | English remains primary; Chinese is paired learning material | Link/file audit pending |
| 6 | First remote validation command failed | Local PowerShell expanded `$PWD` into a Windows path before SSH | No project code executed |
| 7 | Corrected remote quoting | Used a single-quoted remote command so Linux expands `$PWD` | 31 tests passed |
| 8 | Ran the aggregator on committed ACT evidence | Selected step 4,000 over 5,000 | 30% versus 10% |
| 9 | Ran same-index 120-episode expert regression | Compare causal change against original baseline | 75% vs 80%; rejected |
| 10 | Genesis segfaulted during shutdown | Separate runtime teardown failure from completed task output | Summary had all 120 episodes and was flushed before teardown |
| 11 | Restored baseline default | Keep 0.01 m only as a reproducible candidate | Comparison recommendation: `repeat_or_reject` |

The quoting failure is recorded because cross-shell automation is part of the
engineering process. It is classified separately from a code failure: the
command parser rejected an invalid environment assignment before tests ran.

## Implementation session record: catalog and policy revision

The follow-up revision added a weighted parcel catalog, Box/Cylinder spawn
mapping, profile-filtered evaluation, geometry-aware pregrasp windows, latched
final descent, and lift-transfer-descend motion. A complete remote run passed
48 unit tests and produced a seven-profile 20-second smoke artifact under
`evidence/catalog/`. Four box profiles completed; the micro box and two
cylinders remained hard cases. This is a regression smoke, not a statistical
success claim.

The generic checkpoint adapter was verified by loading an existing ACT checkpoint
on `cuda:0` (the ROCm/HIP device) and by running one Genesis closed-loop episode.
That episode was intentionally not promoted to an ACT success result.

The first Diffusion smoke stopped before model creation because the optional
`diffusers` package was missing. After installing LeRobot's pinned `diffusion`
and `smolvla` extras, one step completed and a checkpoint was saved on Radeon.
The result is recorded as a training-path smoke only. SmolVLA base probing then
showed that this instance cannot reach Hugging Face; its script therefore
requires an explicit staged local checkpoint instead of silently depending on
network access.
