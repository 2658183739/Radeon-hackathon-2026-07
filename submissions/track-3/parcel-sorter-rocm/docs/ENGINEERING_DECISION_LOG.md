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

### 48. Revalidate the complete configuration after CLI overrides

**Observation.** TOML loading validates the configuration, but `--reset-qpos`
replaces a field after loading. Python's `float` parser accepts `NaN` and
`Inf`, so load-time validation alone allowed non-finite joints to reach
environment initialization.

**Decision and reason.** Call `config.validate()` once all runtime overrides
have been merged, and report failures through `argparse`. The validation
boundary belongs at the final effective configuration, not only at source-file
parsing.

**Code capability.** Final-configuration contract enforcement, non-finite
numeric input protection, and fast failure before expensive simulation setup.

**Verification.** A CLI-level regression test supplies nine `NaN` values and
asserts exit code 2, an actionable message, and no `GenesisParcelEnv`
construction. All 88 tests pass on Radeon when the current project's
`PYTHONPATH` is explicit. The first test attempt accidentally resolved an old
editable install at `/workspace/parcel-sorter-rocm`; that was an environment
path mix-up rather than a code regression.

**Revisit trigger.** Any new CLI or environment-based override must preserve
the sequence: merge all overrides, validate once, then create side effects.

### 49. Freeze reset-pose A/B as a one-command protocol

**Problem.** Manually copying two long commands can omit the profile, episode
range, backend, or candidate joints. Reusing an old directory can also mix
artifacts and invalidate the comparison.

**Decision and reason.** Add `run_reset_pose_ab_rocm.sh` with one visible
Radeon, 20 fixed `large_narrow_carton` episodes, the baseline, pose C, and the
comparison tool. It rejects non-20-episode budgets and existing output roots,
then hashes both summaries and the comparison in `SHA256SUMS`. Freezing the
protocol reduces operator drift; refusing overwrite preserves negative results.

**Code capability.** Single-GPU experiment orchestration, environment
preflight, deterministic A/B execution, immutable artifact lifecycle, and
integrity hashes.

**Verification.** The script passes `bash -n` in the Radeon workspace. Its
formal run waits for the active ACT smoke process to exit so both workloads do
not contend for the GPU.

**Revisit trigger.** A changed sample count, target profile, or pose requires a
versioned protocol and output root rather than a silent v1 edit.

### 50. Treat the completed six-cell matrix as hashed integration evidence

**Evidence.** All ACT RGB/RGB-D combinations for seeds 11, 22, and 33 finished
5,000 steps with status 0 and produced `005000/pretrained_model` artifacts.

**Decision and reason.** Add a sweep evidence builder that reads each saved
`train_config.json` and policy config, verifies steps, seed, ACT, AMP, and the
exact visual inputs, then hashes the split, status CSV, logs, and every
checkpoint file. This is more reliable than scraping terminal progress text.

**Boundary.** The JSON explicitly says
`integration_smoke_only_not_model_selection`. The dataset remains unbalanced
and below the formal 300-success gate, so the six checkpoints are not ranked.

**Verification.** Six cells and six checkpoints passed; the evidence JSON has
SHA-256 `a144d87fe667c4ce1f5f34934747a7aa54e905106d73d97abe8db21d0362820a`.
The generator rejects an incomplete five-cell matrix. The full Radeon test
suite reached 90 passing tests before the subsequent comparison-contract test.

### 51. Reject reset pose C after matched Radeon A/B

**Evidence.** On identical episodes `7000000` through `7000019` and the same
35 N limit, the baseline completed 1/20 with 12 force aborts. Pose C completed
4/20 with 9 force aborts, recovered four baseline failures, and regressed the
baseline success at `7000005`. Peak force fell from 111.28 N to 85.90 N; both
runs had zero drops.

**Decision and reason.** Reject pose C and keep the historical default. It
improves descriptive metrics but fails both predeclared gates: at least 18/20
successes and at most 1/20 force abort. Its 4.35x throughput ratio is dominated
by the baseline having only one success and is not a standalone optimization
claim.

**Next intervention.** Keep reset pose as a controlled variable and test a
separate size-aware approach-clearance candidate. Do not bulk-collect new
demonstrations until the expert safety gate passes.

### 52. Require exact config differences and tolerate only verified post-summary cleanup failure

**Observation.** The candidate process wrote all 20 episodes and its complete
summary, logged normal Genesis shutdown, then exited with segmentation status
139 during cleanup. The original one-command runner therefore stopped before
comparison even though its scientific artifact was complete.

**Decision and reason.** The runner now accepts status 139 only when a strict
postcondition validates the expected count, unique episode IDs, evaluation
range, and profile. Missing or incomplete summaries still fail. The comparison
CLI also accepts an exact config-difference allowlist; reset A/B requires the
sole difference to be `control.reset_qpos`.

**Code capability.** Artifact postconditions, narrow handling of an upstream
cleanup fault, and machine-enforced single-variable experiment contracts.

**Verification.** The stored comparison reports exactly one config difference,
`control.reset_qpos`; all 91 tests and Radeon shell syntax validation pass.

**Revisit trigger.** Remove the status-139 exception when the pinned Genesis
runtime no longer crashes after complete summary emission. Never broaden it to
accept an incomplete run or a different exit status.

### 54. Reject the first size-aware approach candidate and fix detached-run logging

**Evidence.** On the same 20 Radeon episodes, the baseline completed 1/20 with
12 force aborts and a 111.28 N peak. The size-aware candidate (vertical-envelope
delta plus 20 mm margin) completed 0/20, kept 12 force aborts, raised the peak
to 304.67 N, and regressed baseline success `7000005`. It also had eight
approach timeouts versus seven and no lifted parcels. The comparison contains
exactly the two declared task-field differences and returns `repeat_or_reject`.

**Decision.** Reject the candidate and keep the feature disabled. The trace
shows the regression occurs after a lost-grasp retry: the parcel has moved, and
the retry enters approach before a safe recovery pose is established. Increasing
transit height is therefore not a sufficient fix and must not be swept blindly.
The next controller intervention is recovery-aware retry initialization, with
the same 35 N hard boundary.

**Operational fix.** Redirect each expert leg to a versioned run log inside the
output root. The previous detached SSH run produced a complete baseline summary
but lost the shell continuation after the remote stdout pipe closed, so the
candidate had to be launched manually. Future runs retain baseline and candidate
logs and hash them with the summaries and comparison.

**Revisit trigger.** Only revisit size-aware clearance after a recovery-policy
candidate has a matched experiment showing no retry regression; do not claim
this rejected result as an optimization.

### 55. Keep recovery-aware retry as a promising diagnostic, not a release change

**Evidence.** The matched 20-episode Radeon A/B changed only
`task.retry_retreat_distance_m` from `0.0` to `0.120`. The candidate improved
success from 1/20 to 2/20, recovered episode `7000014`, introduced no success
regressions or drops, reduced force aborts from 12 to 11, and retained 1.98x
of baseline throughput. Failure attribution moved from 12 to 11 force aborts
with the same seven approach timeouts.

**Decision.** Keep the implementation disabled by default and classify this as
a promising diagnostic. It still fails the absolute gates by a wide margin:
10% success and 55% force-abort rate are not deployable. The result justifies a
larger pre-registered recovery evaluation, not a default configuration change.

**Implementation.** Add `retry_retreat_distance_m`, a lateral separation step
used only when the supervisor increments `retry_count`; first attempts retain
the historical path. The CLI, validation, unit tests, fixed A/B runner, failure
analyses, compact summaries, logs, and hashes are all versioned.

**Revisit trigger.** Repeat on a larger fixed episode set only after the data
and safety protocol is predeclared. Promote the setting only if absolute
success, force-abort, drop, and profile-stratified gates pass; otherwise keep it
as a documented recovery component without claiming task readiness.

### 53. Implement a size-aware horizontal-transit candidate

**Problem.** The fixed `approach_clearance_m` is measured from the baseline parcel
center. For a substantially taller carton, the parcel's vertical envelope grows
while the robot crosses the workspace, reducing effective top clearance. A global
height increase would change every profile and make the result hard to attribute.

