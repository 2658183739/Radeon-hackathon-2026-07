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
contact, and physical outcome. The original implementation assumed Genesis
depth was millimetres; a later source and data audit disproved that assumption.

**Alternatives.** State-only control, RGB only, or RGB-D plus proprioception and
contact.

**Decision and reason.** Capture RGB, raw metric depth, nine joint positions,
end-effector pose, target, contact force, and privileged parcel pose. Store
Genesis depth without rescaling and gate modality use through metadata audits.
Keep parcel pose out of learned policy input.

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
LeRobot episodes with 11,753 RGB/state frames. Its depth is invalid for RGB-D;
the corrected multimodal path has separate smoke evidence.

**Revisit trigger.** Failed data may be used later for value, recovery, or
preference learning, but not silently mixed into behaviour-cloning targets.

## Step 10: establish a task baseline before training

**Question.** When is the system ready for learning?

**Evidence.** Training cannot fix broken IK, contact detection, unit conversion,
or bin geometry.

**Alternatives.** Start model training immediately, or gate it behind a working
deterministic task.

**Decision and reason.** Require a successful nominal pipeline, randomized
expert metrics, audited sensor data, and reproducible failures before training.

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

## Implementation session record: balanced collection and compact Diffusion

### 17. Expand the training catalog without inventing carrier standards

Catalog v2 adds twelve weighted training strata with a 20-episode exact block:
micro box (1), small carton (3), flat mailer (2), book box (2), medium carton
(3), shoe-box proxy (2), long carton (2), large narrow carton (1), upright
canister (1), mailing tube (1), near-limit box (1), and electronics box (1).
The dimensions are explicitly Panda-aperture engineering strata. USPS profiles
retain exact dimensions, source URLs, and `evaluation_only=true` when the
parallel jaw cannot physically grasp them. Decision: **keep**, pending balanced
Radeon collection and multi-seed results.

### 18. Make hard-example collection deterministic and non-destructive

`episode_plan.py` gives each selected profile a million-index namespace and
keeps the unfiltered contiguous range unchanged. `run_expert.py` and
`evaluate_act.py` accept repeatable `--profile`; with a filter, `--episodes`
means episodes per profile. The JSONL writer now refuses to overwrite an audit
episode. Decision: **keep**. This supports data aggregation without silently
mixing or replacing provenance; each LeRobot shard still uses a new output
directory.

### 19. Expose only real LeRobot 0.6.1 optimization variables

ACT exposes seed, chunk size, executed action steps, model width/layers, and
optional temporal ensembling (guarded because LeRobot requires one action step
for that mode). Diffusion exposes seed, horizon, observation/action steps, UNet
widths, scheduler, inference steps, AMP, and compilation. A Bash preflight
checks the Diffusion horizon/downsampling invariant. Decision: **keep**; the
defaults preserve previous behavior.

### 20. Run the compact Diffusion training smoke on Radeon

The first retry passed three list tokens to the dynamic LeRobot CLI and stopped
before model creation. The script was corrected to pass one list-valued argument
(`"[256,512,1024]"`). The repeated run completed one forward/backward/update
step on the single `gfx1100` Radeon, produced a 76,597,288-parameter checkpoint,
and took 23.60 seconds in the training progress (41.10 seconds including
setup). The artifact and hashes are in
`evidence/training/diffusion-compact-1step-rocm.md`. Decision: **keep the
parameterization; repeat with a real budget and closed-loop evaluation before
selecting the compact model**.

### 21. Classify verification environment honestly

The Windows development host has only the Microsoft Store Python shim, so local
Python tests could not start. The same change set was copied to the configured
Radeon host, where 56 unit tests, Python compilation, Bash syntax, and CLI help
all passed. Decision: **record the host limitation, keep Radeon as the source
of truth, and add a Windows setup note before asking contributors to run tests**.

### 22. Treat catalog v2 smoke as a regression artifact, not a success claim