**Decision.** Add `TaskConfig.size_aware_approach_enabled` and
`approach_clearance_margin_m`. With the switch off, behavior is exactly the
legacy path. With it on, the expert adds only the current parcel's vertical
envelope delta over the baseline parcel, plus an explicit margin. Reset pose,
physics, grasp target, 35 N safety boundary, and random samples remain fixed.

**Implementation.** Centralize the geometry rule in
`ScriptedPickPlaceExpert.approach_clearance_m()`. Add CLI overrides that are
validated before Genesis construction, plus
`run_size_aware_approach_ab_rocm.sh`, which fixes 20 `large_narrow_carton`
episodes on one Radeon and allows exactly the two task-field differences in the
comparison contract.

**Acceptance.** The candidate must pass the fixed success, force-abort, drop,
and throughput gates before a full-catalog regression. Otherwise retain the
artifacts as evidence and keep the switch disabled. Record the command and
SHA-256 with the commit.

### 56. Reject the 20 mm approach-step candidate after matched Radeon A/B

**Question.** Would reducing every free-space `MOVE_PREGRASP` step from 40 mm
to 20 mm prevent the approach-stage failures observed in the
`large_narrow_carton` diagnostic profile?

**Controlled change.** Add `control.approach_step_m` and change only that value
for the candidate. The reset pose, physics, random episode IDs (`7000000`-
`7000019`), profile filter, 35 N contact-force limit, retry policy, and runtime
environment stayed fixed. The candidate was run on one AMD Radeon GPU through
ROCm with the same Genesis and PyTorch stack.

**Evidence.** Baseline: 1/20 successes, 12/20 force aborts, 0 drops, 111.28 N
maximum contact force. Candidate: 0/20 successes, 12/20 force aborts, 0 drops,
161.28 N maximum contact force. Failure analysis attributes both runs mainly to
approach timeouts and force safety aborts in `large_narrow_carton`; the
candidate also regressed episode `7000005`. The comparison returns
`repeat_or_reject` and records `control.approach_step_m` as the only config
difference.

**Decision.** Reject the candidate and keep the default at 40 mm. A smaller
step does not address the limiting failure mode and increases peak force in
this matched sample. Do not use this result to justify more data collection or
model ranking.

**Implementation and auditability.** Add the typed config field, CLI override,
validation, fixed A/B runner, trace-derived failure analysis, compact summary
writer, logs, and local/remote SHA-256 manifests. The compact artifacts omit
per-frame traces only; they retain the source summary path, byte count, digest,
runtime, configuration, randomization, and per-episode outcomes.

**Revisit trigger.** Reconsider approach-step changes only after a controller
change addresses the approach/retry state machine and passes the predeclared
absolute success, force-abort, drop, profile, and throughput gates on a larger
fixed set.

### 57. Reject the previous-frame contact-brake candidate

**Hypothesis.** Some failures in the 400-episode trace showed 20--32 N during
approach before crossing the 35 N hard limit. The candidate observes at least
20 N during `MOVE_PREGRASP` and commands at most 10 mm of separation before the
next transit command can press farther into the parcel.

**Controlled protocol.** Only `control.approach_contact_brake_force_n` changed,
to 20 N. The 10 mm brake step already equals the baseline default and is not an
observed config difference. Both runs used one Radeon, episodes `7000000`-
`7000019`, `large_narrow_carton`, the same 35 N boundary, and the same ROCm
runtime.

**Evidence.** Baseline and candidate both achieved 1/20 successes, 12/20 force
aborts, and zero drops. Candidate throughput was 1.047x baseline, but peak force
rose from 111.28 N to 467.31 N. Candidate episode `7000007` measured 0 N on the
previous frame and jumped directly to 467.31 N on the abort frame, leaving no
control frame in which the 20 N brake could act. The candidate only reduced
episode `7000014` from 37.20 N to 36.10 N, recovered no failures, and failed the
90% success and 5% force-abort gates.

**Decision.** Reject and keep the feature disabled. A low-rate, one-frame-late
force threshold is not a sufficient safety layer here. The next candidate must
act before collision using geometric proximity/predicted contact, or move force
limiting into a higher-rate compliant/impedance controller. Do not raise the
35 N hard limit or start the 360-success collection from this result.

**Implementation and auditability.** Retain the typed config, CLI, validation,
tests, and fixed A/B runner as a reproducible experiment component. Fix the
runner's exact difference contract to list only the field that actually changed.
Full summaries remain on the Radeon host; Git stores compact summaries, failure
analyses, logs, comparison, and local/remote SHA-256 manifests.

### 58. Reject the larger vertical recovery-step barrier candidate

**Diagnosis.** Baseline traces showed the end effector falling below
`parcel_z + approach_clearance_m` during horizontal approach even though the
nominal Cartesian target stayed at the transit height. The candidate borrowed
the safety-set idea from CBFs: while still away from the grasp center and below
that height, freeze horizontal motion and allow one vertical recovery step up
to 120 mm. It is disabled by default and does not affect final descent or retry
retreat.

**Evidence.** On matched Radeon episodes, candidate success fell from 1/20 to
0/20, force aborts remained 12/20, and both arms had zero drops. Candidate
episode `7000007` improved peak force from 56.76 N to 32.99 N but became an
approach timeout; more importantly, successful baseline episode `7000005`
regressed to a 42.43 N force abort. Approach timeouts rose from 7 to 8 and the
candidate failed the absolute success, safety, and throughput gates.

**Decision.** Reject and keep disabled. Enlarging a vertical recovery step can
change an individual impulse but breaks successful trajectories; it does not
replace a pre-contact constraint on finger geometry and IK/PD tracking. The
next candidate will use Genesis `get_AABB()` to estimate finger-to-parcel axis-
aligned clearance and filter horizontal motion only near the threshold. This is
an engineering safety filter, not a claim of formal CBF proof.

**Research basis.** The design was informed by arXiv:2503.06736 (Operational
Space CBF, MIT-licensed OSCBF), arXiv:2503.00623 (collision-cone CBF with
Cartesian impedance), and arXiv:2211.11391 (RL-enhanced CBF parameterization).
OSCBF depends on URDF/JAX and a hand-authored collision model, so it is not
directly imported into this Genesis/ROCm stack; only the auditable principle of
filtering a nominal controller through a safety constraint is retained.

### 59. Reject the pre-contact AABB guard after matched Radeon A/B

The candidate added a disabled-by-default `control.precontact_aabb_guard_distance_m`
and evaluated the closest GPU AABB gap between each Panda finger and the parcel.
It only filtered `MOVE_PREGRASP` actions when the end effector was outside the
position-tolerance descent window and the nominal target reduced horizontal
distance to the parcel. A low end effector was redirected vertically toward the
transit height; otherwise the action retreated away from the parcel. The 8-D
action contract, 35 N hard limit, final descent, grasp, lift, release, and retry
logic were unchanged.

The fixed single-Radeon protocol used `large_narrow_carton`, episodes
`7000000`--`7000019`, and identical seed, reset pose, physics, runtime, and
comparison rules. The 40 mm threshold triggered 65 filters across 6,003
pregrasp samples. AABB measurement and scalar synchronization averaged
1.625 ms per sample (9,755.57 ms total); the maximum consecutive filter span
was 16 control steps.

Baseline results were 1/20 successes, 12/20 force-safety aborts, 0 drops,
111.28 N peak force, and 17.81 successful parcels/hour. The candidate produced
0/20 successes, 12/20 force aborts, 0 drops, the same 111.28 N peak, and zero
throughput. Approach timeouts increased from 7 to 8; no failed episode was
recovered, and baseline success `7000005` regressed. Peak force improved in
three individual episodes, but no absolute task, safety, or throughput gate
passed except unchanged drop rate.

**Decision.** Reject and keep disabled. Retain the filter as an auditable
diagnostic because it runs on Radeon and records nominal/filtered targets, gap,
trigger reason, count, active duration, and synchronization cost. AABB overlap
is not a sufficient final-grasp safety signal. This result does not justify a
threshold sweep, balanced collection, or ACT/Diffusion/VLA ranking.

Evidence is indexed under `evidence/expert/radeon-approach-aabb-ab-v1-*`.
Complete remote summaries remain the provenance source; compact summaries
preserve the safety aggregate and source SHA-256. Validation reached 121 local
tests and 116 tests on Radeon, plus shell syntax checks.

### 60. Reject global approach-stiffness scaling after matched Radeon A/B

**Hypothesis.** The preceding geometric guards could not limit the first
collision impulse. Reducing arm proportional gains during `MOVE_PREGRASP` might
make contact less energetic without changing the 8-D policy action, gripper
gains, final grasp, or the 35 N hard abort. The candidate used 0.50 arm Kp and
`sqrt(0.50)` arm Kv so the nominal damping relationship was preserved. All
other commands restored the original gains, and the default scale remained
1.0.

**Protocol.** The single-Radeon A/B fixed `large_narrow_carton`, episodes
`7000000`--`7000019`, seed, reset pose, physics, runtime, and safety limit.
The comparison accepted exactly one difference:
`control.approach_stiffness_scale`. Probes eliminated 0.25 because it timed out
without contact; 0.50 preserved successful probe `7000005` and therefore
became the sole registered candidate.

**Evidence.** Baseline and candidate both achieved 1/20 successes with zero
drops and the same 111.28 N maximum contact force. Force aborts decreased from
12/20 to 10/20, mean episode peak force from 34.02 N to 28.53 N, and P95 from
98.12 N to 71.07 N. These were not task recoveries: approach timeouts increased
from 7 to 9, there were no recovered or regressed successful episodes, and
throughput fell from 17.80 to 13.36 successful parcels/hour (0.751x). The
candidate failed the 90% success, 5% force-abort, and 85% throughput gates.

**Decision.** Reject 0.50 as a default and keep `approach_stiffness_scale=1.0`.
Retain the typed setting, CLI, gain-switching implementation, tests, and runner
as an auditable negative control. Uniform joint-gain scaling trades force
aborts for tracking timeouts and cannot solve geometry, IK, and recovery
together. The next controller design should use Cartesian/operational-space
velocity or impedance limits near contact, with an explicit recovery state and
the same hard safety boundary, rather than sweep a global stiffness scalar.

Evidence is indexed under
`evidence/expert/radeon-approach-compliance-ab-v1-*`. Full trace summaries stay
on the Radeon host; Git contains compact summaries, comparison, failure
analyses, logs, and local/remote SHA-256 manifests. Remote validation passed
123 tests plus 6 subtests; the fixed A/B and both post-run analyses completed.

### 61. Reject approach-stage operational-space velocity control

**Hypothesis and implementation.** Joint-space stiffness scaling reduced some
forces but lost tracking authority. The next isolated candidate replaced IK
position commands only during `MOVE_PREGRASP` with a world-frame Cartesian
twist and weighted damped-least-squares joint velocity. Translation weight was
1.0, orientation weight 0.20, damping 0.05, and each joint was capped at
1.50 rad/s. Grasp, lift, place, the 8-D policy action, delayed-action path,
gripper control, and 35 N hard abort were unchanged. The feature defaults off.

**API and correction evidence.** Genesis 1.2.3 source and an on-device probe
confirmed that `get_jacobian()` rows 0--2 are translation and rows 3--5 are
rotation. An initial equal-weight controller over-prioritized orientation, so
the registered version used an explicit 0.20 orientation task weight. An
isolated `control_dofs_velocity()` check on Radeon produced about 1.03 rad/s
measured joint velocity and 25 mm end-effector descent, proving that the API
and Jacobian order worked. In the parcel scene, predicted downward motion
persisted while measured joint velocity fell near 0.005 rad/s: the non-finger
hand/carton geometry physically blocked descent. This separated an execution
failure from a numerical or API failure.

**Protocol and result.** The formal single-Radeon A/B fixed
`large_narrow_carton`, episodes `7000000`--`7000019`, seed, reset, physics,
runtime, and force threshold. The only accepted difference was
`control.approach_velocity_control_enabled`. Baseline achieved 1/20 success,
12/20 force aborts, 7 approach timeouts, zero drops, and 17.80 parcels/hour.
The candidate achieved 0/20, 13/20 force aborts, 7 timeouts, zero drops, and
zero throughput; it regressed `7000005`. P95 peak force improved from 98.12 N
to 67.55 N, but maximum force stayed 111.28 N. Across 5,727 controller samples,
mean synchronized compute time was 1.983 ms, maximum command 1.50 rad/s, and
maximum pose error 0.1817 m.

**Decision.** Reject and keep disabled. A controller that lowers a percentile
force metric while eliminating the only success and adding a force abort does
not pass the task, safety, or throughput gates. Keep the typed configuration,
controller, telemetry, comparison support, tests, and runner as a reproducible
negative control. The next justified intervention is an explicit
geometry-aware grasp pose and recovery-state redesign, not another velocity-
gain sweep. Evidence is under
`evidence/expert/radeon-approach-velocity-ab-v1-*`; formal Radeon validation
passed 128 tests plus 6 subtests.

### 62. Retain collision-checked reset as a disabled diagnostic

**Observation.** The velocity controller was numerically valid but physically
blocked. A new 240 Hz link diagnostic compared failed episode `7000001` with
successful episode `7000005`. The failed sample produced a hand/carton contact
on initialization substep zero at 1,270.85 N, while the successful sample had
no initialization contact and later reached only 17.12 N finger contact. The
failure therefore existed before the 30 Hz policy loop could react.

**Candidate and protocol.** Add a disabled-by-default collision check after
scene construction but before integration. If and only if the historical reset
intersects the sampled parcel, switch to one fixed fallback qpos and require a
second collision query to return no robot/parcel pairs. The fixed Radeon A/B
used `large_narrow_carton`, episodes `7000000`--`7000019`, identical seeds,
physics, controller, and 35 N limit. The only allowed config difference was
`control.collision_checked_reset_enabled`.

**Evidence.** The candidate checked 20/20 episodes and used the fallback in 14.
It detected 86 initial geometry pairs and zero after fallback. Success improved
from 1/20 to 5/20, force aborts from 12/20 to 8/20, with no successful-episode
regressions and no drops. Throughput rose from 17.80 to 97.00 successful
parcels/hour. Mean synchronized check cost was 3.707 ms per episode. However,
episode `7000001` still aborted at 37.37 N and the aggregate result remained
25% success with 40% force aborts.

**Decision.** Keep the implementation, telemetry, diagnostics, tests, and A/B
runner, but keep the feature disabled. It is causal evidence that reset-scene
intersection is one failure source, not proof that the task is deployable. It
fails the preregistered 90% success and 5% force-abort gates. The next candidate
must generate collision-free reset and grasp poses from sampled parcel geometry,
then redesign approach/recovery without weakening the 35 N hard stop.

Evidence is indexed under
`evidence/expert/radeon-contact-link-diagnostic-v1-*` and
`evidence/expert/radeon-collision-checked-reset-ab-v1-*`. The formal Radeon
checkout passed 134 tests plus 6 subtests; local/remote SHA-256 manifests retain
the complete provenance chain.

### 63. Reject surface-aware pregrasp capture before formal A/B

**Observation and hypothesis.** Seven remaining high-carton timeouts reached
within 40--50 mm above the nominal grasp centre with 0--5 mm XY error. A
height-bounded capture band might turn these stalled but aligned poses into
grasp attempts without admitting arbitrary early closure.

**Sequential design.** The treatment unit was one deterministic episode. Both
arms retained collision-checked reset; the only candidate flag was
`task.surface_aware_pregrasp_enabled`. The capture band required 15 mm XY
alignment, 20 mm minimum side overlap, and a 55 mm upper vertical cap. Probes
were ordered as preservation (`7000005`), target timeout (`7000000`), then
force-abort challenge (`7000001`). Any success regression or new force abort
stopped the sequence before the expensive matched A/B.

**Evidence and adaptation.** V1 applied to every non-flat box and immediately
regressed `7000005`: the historical 17.12 N success became a 56.50 N force
abort. V2 preregistered a 150 mm minimum carton height from the already observed
failure stratum, thereby preserving `7000005` and its 17.12 N peak. The next
probe still failed: `7000000` changed from a low-force approach timeout to a
66.22 N force abort after two retries. The challenge probe and 20+20 A/B were
cancelled, avoiding pseudoreplication and post-hoc threshold scanning.