**Evidence:** one deterministic episode per profile gave 8/12 completion on the
Radeon. Medium and shoe-box profiles hit the 35 N boundary, the large narrow
carton timed out in approach, and the mailing tube rolled away. **Decision:**
keep the profile-level JSON and report it only as a smoke/regression result.
Formal claims require repeated seeds and a predeclared held-out episode set.

### 23. Reject height-aware and seated-grasp control candidates

**Evidence:** the height-aware candidate added no successful profile. The
post-close seating candidate added no success and reached 51.10 N, 51.64 N,
and 48.33 N on the targeted boxes. **Decision:** restore the original expert
control and retain both traces as negative evidence. A candidate must improve
task completion without crossing the fixed safety limit to become a default.

### 24. Keep rolling friction as a physics correction, not a grasp claim

**Evidence:** the baseline horizontal tube drifted about 4.2 m without finger
contact. Genesis 1.2.3 required both rolling and torsional friction flags. With
rolling friction 0.002, drift fell to 18.3 mm but a single finger still hit at
79.27 N. A 0.005 candidate reduced short-horizon drift to 3.3 mm but still
aborted at 73.99 N. **Decision:** keep the solver support and 0.005 catalog
value as a physical-model candidate; do not call it a manipulation success.

### 25. Reject single-episode control overrides and change the system boundary

The 2.5 mm and 2.0 mm final-approach overrides produced 36.74 N and 98.83 N.
A 5 mm XY tolerance produced zero contact but timed out while tracking the
moving object. **Decision:** remove all three overrides. The next justified
change is a staging cradle or a gripper designed for cylindrical parcels,
followed by multi-seed validation; further magic constants are not justified.

### 26. Current acceptance gates

No learned policy is promoted until it has: a frozen dataset split, at least
three training seeds, held-out closed-loop evaluation, per-profile results,
fixed safety thresholds, device-synchronized latency samples, and a
reproducible command plus artifact hash. A one-step Diffusion run and a
single-profile expert smoke remain pipeline evidence only.

### 27. Scope a physics feature after a regression

**Evidence:** global rolling/torsional friction changed the catalog from 8/12
to 6/12 and introduced failures for `micro_box` and `electronics_box`. The
scoped implementation enables the solver path only for horizontal cylinders
with a positive coefficient; the 58-test suite passed and the full catalog
returned to 8/12. **Decision:** keep the scoped implementation and retain the
global run as a negative regression artifact. This is the required rollback
pattern for a cross-cutting simulation feature.

### 28. Correct cylinder geometry before policy tuning

**Evidence:** horizontal-cylinder radius and spawn height came from independent
radial samples, creating an artificial drop. Axis-aligned grasp yaw also cut
the diagnostic peak from 72.92 N to 43.54 N. **Decision:** keep canonical
cylinder dimensions, radius-derived spawn height, and axis-aligned fingers.

### 29. Add profile-scoped contact controls

**Evidence:** a 5 mm final approach passed at 34.26 N; a 10 mm lift request and
three stable-contact frames improved the lift trace. High-friction pads reduced
the peak to 15.62 N. A 10 mm close tolerance then lifted the tube center by
35.5 mm. **Decision:** keep the explicit profile fields and their validation;
do not claim complete manipulation.

### 30. Remove the rejected close-force API

**Evidence:** 25 N and 35 N commands added at most 3.5 mm of partial lift,
crossed the measured 35 N boundary, and did not complete the task. **Decision:**
remove the field, configuration, and tests instead of preserving an unused
experimental knob.

### 31. Scope stability after cross-profile regression

**Evidence:** global three-frame stability changed the catalog smoke from 8/12
to 5/12. A profile override restored the exact 8/12 outcome with 67 tests
passing on Radeon. **Decision:** default to one frame and use three only for
mailing tubes. Retain both full-catalog artifacts as rollback evidence.