**Decision.** Reject and keep disabled. Reclassifying a physically stalled pose
as “at pregrasp” changes state-machine timing but does not create a stable grasp
or collision-free retry. Keep the typed parameters, tests, and runner as an
auditable negative control. The next intervention must generate and validate a
reachable grasp pose, including palm/wrist/link clearance, before the supervisor
is allowed to close the gripper.

Evidence is under `evidence/expert/radeon-surface-aware-pregrasp-probes-v1-*`.
Radeon validation passed 140 tests plus 6 subtests; source and derived hashes
were verified. No formal success-rate claim is made from three single-episode
probes.

### 64. Retain geometry-aware grasp planning as the leading experimental path

**Observation.** Collision-checked reset removed initial intersections but left
high cartons without a shared, reachable grasp pose. Surface-aware completion
tolerance changed event timing and created unsafe closure. The controller needed
pose generation, feasibility checks, and consistent execution semantics.

**Hypothesis and implementation.** Generate box-relative pose candidates,
evaluate them with Radeon IK/FK, collision, Jacobian, state-restoration, and
clearance evidence, then bind one pose across approach, capture, grasp, and
lift. Scope the change to boxes at least 125 mm high so known lower-box success
paths remain byte-for-byte equivalent at the action level. Replan after retry.

**Alternatives considered.** Loosen pregrasp tolerance was already unsafe.
Raising the 35 N abort would hide rather than solve the failure. A swept
0.025-rad joint collision gate was implemented and measured, but it rejected
zero challenge waypoints, did not prevent six force aborts, and added up to
7.76 seconds per episode; keep it opt-in only. One global 5 mm or 2.5 mm
approach step was rejected because contact response was non-monotonic across
medium and tall boxes.

**Decision and reason.** Keep a two-stage planned approach: 5 mm for the active
125--160 mm band and 2.5 mm for boxes at least 160 mm high. The boundary is tied
to the 105 mm palm clearance plus 55 mm maximum vertical candidate offset. Keep
the entire planner disabled by default because the formal candidate reached
15/20 success and 4/20 force aborts, not the required 18/20 and at most 1/20.
This is the leading experimental controller and a valid competition result,
but not a deployable default.

**Evidence.** The exact-config, fixed-episode Radeon A/B recovered ten failures,
regressed none, kept zero drops, improved throughput by 3.66x, and reduced peak
force from 111.30 N to 46.99 N. Remaining failures are three approach-force
aborts, one lift-force abort, and one lost-grasp approach timeout. Evidence and
SHA-256 manifests are under
`evidence/expert/radeon-geometry-aware-grasp-planning-ab-v2-tiered-*`.

**Next decision gate.** Target low-box contact prediction, collision-free retry,
and lift retention on new preregistered probes. Do not fit more height thresholds
to the same 20 episodes. Expand to held-out shapes only after reaching 18/20
success and at most 1/20 force abort.

### 65. Freeze an unseen multi-profile screen before further controller tuning

**Problem.** The leading planner was developed against one 20-episode high-box
set. Reusing it would underestimate uncertainty and encourage threshold fitting;
immediately running hundreds of episodes without a frozen contract would create
expensive but weak evidence.

**Evidence and alternatives.** The catalog has 12 training profiles supported
by the current parallel-jaw end effector and nine evaluation-only profiles that
explicitly require suction or a cradle. Existing tooling had deterministic
profile namespaces and Wilson intervals, but no multi-group matched report,
exact paired test, or campaign runner. Alternatives were another single-profile
A/B, one unstratified random pool, or a balanced screen followed by a separate
confirmatory namespace.

**Decision and reason.** Freeze the balanced screen. Run historical control,
collision-checked reset, and complete geometry planning on the same five unseen
episodes for each supported profile. Treat the resulting 180 episodes as
exploratory elimination evidence. Reserve local episodes `200000`--`200039`
for later confirmation and keep all unsupported end-effector profiles outside
the denominator.

**Code capability.** `campaign_geometry_screen_v1.toml` freezes samples and
groups; `run_geometry_screen_campaign_rocm.sh` verifies and executes them;
`evaluation_statistics.py` reports Wilson intervals, exact McNemar tests,
paired bootstrap/sign-flip effects, per-profile strata, and planning overhead.
The tall-box tier now has an explicit ablation-only disable switch. None of
these changes alters the default controller or 35 N limit.

**Validation and revisit trigger.** Focused Radeon tests, Python compilation,
shell syntax, campaign fingerprinting, and a replay through the existing 20+20
artifacts must pass before launch. The method advances only if aggregate safety
does not regress and no profile loses more than one matched success. A formal
claim requires the untouched reserved namespace and a separately frozen primary
hypothesis.

### 66. Reject universal planning and develop a reset-risk gate

**Observed evidence.** The frozen 180-episode Radeon screen produced 38/60
successes and 15/60 force aborts for both collision-checked reset and complete
planning. Success and force-abort McNemar p-values were both 1.0. Planning added
1.65 N to mean episode peak force with a paired bootstrap 95% interval of
-1.67 to +5.99 N, and one planning attempt averaged 5.57 s. The complete method
therefore failed the preregistered aggregate safety and utility test.

**Failure attribution.** Of four success changes, only two episodes actually
ran the planner. Planning regressed `4100004 medium_carton` from a 6.05 N
success to a 54.78 N abort, while it recovered `7100002
large_narrow_carton` from a 36.59 N abort to a 9.23 N success. Two other changed
episodes never planned and showed state divergence before action divergence,
which requires execution-repeat analysis rather than a causal method label.

**Alternatives.** Enabling planning for every geometry-eligible box is rejected.
Fitting another height, length, or aspect-ratio threshold to five samples per
profile would be post-hoc overfitting. Removing planning would also discard the
measured recovery for an initially colliding narrow carton.

**Decision and reason.** Add a default-off reset-fallback risk gate. Planning
may activate only when geometry eligibility holds and collision-checked reset
actually detected an initial intersection and selected its verified fallback.
The gate reuses a measured causal precursor already available before the first
policy action, reduces unnecessary planning, and is auditable in telemetry.
The current screen is development data only; promotion requires new probes,
execution repeats, and a separately frozen validation namespace.

### 67. Freeze validation before measuring the risk-gated method

**Implementation evidence.** The gate is default off, requires both prerequisite
features, resolves after the reset collision query, and exposes eligibility,
satisfaction, activation, avoided work, attempts, and compute time. Local and
Radeon suites passed 183 and 178 tests. Three mechanism probes preserved two
non-risk successes with zero planning attempts and retained the intended
`large_narrow_carton` recovery with one planning attempt and a 9.23 N peak.

**Decision and reason.** Advance to a matched development validation rather
than replaying all 60 observed screening episodes. Freeze local IDs
`120000`--`120004` for all 12 supported profiles and compare collision-checked
reset against reset-risk-gated planning, for 120 episodes total. This namespace
was generated before viewing any of its physics outcomes. Keep
`200000`--`200039` untouched for final confirmation.

**Acceptance logic.** The validation is exploratory for method selection. It
must show no aggregate safety regression, no systematic ordinary-profile
regression, measurable avoidance of unnecessary planning, and at least one
repeatable hard-profile recovery before confirmatory evaluation. Because the
earlier trace audit found execution-level divergence, later confirmation must
also include 3--5 repeated executions per selected condition.

### 68. Reject the gate and make process position an experimental factor

**Observed evidence.** The frozen validation failed every advancement reason:
success fell from 35/60 to 33/60, force aborts increased from 17/60 to 19/60,
mean episode peak force increased by 6.67 N, and throughput fell to 0.910x.
All five geometry-eligible episodes also satisfied the reset gate, so the gate
avoided no planner work. The active subset contained one recovery and two
regressions.

**Attribution evidence.** Five nested repeats per condition reproduced both
active regressions and the active recovery 5/5. The inactive discordant episode
succeeded 2/5 under each method. All four successes occurred when that method
ran second in its block, revealing a process-local period/carry-over effect.
The repeat is descriptive: four unique episodes are the experimental units,
not the 40 executions.

**Alternatives.** Raising the 35 N threshold, fitting another geometry scalar,
or opening the reserved confirmation IDs would convert failure into post-hoc
selection and is rejected. Treating the 40 runs as independent would be
pseudoreplication. Repeating every observation in a fresh process would isolate
process initialization but adds substantial kernel-compilation cost; it is
retained only as a targeted sentinel reliability check.

**Decision and reason.** Keep reset-risk-gated planning disabled and seal the
confirmation set. Record process identity and within-process position in every
future simulator comparison, block and balance method order, and require
fresh-process repeats for selected discordant sentinels before causal promotion.
The next controller must redesign recovery state or grasp execution rather than
add another post-hoc eligibility threshold.

### 69. Reject the universal transport contract and prioritize grasp stability

**Observation and hypothesis.** All three repeatable planner-active episodes
selected a centered, canonical-wrist grasp 40 mm above nominal. The planner
proved IK/FK and static-collision feasibility but not loaded raise, transport,
and placement feasibility. The two regressions produced 159.27 N and 69.00 N
peaks during post-grasp execution, motivating a default-off staged transport
contract.

**Capability and ordered corrections.** The implementation adds monotonic
`raise / raise_settle / transfer / transfer_settle / descend` phases, separate
raise and transfer increments, delayed-action handoffs, bounded reference
lookahead, CLI controls, and phase/pose/relative-position telemetry. Early
versions incorrectly re-evaluated stability every frame: `5120003` spent 201
frames at the raise handoff and 126 at the transfer handoff. Monotonic latching
restored that episode to a 10.4 s, 29.69 N success. The full 186-test Radeon
suite passed.

**Mechanism result.** Feedback-limited transport recovered `7120004` from the
69.00 N regression to a 13.88 N success and retained the `5120003` recovery,
but `4120001` lost its grasp during slow transport. Bounded lookahead shortened
execution but produced 39.95 N; reducing its increment from 10 mm to 5 mm still
produced 40.95 N. The 35 N limit never changed.

**Decision and revisit trigger.** Reject promotion and do not run repeats,
ordinary-profile sentinels, or confirmation episodes. More step scans on the
same development cases would be post-hoc fitting. Keep the code default off as
a negative control. The next method must change grasp stability itself through
payload-aware ranking, a side-grasp family, or measured-slip-triggered regrasp,
then freeze new episodes before making a performance claim.

### 70. Reject stock-Panda side and oblique grasps after feasibility screening

**Observation.** The failed and successful transport-contract episodes all
used the same centered top grasp, but mass and friction did not explain the
failure ordering. This justified checking deeper contact geometry before
changing force or transport timing again.

**Alternatives and evidence.** Top-down, three long-axis side-clearance groups,
and 30/45-degree oblique grasps were evaluated with the same IK, FK restore,
and non-finger collision contract. Top-down produced 36/72 feasible
evaluations. Every side group produced 0/24. Oblique grasps produced 24/24 IK
solutions and 24/24 hand/carton collisions.

**Decision and reason.** Do not integrate these pose families. The stock hand
cannot establish the intended deeper contact without collision. Longer fingers,
a cradle, or suction are different robot assets and must have explicit source,
license, model, and collision validation before evaluation. Diagnostic
generators remain for reproducibility; the production candidate set is
unchanged.

### 71. Reject force-only slip recovery and require a state-changing response

**Hypothesis and fixed rule.** A single-frame 8 mm relative jump with at least
6 mm downward motion, 1 N contact, and 80 mm destination distance isolated the
known frame-159 slip without firing on two successful frozen traces. The only
response was a 20 N to 22 N close-force command for 15 frames; the 35 N abort
threshold and every pose/transport parameter remained fixed.

**Implementation evidence.** Slip detection, bounded force response, per-frame
and episode telemetry, a default-preserving transport-lookahead ablation, CLI
validation, and unit contracts passed all 200 Radeon tests. The lookahead
switch was necessary to compare against the feedback trace on which the rule
was frozen; leaving lookahead active produced a separate 39.95 N failure and
would confound the experiment.

**Physical result.** The rule fired at frames 159 and 261. Peak force was a safe
22.92 N, but final contact loss moved by only one frame, from 260 to 261. The
candidate and feedback baseline both failed after one retry in 19.97 s. At the
second trigger bilateral contact was already absent, so close force could not
recapture the parcel.

**Decision and revisit trigger.** Reject promotion, retain the code disabled,
and cancel sentinels and parameter scans under the preregistered stop rule.
Revisit only with a response that changes state: safe set-down/regrasp, verified
deeper capture geometry, or a different licensed end effector. Do not infer a
success-rate effect from this single development episode.

### 72. Reject short-horizon dynamic ranking despite exact state restoration

**Question and contract.** Test whether a cheap close-lift-transfer rollout can
rank statically feasible grasps before task execution. Use complete Genesis
scene snapshots between candidates, six unique candidates, two repeats, a
30 mm lift, a 30 mm transfer, and the unchanged 35 N safety line.

**Code capability.** `grasp_stability.py` separates threshold validation,
pass/fail classification, and deterministic ranking from the simulator-facing
diagnostic. `diagnose_dynamic_grasp_stability.py` captures/restores complete
scene state and emits the static evaluation, loaded trace, restore error, and
ranking for audit. Unit tests cover boundary behavior and ranking order.

**Evidence.** Every restore had zero measured state-vector error and every
repeat was identical. The known failed production candidate for `4120001`
nevertheless passed 2/2 short rollouts. The alternative ranked first by only
0.00000849 m of maximum one-frame relative motion.

**Decision and reason.** Keep snapshot-isolated rollout as a diagnostic, but do
not call it online planning and do not change candidate selection. Reproducible
execution is necessary but not sufficient: the 30 mm horizon does not expose
the later transport instability. Revisit only with a horizon and disturbance
contract that predicts held-out full-transport outcomes before integration.

### 73. Retain safe set-down and failed-candidate feedback as negative controls

**Question.** Determine whether a detected slip can be converted into a safe
set-down, release, and regrasp, and whether excluding the failed grasp family
prevents recurrence.

**Code capability.** The supervisor adds explicit recovery states; the expert
generates a vertical, bounded set-down target; observations and traces expose
slip and set-down completion; configuration validates step and retry contracts.
A pure helper updates the failed-candidate blacklist while preserving the
historical empty-on-retry behavior when the new switch is off. Both features
are default off and require their existing prerequisites.

**Evidence.** Set-down and release completed below the force limit, followed by
a second planned grasp. Reusing `+40 mm` produced a 129.45 N second-transfer
abort. Excluding it selected `+45.1 mm`, but produced a 129.98 N abort during
the next transfer. The dangerous force occurred after regrasp, not during the
set-down transition.

**Decision and revisit trigger.** Do not promote either feature and do not tune
set-down step, adjacent height, or close force on the same episode. Retain the
mechanisms for audit and future composition. Revisit when the regrasp changes
support geometry, or when a longer-horizon model can reject both unstable
loaded trajectories before execution.

### 74. Accept the formal counterfactual as a labeler, not a ranker

**Question.** Determine whether extending the dynamic rollout through descent
is sufficient, and if not, whether forcing one candidate inside the production
closed loop can generate trustworthy loaded-grasp labels.

**Evidence and alternatives.** The idealized pre-release horizon classified all
six candidates stable, including the known failed `+40 mm` grasp. A fresh-scene
formal counterfactual preserved approach tracking, action delay, feedback
transport, state transitions, the 35 N gate, and the terminal task check. It
reproduced the `+40 mm` miss and found four successful alternatives. Centered
`+45 mm` completed twice with identical 10.31 N peaks. One offset candidate
aborted at 53.74 N. Two success sentinels retained their feasible fallback.

**Code capability.** Add bounded segment helpers and completion-aware dynamic
ranking; add a pure allowlist/rejection merge; expose a pre-execution diagnostic
allowlist in `GenesisParcelEnv`; and provide a runner that verifies requested
and selected IDs for every fresh-scene rollout. All capabilities default to no
production behavior change.

**Decision and reason.** Reject idealized long-horizon ranking and reject a
hand-written `+45 mm` preference. Accept the controller-faithful runner as a
ROCm label collector. The one observed mechanism episode proves discriminative
potential, not generalization.