### 32. Correct depth scale before multimodal training

**Problem.** The historical dataset declared metric depth but its median was
0.00117156 m, physically inconsistent with the camera pose. **Evidence.** The
source multiplied Genesis output by 0.001, while upstream camera near/far and
point-cloud reconstruction use metres. **Alternatives.** Edit metadata, rescale
old encoded frames, ignore depth, or fix collection and recollect. **Decision.**
Do not fabricate a retroactive repair. Keep the 96-episode shard for RGB/state,
hard-reject it for RGB-D, and collect corrected raw depth plus a deterministic
three-channel view. **Code.** Added metric preservation, dataset audit, derived
depth feature, checkpoint-driven multimodal inference, and ACT/Diffusion depth
switches. **Verification.** Seventy-one tests passed; a new 152-frame shard had
0.737-3.535 m depth and passed audit; a 51,577,736-parameter RGB-D ACT completed
one Radeon update, saved/reloaded, and ran one closed-loop episode. The episode
failed and remains interface evidence only. **Decision: keep the pipeline;
recollect balanced data before any modality capability claim.**

### 33. Select the next model by task and license constraints

**Evidence.** ACT and compact Diffusion already use the pinned open LeRobot
stack. OpenVLA weights inherit Llama 2 terms; openpi explicitly requires an
NVIDIA GPU; SmolVLA checkpoint metadata did not declare a license. VLA-Adapter
uses a 0.5B backbone and its code, base, and sampled checkpoints are tagged MIT,
but its official setup remains CUDA-oriented. **Decision.** Train matched ACT
and Diffusion first. Use VLA-Adapter only for a separate ROCm and transitive-
license spike; do not place it on the reproducible path until both pass.

### 34. Add industry-size boundary profiles without contaminating training

**Problem.** The project needed evidence about realistic large cartons, flat-rate
mailers, and cylindrical parcels, while the current parallel gripper cannot
honestly claim to manipulate all of them.

**Alternatives.** Put the dimensions into the training distribution, omit them,
or add explicitly sourced evaluation-only profiles with the required end-effector
class.

**Decision.** Add five catalog v2 boundary profiles with `evaluation_only=true`
and `selection_weight=0`. Box profiles are marked `suction_required`; the large
cylinder is marked `cradle_required`. Official carrier URLs are retained, and
the profiles are excluded by the expert collector unless an explicit evaluation
flag is provided.

**Code capability.** Configuration validation, source provenance, handling-class
contracts, profile filtering, and tests that protect training/evaluation
separation.

**Verification.** The local suite passes the profile shape, handling class,
evaluation flag, source URL, and dimension-boundary checks. Suction and cradle
execution remain unimplemented and are not reported as current abilities.

**Revisit trigger.** Implement and validate the corresponding end effectors,
then run a new fixed held-out evaluation; do not silently change the existing
parallel-gripper baseline.

### 35. Report uncertainty for success, recovery, and drop metrics

**Problem.** Point estimates hide uncertainty, especially when a candidate has
few retries or no retry episodes at all.

**Alternatives.** Keep percentages only, use a normal approximation, or use a
Wilson score interval with an explicit zero-trial state.

**Decision.** Add Wilson 95% interval fields for success, first-attempt success,
recovery, and drops. A zero-trial recovery denominator returns `[0, 1]` while the
displayed recovery point estimate remains `0.0`; this means “not observed,” not
“stable zero recovery.”

**Code capability.** Numerically stable statistics, input validation, typed
summary fields, and focused unit tests for bounds and invalid arguments.

**Verification.** The test suite covers bounded intervals, zero trials, invalid
success counts, and non-positive/non-finite z scores. Reports must include the
interval fields alongside the numerator and denominator.

**Revisit trigger.** If the competition report requires a different confidence
level or hierarchical profile model, add it as a versioned analysis rather than
overwriting existing summaries.

### 37. Freeze an explicit split before model comparison