**Revisit trigger.** Freeze new episode IDs, collect candidate labels, train a
small PyTorch/ROCm scorer with safety-first targets, and beat static ranking on
an untouched paired holdout before integration.

### 75. Freeze a small safety-first scorer before collecting new labels

**Question.** Choose the first learnable grasp-ranking model and define what
must be frozen before expensive counterfactual collection.

**Alternatives.** A hand-coded height rule is fitted to one episode. A VLA adds
large visual/language capacity without solving the label-fidelity or safety
problem. Direct online rollout remains too slow and the idealized rollout has
already failed predictive validation.

**Decision and reason.** Use a 6,276-parameter PyTorch/ROCm MLP over 28 explicit
physical/planning features. Predict safety abort, success, force, and duration;
rank safety first. Keep IK, collision checks, and 35 N supervision outside the
model. Freeze 12 train, six development, and six untouched holdout episodes
across three box profiles before observing any new result.

**Implementation evidence.** The builder enforces fresh-scene formal labels and
split membership. Training, checkpoint loading, offline evaluation, and warm
latency benchmarking run independently. A six-row observed smoke fit completed
in 1.715 s on Radeon; steady six-candidate P95 was 0.902 ms. In-sample recovery
is explicitly not a model-performance claim.

**Promotion gate.** Holdout must add no safety abort or per-profile paired
regression, recover at least one static-ranking failure, and keep warm batch
P95 below 5 ms. Until then the scorer remains disconnected.

### 76. Do not open holdout after an underpowered failed development check

**Question.** Does the frozen scorer show enough independent safety and task
evidence to justify the one-time holdout evaluation?

**Data and capability.** The collector distinguishes an inactive formal gate
from a failed rollout, isolates episodes in child processes, validates complete
artifacts after the known Genesis cleanup failure, and binds accepted labels to
manifest hashes. Dataset construction can now consume that manifest directly.
The evaluator reports full-split outcomes while benchmarking one named real
six-candidate group.

**Evidence.** Four of 12 train episodes and one of six development episodes
were applicable. The model reconstructed train with one success and zero
selected aborts versus static one success and three aborts. On the only
development group, however, all six candidates aborted and none succeeded.
Both rankers selected an abort; the model choice measured 35.896 N versus the
35.521 N group minimum. Six-candidate P95 was 0.921 ms.

**Decision and reason.** Do not promote, integrate, tune on this group, or open
holdout. The latency gate passes, but task/safety evidence does not, and one
applicable group cannot support model selection. Keep the checkpoint as a
reproducible negative result. Revisit after improving the candidate/support
geometry or preregistering a new development set with sufficient gate-active
coverage; holdout IDs remain untouched.

### 77. Retain contact-wrench telemetry but reject threshold integration

**Question.** Can measured contact points, normals, forces, center-of-mass
moment arms, and friction reserve reject unstable grasps before long transport?

**Code capability.** Add a dependency-free reference calculation, a numerically
matched PyTorch path, fixed pre-lift and early-loaded summaries, and default-off
Genesis telemetry. The counterfactual runner exposes the scorer backend while
recording that neither actions nor candidate rank change.

**Evidence.** The observed `4120001` pair showed the expected direction, but
both early-loaded candidates passed the robust check. In frozen train group
`7130001`, three successes and three failures overlapped: a successful
candidate failed the pre-lift check and a later 100.70 N abort passed it. Early
quality for successes spanned 0.710--0.900 and failures 0.515--0.895.

**GPU scheduling evidence.** The tiny vectorized ROCm workload was slower than
the reference: 101.65 versus 93.98 s for the matched 240 Hz two-rollout run.
The final diagnostic samples at 30 Hz; physics/contact solving stay on Radeon,
while the small scalar score defaults to CPU. This is a measured scheduling
decision, not a claim that CPU is generally preferable.

**Decision and revisit trigger.** Do not tune a threshold, integrate the score,
or open holdout. Keep it as explanatory telemetry. Revisit only after a
licensed support-geometry change creates a new candidate family, or after
batched contact scoring makes GPU execution technically justified.

### 78. Retain and freeze the 30 mm adapter, but keep it default off

**Question.** Can an explicitly modeled, open-source fingertip extension fix
the loaded-support failure without changing force policy, ranking, or control?

**Alternatives.** More force already failed to retain the parcel. Adjacent
height selection overfits one episode. Side and oblique stock-Panda grasps were
statically infeasible. A new robot or opaque mesh would expand scope and weaken
the license/reproduction contract.

**Code capability.** Parse the locked Genesis Panda MJCF with a structured XML
API, bind its mesh directory explicitly, and generate one collision plus one
visual box per finger. Validate a 5--60 mm configuration range, expose explicit
CLI switches, preserve generated-asset provenance in telemetry, and provide a
Radeon scene probe that checks collision-geom counts, AABBs, XML elements, and
asset hashes. No third-party mesh is committed.

**Evidence.** The 30 mm geometry increased the finger AABB long span from about
56 to 85 mm. On observed `4120001`, the known failed `+40 mm` grasp completed
at 24.07 N and the successful `+45 mm` sentinel remained successful at
12.55 N. On frozen train group `7130001`, completed candidates changed from
3/6 to 5/6 and safety aborts from 2/6 to 1/6. Across both groups, four stock
successes were preserved and three failures recovered. The remaining candidate
was stopped at 36.95 N by the unchanged 35 N gate.

**Decision and reason.** Retain the adapter as a development-positive physical
candidate, freeze 30 mm, and stop length tuning. Keep it default off because
the eight paired candidate runs are nested within only two deterministic
episodes and no holdout was opened. Do not treat 7/8 as a success rate.

**Revisit trigger.** Model material, fasteners, added mass/inertia, and
compliance, then preregister a separate paired evaluation. Hardware deployment
also requires CAD clearance review and force calibration.

### 79. Retain the mass/inertia implementation but reject candidate promotion

**Question.** Does the frozen 30 mm support geometry remain safe after adding
a finite adapter mass, shifted center of mass, and full inertia tensor?

**Code capability.** Combine a uniform adapter box with the stock finger using
the parallel-axis theorem; generate explicit `fullinertia`; version assets by
extension and effective density; validate configuration; expose production,
counterfactual, and geometry-probe CLI controls; report stock versus combined
inertia and added mass in telemetry.

**Evidence.** At 1240 kg/m3 the box adds 5.952 g per finger. The live Radeon
scene accepted the tensor and preserved the geometry checks. The `+40 mm`
mechanism grasp completed at 13.14 N, but the known-success `+45 mm` sentinel
aborted at frame 204 with 38.3364 N in two identical executions. The force
jump followed a reproducible change from 8 bilateral contacts to 19 unilateral
contacts. No holdout or new episode was opened.

**Decision and reason.** Retain the implementation default off because it is
the physically correct modeling boundary and is independently testable. Reject
promotion and cancel the planned larger campaign because a success sentinel
became a safety abort. Do not scan density or extension on this observation.

**Revisit trigger.** Freeze a separate contact-pair and finger-actuator
diagnostic before executing it. Resume paired evaluation only after that
mechanism is understood and a candidate passes both mechanism and sentinel
gates without changing the independent 35 N supervisor.

### 80. Retain high-rate contact-branch diagnostics and reject the constraint-time candidate

**Question.** Did the mass-aware `+45 mm` regression originate in adapter
collision, high-level control, finger actuation, or the discrete rigid-contact
solve?

**Code capability.** Add default-off 240 Hz telemetry for every active robot
contact, including entity/geom/link identity, force on both bodies, position,
normal, penetration, finger position/velocity, actual force, controller force,
task command, and pose. A pure module summarizes the branch and compares two
aligned traces with preregistered identity, force, position, and velocity
thresholds. It rejects duplicate sample keys and treats complete contact loss
after established bilateral support as support loss. The diagnostic runner can
retain adapter geometry while explicitly ablating only added inertia.

**Differential evidence.** Stock-inertia geometry and combined-inertia traces
first differed in contact identity/count at 197/2, force at 197/4, finger
position at 202/0, and finger velocity/actual force at 203/4. Controller force
never diverged. At 203/4 the mass-aware trace produced 115.5 mm penetration,
162.19 N at a stock fingertip collision, about 2.5 m/s finger speed, and
78.01/72.13 N actual finger force. The adapter geometry did not create the
peak. The unchanged monitor then aborted at frame 204.

**Experiment-integrity correction.** The first constraint-time setup changed a
generated MJCF that environment construction immediately regenerated from the
unchanged source. Code review caught the overwrite; the value-identical run is
explicitly excluded as a no-op rather than reported as a negative candidate.
The valid command-scoped run changed the source before generation, verified
`solref="0.010 1"` in both assets, and removed the Genesis time-constant
warning.

**Candidate evidence.** The verified 0.010 s candidate was worse: it aborted
at frame 134 during `raise` with 105.85 N, before the frozen 196--204 telemetry
window. The absence of high-rate samples is reported rather than imputed.
Source and generated assets were restored after execution.

**Decision and revisit trigger.** Keep the telemetry, comparator, inertia
ablation, tests, bilingual protocol, and hashed evidence. Reject the
constraint-time candidate and do not scan adjacent values, rates, densities,
lengths, gains, or thresholds. No new episode or holdout was opened. Next work
requires a minimal upstream Genesis reproduction and a newly preregistered,
documented solver intervention; VLA or visual training cannot precede a stable
physical baseline. The synchronized Radeon tree compiled and passed 264 tests.

### 81. Keep exact dynamic-state telemetry; do not promote either reproduction as a fix

**Question.** Can the mass-aware impulse be reproduced without the sorter by
restoring the observed generalized state and replaying exposed controller
forces?

**Code capability.** High-rate telemetry now includes complete robot and parcel
qpos/qvel plus nine-DOF actual/controller forces. A validator rejects missing,
non-finite, wrongly sized, non-consecutive, or wrong-start source sequences. A
fresh-scene runner restores state exactly and replays the recorded force
sequence for either inertia model under unchanged force/penetration gates.

**Evidence.** The full source rerun exactly reproduced 162.186 N and 115.546 mm
penetration. Static reductions showed no registered difference. Dynamic replay
restored all four state vectors with zero measured error, yet stock and
mass-aware peaks were only 10.586 N and 7.316 N. Their first and only registered
divergence was a 5.491 N contact-force difference at 198/3.

**Decision and reason.** Retain the telemetry, validators, runners, protocols,
and hashed negative results. Do not treat stock inertia as a physical fix and
do not blame adapter mass alone. Generalized state and exposed post-step forces
are insufficient; a causal claim requires position-control target/mode or
supported complete-scene-state capture under a new protocol. Do not scan the
observed failure. Holdout and all new episodes remain closed.

**Verification.** The final synchronized Radeon tree passed all 268 tests.

### 82. Reproduce the mass-aware event with raw control inputs; reject cross-model attribution

**Question.** Are raw control modes and PD targets the missing state in the
failed dynamic replay, and can the same capture isolate adapter inertia?

**Code capability.** Read Genesis control mode and raw mode-specific targets
without changing them, validate every nine-DOF event, and replay each target
through its public position, velocity, or force API. A deterministic result
summarizer binds raw artifacts, code, and the pre-execution commit by SHA-256.

**Evidence.** The 64-event source contained seven position-controlled arm DOFs
and two force-controlled fingers. Raw target replay reproduced the mass-aware
source failure at `203/4`, 162.186 N and 115.546 mm. The stock replay failed
earlier at `198/1`, 157.787 N and 115.544 mm. The registered comparison was
therefore `invalid_reference`.

**Decision and reason.** Raw targets are sufficient to reproduce the observed
mass-aware event, so solver warm-start capture is not the next priority. Do not
use the unsafe stock cross-model replay for inertia attribution. Keep the
adapter rejected and default off, stop tuning on episode `4120001`, and return
the main effort to stock-hand geometry planning and controller-faithful
candidate ranking under a new frozen protocol.

**Verification.** The pre-execution point is `63ac10b`; the synchronized
Radeon tree passed 269 tests and 28 subtests.

### 83. Replace outcome-dependent label activation with a frozen geometry population

**Question.** Can candidate learning obtain enough controller-faithful groups
without selecting episodes from observed task outcomes or weakening reset and
safety behavior?

**Alternatives.** Enlarging v1 preserves a gate that produced only 5 complete
groups out of 18. Selecting known failures leaks outcomes. Starting ACT, VLA,
or visual embeddings adds model capacity before structured state ranking has a
valid development sample.

**Code capability.** Add an explicit, backward-compatible activation policy;
a physics-free deterministic selector; an exact v2 TOML; SHA-256 bindings for
selector, catalog, and evidence; a recomputing protocol auditor; balanced
32/16/16 splits; and a machine-enforced holdout lock. Collision-checked reset,
hard feasibility, and the 35 N monitor remain external to learning.

**Evidence.** Commit `af88121` predates selection. The selector produced all 64
required groups without scene construction or actions. The audit passed exact
sample and assignment reproduction. Radeon dry-run planned 192 train and 96
development rollouts under `geometry-eligible`; holdout was rejected before
planning.

**Decision and reason.** Freeze v2 and proceed with train only. This repairs
coverage using a pre-existing geometry scope rather than an observed outcome,
while retaining controller and safety fidelity. Do not execute development
until train completes, and do not open holdout until one scorer and all
hyperparameters are frozen.

**Revisit trigger.** Abandon the study if geometry-ineligible samples appear,
fewer than 15/16 development groups produce complete labels, or the selected
scorer fails the registered development safety, task, per-profile, or Radeon
latency gate.

### 84. Compare training objectives at fixed model capacity

**Question.** Should v2 add a larger model, or directly optimize the deployed
within-parcel candidate choice?

**Alternatives.** A larger MLP confounds objective and capacity and is poorly
supported by 32 train groups. Pointwise BCE/regression is calibrated but gives
no direct within-group preference. An unconstrained scalar reward can trade a
successful unsafe candidate against safety.

**Decision and reason.** Keep the identical 6,276-parameter network and add
group-balanced pairwise safety and safe-success losses. Safety is lexicographic:
safe always outranks force-aborted, and success pairs are formed only among
safe candidates. This matches the runtime decision while preserving calibrated
heads and hard external feasibility gates.

**Evidence and boundary.** Pure grouping tests and a five-step two-group ROCm
smoke passed. The smoke is in-sample integration evidence, not a result. Freeze
the two exact training recipes before development; use development once for
the registered promotion gate and keep holdout locked until one recipe is
selected.

### 85. Freeze checkpoints before collecting development

**Question.** How can two learned scorers be compared without turning the
16-group development split into a hyperparameter search?

**Decision and reason.** Bind two exact recipes, implementation hashes, sample
counts, profile balance, latency batch, promotion gates, tie-break order, and
negative-result stopping rule before train completion. Train and hash both
checkpoints first; only then collect development. This prevents result-driven
changes to width, seed, learning rate, loss weights, or candidate set.

**Promotion rule.** A candidate needs all development groups, no per-profile
safety-abort increase, at least one aggregate safety reduction or success gain,
and six-candidate Radeon warm P95 below 5 ms. Safety abort count is the first
tie-break, followed by success, mean force, duration, latency, and fixed name.
If no candidate passes, promote none and do not open holdout.

**Evidence.** The protocol SHA-256 is
`091c8e28efcab4b59663e07b03ec51daa609d057fbff97a79b26adc9233241ee`.
Its hash audit and runtime 6,276-parameter assertion passed before development
execution.

### 86. Stop static-feature ranker iteration after the frozen CV

**Question.** Should a conservative memory ranker justify a new v3 physical
population, or should the project keep the static geometry selector?

**Alternatives.** Continue scanning KNN thresholds on the same folds, try a
third model on the already observed v2 development split, or add new dynamic
information under a separate protocol. The first two alternatives reuse
selection evidence and cannot repair missing contact dynamics.

**Decision and reason.** Stop the static 28-feature learning branch. All six
preregistered candidates passed the Radeon latency limit but failed to improve
the 7-success/17-abort out-of-fold baseline; one increased aborts to 18. Keep
the static selector, collect no v3 learning population, and keep holdout
locked. A later study may use a new preregistered dynamic pre-grasp or
micro-lift probe with contact/slip state and batched Radeon physics.