**Problem.** LeRobot's default `eval_split` holds out the last episodes per
task, which is deterministic only if the input episode list is fixed. It does
not by itself preserve the original catalog episode IDs or a separate held-out
closed-loop set.

**Alternatives.** Accept the implicit split, copy a new dataset for each seed,
or build one manifest that maps audit IDs to compact LeRobot indices and feeds
the same list to every run.

**Decision.** Add `dataset_split.py` and `build_dataset_split.py`. The builder
requires a completed summary, matches audit and metadata counts/order, rejects
multi-task data in schema v1, stratifies by profile with a stable SHA-256 key,
and emits train, validation, and held-out indices. Training scripts accept
`DATASET_SPLIT_MANIFEST`; validation is the final segment of the explicit
episode list and held-out episodes are never passed to LeRobot.

**Code capability.** Dataset lineage, deterministic stratified sampling,
subprocess-safe CLI argument generation, leak checks, and failure-fast data
contracts.

**Verification.** The local suite increased to 76 tests and passed; the
splitter tests cover determinism, profile coverage, count mismatches,
incomplete collections, duplicate indices, and held-out leakage. Radeon shell
validation is run after synchronization.

**Revisit trigger.** A multi-task VLA dataset requires a versioned schema that
stratifies by task and profile and updates the LeRobot factory semantics; do not
silently reuse schema v1.

### 38. Make the model sweep sequential and failure-preserving

**Problem.** Running every candidate by hand makes it easy to change a seed,
modality, budget, or split without recording the change, and concurrent jobs
would compete for the single Radeon.

**Decision.** Add run_model_sweep_rocm.sh with fixed default seeds 11, 22, and
33. It runs ACT RGB/RGB-D first, optionally adds compact Diffusion, executes one
job at a time, and records a CSV status plus a separate log for every cell.
Failed cells are retained and later cells still run.

**Code capability.** Reproducible experiment orchestration, environment
propagation, single-device scheduling, and failure-tolerant result collection.

**Verification.** The new script passes shell syntax validation; actual model
cells remain gated on the completed frozen dataset and are not counted until
closed-loop evaluation finishes.

**Revisit trigger.** Add a candidate only when its input contract, license,
ROCm execution, and evaluation adapter are recorded in the model matrix.

### 36. Keep catalog counts consistent across submission documents

**Problem.** Catalog v2 now contains twelve training profiles and nine
evaluation-only profiles, but several older documents still stated “four
boundaries.”

**Decision.** Update the current README, technical report, dataset card, and
component matrix to state nine evaluation-only profiles, with four inherited
profiles and five newly sourced boundaries. Historical journal entries retain
their original wording when they describe an earlier snapshot.

**Code capability.** Configuration-to-document consistency review and explicit
distinction between a current state and a historical experiment snapshot.

**Verification.** The TOML parser reports 21 profiles: 12 training and 9
evaluation-only. The changed documents use the same current count.

**Revisit trigger.** Any future catalog addition must update the parser-backed
count and the current status documents in the same commit.

### 39. Add a bilingual engineering playbook

**Problem.** The project had separate roadmap, decision, and development
documents, but a learner still had to infer the complete path from requirement
to release.

**Alternatives.** Add another narrative summary, duplicate the existing logs,
or create a short method document that links to the source of truth.

**Decision.** Add paired `ENGINEERING_PLAYBOOK.md` and
`ENGINEERING_PLAYBOOK_CN.md`. The playbook defines capability states, the
contract-first/test-first workflow, one-variable experiments, task/safety/
performance/reproducibility gates, the code capability map, and a release
checklist. Raw measurements remain in the journals and `evidence/`.

**Code capability.** Documentation indexing, bilingual parity, a standard
experiment record schema, and explicit boundaries for verified, smoke-only,
and planned capabilities.