**Evidence and boundary.** The result is `no_cv_candidate`, with
`selected=null` and `new_physics_authorized=false`. It is train-only model
selection evidence, not an independent generalization claim. The full result
SHA-256 is `3ec39a...8d68`; v2 development is not reusable for tuning.

### 87. Test dynamic information before adding another learned model

**Question.** After static MLP and KNN failures, should the project increase
model capacity, start ACT/VLA expansion, or first test whether a short
controller-faithful probe contains useful ranking information?

**Alternatives.** A larger static model retains the missing-variable problem.
ACT/VLA adds substantial capacity and visual data requirements before the
grasp mechanism is identified. A pre-place micro-lift uses existing physical
state and can later map directly to Radeon-parallel short-horizon simulation.

**Decision and reason.** Freeze the micro-lift feasibility study first. Use 27
mechanically chosen features, four parameter-free policies, hard 35 N/contact/
lift eligibility, safe abstention, and zero profile/fold safety or success
regression. This tests information value without confusing it with model
capacity or opening new physics.

**Evidence and boundary.** Seven directed tests pass. Protocol SHA-256 is
`ca941366...e4ff3`. Only the v2 train manifest is admissible; development,
holdout, online execution, and promotion remain unauthorized until a separate
result and protocol exist.

### 88. Treat the passing probe as a safety veto, not a success ranker

**Evidence.** On 32 frozen train groups, `veto-static` preserved seven
successes and reduced force aborts from 17 to 13. All four reductions were safe
abstentions. The three policies that actively reordered candidates produced
profile, fold, or aggregate regressions and failed.

**Decision and reason.** Advance only the eligibility veto. Do not claim that
micro-lift metrics rank transport success, do not deploy, and do not open V2
holdout. This keeps the positive claim aligned with its mechanism: the early
probe can recognize some candidates for which execution should be withheld,
but did not demonstrate more completed parcels.

**Revisit trigger.** Freeze and run a disjoint, broader parcel population. The
veto may advance only if it preserves baseline successes and reduces safety
aborts without profile concentration. Full train result SHA-256 is
`3df57daf...ba16`.

### 89. Confirm the veto once on a broader independent population

**Question.** Can the V4 safety reduction survive new episodes, profile
novelty, and wider size/yaw/friction/noise variation without sacrificing a
single baseline success?

**Decision and reason.** Freeze 80 box groups before physics: ten groups for
each of four legacy and four unseen profiles. Use only `veto-static`, require
zero paired success/safety/drop regression, at least six safety reductions in
two profiles, and one-sided exact p <= 0.05. This is stricter than merely
repeating the 4/32 point estimate and prevents one profile from carrying the
claim.

**Boundary.** The box planner is extended through a V5-only collection entry
point, leaving V2/V3 shared activation hashes unchanged. Cylinders are excluded
because they need a different candidate generator. Passing authorizes an
online Radeon-parallel probe pilot only; runtime activation still requires a
separate protocol. V2 development and holdout remain forbidden.

**Verification.** Outcome-free selection contains 80 groups with zero old-key
overlap. Protocol audit is valid, dry-run plans 480 rollouts, and 304 tests pass
with one environment skip. Protocol SHA-256 is
`062e3ec9d0c4968b1593331ada5aa1aa737e4eadda869e173fe0116e3ab8101e`.

### 90. Keep cylinder planning analytic, explicit, and independent

**Question.** Should upright canisters and horizontal mailing tubes reuse the
box generator, wait for a learned visual policy, or receive a separate
geometry-aware candidate family?

**Decision and reason.** Implement a separate analytic module. Recover the
axis from the actual pose, align horizontal fingers with that axis, enumerate
radial/axial/symmetric alternatives, and gate unsupported aperture, tool,
length, tilt, and rolling conditions before IK. This preserves physical
symmetry and makes capability failure distinguishable from control failure.

**Boundary.** Do not connect the module to the frozen V5 box path. Pure tests
authorize only later IK/collision screening, not a success claim or runtime
activation. Low-friction horizontal tubes require guarded support and large
tubes remain `cradle_required`.

**Evidence.** Ten directed tests pass remotely. Candidate geometry is finite,
normalized, deterministic, axis-aligned, and explicitly empty at capability
boundaries. No physical cylinder rollout has yet been used for selection.

### 91. Advance cylinder planning only to static feasibility screening

**Evidence.** After commit `4788d21`, the frozen outcome-free audit accepted
128/128 catalog samples. Candidate uniqueness, quaternion norms, aperture
margin, tube-axis alignment, and approach orthogonality all passed fixed gates.

**Decision and reason.** Authorize a static Radeon IK/FK and mesh-collision
screen. Do not authorize physical execution, because analytic candidate
existence says nothing about Panda reachability, swept collision, contact
force, rolling, lift retention, or placement.

**Revisit trigger.** A separately frozen feasibility screen must show useful
coverage in both profiles with bounded P95 planning cost. Any candidate-family
redesign uses a new development namespace and leaves this audit immutable.

### 92. Freeze the cylinder static screen before using the Radeon

**Decision and reason.** Use 24 evenly spaced keys from the outcome-free source
population and bind the planner, adapter, runner, Genesis evaluator, catalog,
and source evidence. Require per-profile feasibility rather than allowing the
easier shape to hide the harder one.

**Concurrency boundary.** Do not execute while V5 runs. Both jobs construct
Genesis scenes on the only Radeon, so concurrent execution would contaminate
latency and could destabilize collection. Code and tests may be frozen now;
physical/static GPU work waits for V5 completion.

**Interpretation.** Passing is static reachability evidence only and cannot be
reported as a grasp, lift, or parcel-sorting result.

### 93. Reject backend-ambiguous static-screen evidence

**Problem.** The first frozen runner defaulted to ROCm but still accepted CPU,
and its sample files did not bind HIP/device metadata. A nominally passing
screen could therefore fail to prove the contest platform requirement.

**Decision.** Before any execution, refreeze with a protocol-level ROCm
requirement, exact one-device gate, HIP presence, and consistent device
fingerprints across resume. Preserve the old hash as superseded rather than
silently replacing it.

**Evidence boundary.** No screen scene or feasibility outcome existed during
this change. The thresholds and 24 sample keys are unchanged. Active protocol
SHA-256 is `e2777ccb...adcfeb`.

### 94. Treat VLA and world models as gated comparisons, not automatic upgrades

**Question.** Should the project immediately add the newest VLA/world-model
stack, or finish the geometry and contact mechanism that currently limits
expert success?

**Decision and reason.** Finish multi-shape feasible-pose planning, then remove
privileged geometry with an analytic ROCm RGB-D front end, then compare ACT and
compact Diffusion on a frozen balanced dataset. This order makes each effect
identifiable. VLA-Adapter 0.5B is the first later compatibility spike because
its scale is plausible on the 48 GB card, but upstream CUDA examples, licenses,
and task/action adaptation must pass isolated gates. A world model is deferred
until long-horizon prediction, rather than grasp geometry/contact, becomes the
measured bottleneck.

**Evidence boundary.** GitHub support and published benchmark numbers do not
prove ROCm compatibility or parcel performance. The VLA evaluation harness is
an evaluator, its listed containers are CUDA-based, and this Genesis task is
not an included benchmark. No new model capability is claimed from the review.

### 95. Keep shape dispatch separate from frozen campaigns

**Question.** How can cylinder candidates enter the future closed loop without
reusing box assumptions or invalidating the active static-screen and V5 hashes?

**Decision.** Add a pure `ShapeGraspPlan` dispatcher in a new module. Boxes keep
the existing height eligibility gate; cylinders use the independent analytic
planner and expose capability failures such as `cradle_required`, insufficient
aperture, and low rolling friction. Do not edit the hash-bound environment or
static-screen implementation before the Radeon screen completes.

**Evidence and boundary.** Nine dispatch tests plus the cylinder unit tests pass
locally. Box ranking is byte-for-byte equivalent at the key level; cylinder
ranking adds rolling-risk and moment-arm priors only after hard feasibility.
This proves interface selection only. It does not authorize a scene,
IK/FK feasibility, force-safe lift, rolling retention, or parcel placement.
After the static screen, integration requires a new protocol, new source
hashes, and the existing reset, collision, retry, and 35 N safety gates.