**Verification.** Both files are linked from the repository README and the
documentation index. Local validation completed with 76 unit tests, Python
compilation, and whitespace checks. The remote collection is still running,
so no unverified training result is added to the claims.

**Revisit trigger.** Update the playbook when the acceptance gates, model
matrix, or deployment contract changes; do not rewrite historical evidence.

### 40. Enforce matched, profile-balanced checkpoint selection

**Problem.** A checkpoint rank could combine disjoint episode sets, use a
different force threshold, and win on aggregate success while failing one
important parcel profile.

**Decision.** Reject mismatched episode sets and safety thresholds. Add Wilson
95% intervals, per-profile counts, macro profile success, and safety-violation
rates. Canonicalize each randomized sample into a SHA-256 evaluation fingerprint
so equal episode IDs with different conditions are rejected. Rank safety first,
then macro profile success, overall success, drops, latency, and peak force.

**Verification.** The local suite increased to 81 tests and passed. Existing
historical summaries are not rewritten; they must be reprocessed only when
their raw episode sets and threshold metadata satisfy the new contract.

**Revisit trigger.** If evaluation becomes multi-task, version the manifest
schema and macro aggregation rather than mixing task and profile averages.

### 41. Gate unsupported end-effectors before simulation

**Problem.** Catalog v2 includes real-world boundary profiles labelled
`suction_required` and `cradle_required`, while the current Genesis scene only
contains the Panda parallel jaw gripper. Letting those profiles reach the
scene would produce a misleading result under the wrong tool.

**Alternatives.** Silently run every profile with parallel jaws; remove the
boundary profiles; or add an explicit capability registry and fail early.

**Decision.** Add a small capability module with `parallel_jaw` as the only
implemented class. `GenesisParcelEnv` checks the sample before Genesis
initialization and raises an actionable error for unsupported classes. The
catalog remains useful for documented evaluation boundaries without changing
the training distribution.

**Code capability.** Contract-first runtime validation, capability registry
design, and prevention of invalid benchmark claims before expensive simulation.

**Verification.** Added unit tests for the supported class, actionable failure,
and explicit registry extension. The capability contract is documented in
English and Chinese. Existing parallel-jaw collection paths are unchanged.

**Revisit trigger.** Enable suction or cradle only after adding versioned
geometry, a control adapter, reset/release behavior, tool-specific safety
metrics, balanced splits, and a ROCm closed-loop report.

### 42. Preserve failed model-sweep cells and make retries explicit

**Observation.** The first post-collection sweep exposed a deployment issue:
the Windows-to-Radeon copy preserved a UTF-8 BOM in `run_model_sweep_rocm.sh`,
and failed LeRobot cells left output directories that blocked a retry with
`resume=false`. The dataset and model code were not implicated.

**Decision.** Remove the BOM and add `MODEL_SWEEP_OUTPUT_ROOT` to the watcher.
Retries must use a new output root, while the failed directory and status CSV
remain untouched as negative evidence.

**Code capability.** Cross-platform shell portability, failure-preserving
experiment orchestration, and explicit artifact namespace management.

**Verification.** The corrected script begins with a plain `#!` shebang and
the watcher accepts an alternate output root. A retry is launched only after
the corrected script is copied to the Radeon environment.

**Revisit trigger.** If automatic resume is introduced, it must validate the
checkpoint/config hash before reusing an existing cell; never silently mix
different seeds, modalities, or dataset manifests.

### 43. Let LeRobot own fresh checkpoint directories

**Observation.** The BOM-corrected retry still failed before training because
the sweep helper created each cell's output directory. LeRobot 0.6.1 treats an
existing directory with `resume=false` as a protection against accidental
overwrite.

**Decision.** The sweep now creates only the matrix root and passes a fresh
cell path to LeRobot. Failed cell directories remain untouched; a retry gets a
new matrix root rather than changing resume semantics.

**Code capability.** Correct ownership of artifact lifecycle between shell
orchestration and the training framework, with explicit retry isolation.

**Verification.** Shell syntax remains valid and the retry uses a new matrix
root whose cell paths do not exist before `lerobot-train` starts.

**Revisit trigger.** If a framework changes its directory contract, add a
preflight assertion that reports the exact path and resume mode before launch.

### 44. Separate a short smoke budget from the formal training budget

**Observation.** The corrected ACT pipeline reached real Radeon training, but
30,000 steps per cell would take hours before exposing a later checkpoint or
evaluation integration issue.

**Decision.** Run a five-thousand-step, three-seed RGB/RGB-D smoke matrix in a
new output root first. Treat it only as an integration and checkpoint
artifact test. Keep 30,000 steps as the formal budget, and do not select a
model from the smoke matrix without the fixed held-out closed-loop evaluation.

**Code capability.** Budgeted experiment staging, single-GPU scheduling, and
clear separation between pipeline validation and scientific comparison.

**Verification.** The existing sweep already accepts `MODEL_SWEEP_ACT_STEPS`;
the retry is launched with `MODEL_SWEEP_ACT_STEPS=5000` and a new artifact
namespace.

**Revisit trigger.** Promote a smoke cell to formal training only after it
produces a loadable checkpoint and passes the same data, safety, and evaluation
contracts as the 30K run.

### 45. Preserve caller-provided watcher configuration

**Observation.** The first bounded retry still received 30K steps because the
watcher assigned defaults before reading its environment. The assignment
overwrote the caller value, so the later `printenv` read returned the default.

**Decision.** Replace the assignment-plus-read pattern with POSIX parameter
defaults (`${VARIABLE:-default}`) for polling, model list, seeds, and step
budget. Caller-provided configuration now has precedence.

**Code capability.** Reliable environment-based configuration with explicit
defaults, which is required for reproducible smoke versus formal experiment
budgets.

**Verification.** The corrected watcher is copied before the next retry; its
command configuration will be verified from the LeRobot log before claiming
the bounded run has started.

**Revisit trigger.** Add a machine-readable resolved-config JSON at every
run root if the sweep grows beyond its current environment-variable interface.

### 46. Use trace attribution to choose the first controller intervention

**Evidence.** The completed 400-attempt Radeon run contains 190 successes and
161 force violations. Of those violations, 104 are attributed to the approach
stage and 22 already exist in the initial state. The worst profile,
`large_narrow_carton`, has 2/20 success and 17/20 force aborts. Three of its
initial-state examples reached 95.65 N, 351.76 N, and 2761.74 N.

**Alternatives.** Increase the 35 N limit; tune grasp force; collect more data;
train a larger policy; or first eliminate reset and approach collisions.

**Decision and reason.** Keep the safety threshold fixed. Test a configurable
high-clearance home pose and geometry-aware approach as the first controller
candidate. High force occurs before learning can help in many episodes, so
collecting or training now would preserve unsafe demonstrations. Grasp-force
tuning does not target initial or approach-stage contact.

**Acceptance.** Use identical episode IDs, catalog, force limit, runtime, and
seed. Accept only if force aborts decrease without worse task success, drops,
timeouts, or material throughput regression; then run the complete catalog.

**Limit.** The factor table is observational. It prioritizes experiments but
does not establish that mass, size, pose, or friction caused a failure.

### 47. Keep reset-pose screening separate from Radeon acceptance

**Evidence.** A CPU screen on one fixed `large_narrow_carton` episode rejected
pose A: it changed a baseline success into a 50.36 N safety abort. Pose C
completed the same episode with 10.86 N peak force versus 32.24 N for the
baseline.

**Decision.** Keep pose C as a held candidate and leave the default unchanged
until the single Radeon device is free. This avoids promoting a CPU-only result
to competition evidence and makes the next run a clear one-variable A/B test.

**Revisit trigger.** Run identical Radeon episodes with the same 35 N limit,
then require no success or throughput regression and a full catalog check.
