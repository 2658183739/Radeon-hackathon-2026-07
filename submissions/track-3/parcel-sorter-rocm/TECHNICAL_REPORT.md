# Parcel Sorter ROCm: Technical Report

## 1. Executive summary

Parcel Sorter ROCm is a complete simulated robot application for small-parcel
picking and destination sorting on a single AMD Radeon GPU. The project targets
a practical warehouse edge-workcell scenario: parcels vary in size, mass,
friction, position, and orientation, and the controller must pick each parcel,
transport it to the assigned bin, release it, and verify the result without
exceeding a force safety boundary.

The current embodiment has a three-DoF holonomic base, two Franka Panda arms,
three left-arm suction cups, and a right-arm V-cradle. It combines Genesis,
RGB-D and proprioception, an IK expert, a closed-loop safety supervisor,
LeRobotDataset, and SmolVLA; the earlier single-arm ACT path remains a controlled
baseline. Physics, expert execution, training, inference, and benchmarks ran on
one `gfx1100` Radeon with ROCm 7.2.1.

## 2. Target application and value

Small fulfilment and teaching workcells need manipulation software that can be
developed without a large robot fleet or datacentre GPU allocation. The target
application is a compact sorting station in which one robot processes parcels
arriving within a bounded workspace and places them into one of two destinations.
This task exercises perception, manipulation, physical contact, task-level
recovery, and safe execution while remaining reproducible on a single desktop-
class Radeon device.

The same workflow can support pre-deployment controller testing, synthetic
demonstration generation, introductory robotics teaching, and low-volume parcel
handling research. The simulation is intentionally configurable rather than
hard-coded to one object instance.

## 3. System architecture

The application is divided into five boundaries:

1. **Simulation and sensing.** Genesis advances mobile dual-arm physics at
   240 Hz and renders overhead RGB-D observations.
2. **Task supervision.** A deterministic state machine implements navigation,
   approach, grasp, verify, lift, transport, place, release, and abort stages.
3. **Action generation.** The IK expert provides nominal actions. SmolVLA emits
   a 19-D base/dual-arm action at 3 Hz, and Harness-Lite permits only verified
   bounded residuals. ACT remains the single-arm baseline.
4. **Low-level execution.** Base speeds and Cartesian targets are bounded,
   solved through IK, and executed by arm PD and tri-suction control.
5. **Evidence and evaluation.** Audit trajectories, LeRobot episodes, MP4
   recordings, runtime provenance, task metrics, and performance measurements
   are persisted for reproduction.

The learned model does not replace the safety supervisor. This hybrid boundary
allows data-driven action generation while retaining deterministic limits,
contact checks, retries, and safe abort behaviour.

## 4. Physics simulation and robot model

Genesis 1.2.3 provides AMD GPU physics and headless rendering. The Franka Panda
is loaded from the MJCF assets distributed with Genesis. Each episode creates a
rigid parcel and assigns a left or right destination. Genesis rasterizer depth
is already expressed in metres and is stored as float32 without rescaling.

The baseline uses:

| Setting | Value |
| --- | ---: |
| Physics rate | 240 Hz |
| Control rate | 30 Hz |
| Camera rate | 10 Hz |
| Camera resolution | 224 x 224 |
| Episode limit | 20 s |
| Maximum Cartesian step | 0.04 m |
| Final aligned approach step | 0.01 m |
| Gripper close force | 20 N with a 1 N/step ramp |
| Safety contact threshold | 35 N |
| Maximum grasp retries | 2 |

The deterministic randomizer changes parcel scale, mass, friction, XY position,
yaw, camera position, action delay, and destination. Every sample is a pure
function of the project seed and episode index, so a failure can be replayed
exactly with `--start-episode`.

Catalog v1 defines seven weighted training profiles; catalog v2 expands this to
twelve balanced engineering strata while retaining nine evaluation-only
industry-size boundaries (four existing profiles and five newly sourced
boundaries). Genesis creates actual Box or Cylinder geometry. A
20-episode block has an exact profile allocation, and profile-specific
evaluation uses stable episode IDs even when the evaluator filters profiles.

The mobile mainline augments the upstream Bi-Franka MJCF with an original
`x/y/yaw` base, physical chassis collision, three compliant left-arm cups, and
a right-arm V-cradle for 21 DoF total. Current successful transport uses the
left suction arm; cooperative right-cradle load sharing is not yet verified.

## 5. Perception and action contracts

The simulator exposes RGB, metric depth, seven arm joint positions, seven-value
end-effector pose, destination position, gripper contact force, and parcel pose.
The 20-dimensional ACT state contains robot joints, end-effector pose,
destination, and contact force. The seven-dimensional parcel pose is stored as
privileged audit state but is not provided to ACT.

The learned action has eight values: target Cartesian position, target
quaternion, and gripper command. Before execution, the adapter rejects non-
finite or incorrectly shaped outputs, normalizes the quaternion, limits the
Cartesian displacement, and applies the supervisor's stage-dependent gripper
command. This prevents a malformed policy output from bypassing task safety.

Mobile SmolVLA consumes a 43-D non-privileged state, 224x224 overhead RGB, and
task text and emits three base velocities plus two eight-value Cartesian/tool
commands. The selected v2 executes base residuals only; tool commands, arm
orientation, and high-risk stages remain expert-locked. Metric depth is recorded
and was evaluated in a separate paired RGB-D ablation.

## 6. Expert control and closed-loop behaviour

The expert computes a parcel-aligned top grasp and uses a three-part safe
approach: rise to a transit height, move horizontally above the parcel, and
descend to pregrasp. It then closes the gripper using a force ramp, verifies
bilateral contact, lifts, moves to the destination, opens, and checks both
release and final parcel location.

The catalog controller separates horizontal and final-pose tolerances, latches
the 0.01 m descent after XY alignment, adapts pregrasp tolerance to geometry,
and transfers through lift, horizontal motion, and descent. This is not the
rejected isolated global 0.01 m candidate: that earlier candidate lacked the
XY gate, hysteresis, and geometry window and regressed from 80% to 75%.

The supervisor retries failed grasp verification and short contact losses. It
aborts on a simulator fault or excessive contact force. This behaviour is
present for expert, ACT, and SmolVLA execution, so learned inference remains
inside the same control and safety envelope.

The mobile loop combines a 3 Hz SmolVLA/Harness slow loop with a 240 Hz physics
and safety loop. Harness generates five residual scales and checks progress,
speed, displacement, finite values, and the 35 N boundary. Three physical cups
use contact, compliant force, and breakable constraints to seal, lift, carry a
parcel for 30 cm, place it, and release it.

### 6.1 Experimental geometry-aware grasp planner

The current leading hard-carton candidate generates 24 parcel-relative side
grasp poses, evaluates each from up to three joint seeds with Radeon IK/FK,
non-finger collision, Jacobian, clearance, and state-restoration checks, and
shares the selected XYZ/quaternion across approach, capture, closure, and lift.
It is scoped to boxes at least 125 mm high. Planned contact requires five
stable bilateral frames, final placement descent is capped at 5 mm, and final
approach is capped at 5 mm below 160 mm box height and 2.5 mm above it.

On fixed `large_narrow_carton` episodes `7000000`--`7000019`, with the same
collision-checked reset and 35 N abort in both arms, success improved from 5/20
to 15/20, force aborts fell from 8/20 to 4/20, drops remained zero, and maximum
force fell from 111.30 N to 46.99 N. Ten failures were recovered with no
regression. The feature remains disabled by default because it did not reach
the preregistered 18/20 success and at-most-1/20 force-abort gates. Full method,
negative swept-gate evidence, and remaining failures are documented in
`docs/GEOMETRY_AWARE_GRASP_PLANNING.md`.

## 7. Dataset and robot learning

The formal collection contains 120 randomized attempts. Ninety-six successful
episodes were written to LeRobotDataset, producing 11,753 RGB/state frames. Failed
attempts were excluded from imitation targets but retained in JSONL audit data.
The dataset is self-generated and does not contain personal data or third-party
recordings.

ACT was selected as a compact, established open-source action-chunking policy.
The implementation uses a 52M-parameter configuration, a chunk size of 30, and
10 executed action steps. The formal run used batch size 32, automatic mixed
precision, 5,000 optimization steps, periodic checkpoints, and a 10% evaluation
split. Training ran locally on the Radeon; weights were not pushed to a model
hosting service.

The historical shard multiplied already-metric Genesis depth by `0.001`; its
depth median is only 0.00117 m and is invalid for RGB-D training. It remains
valid for reproducing the RGB/state ACT baseline. Corrected shards store raw
metric depth and a derived three-channel depth view, and a one-step Radeon ACT
smoke verified collection, training, checkpoint reload, and closed-loop input.
Formal RGB-D comparison requires newly collected balanced demonstrations.

Generic image transforms now default to disabled for synthetic geometry. The
training entry point retains an explicit switch so augmentation can be evaluated
as a matched ablation rather than assumed to be beneficial. The recorded
5,000-step run used the previous enabled setting and remains the baseline.

The mobile mainline uses Apache-2.0 LeRobot SmolVLA initialized from
`HuggingFaceTB/SmolVLM2-500M-Video-Instruct`. It consumes a 224x224 overhead
view, 43-D non-privileged state, and task text and emits a 19-D base/dual-arm
action. The selected v2 checkpoint trained for 2,400 steps on six successful
expert episodes. Harness-Lite executes bounded base residuals while deterministic
arm, suction, and safety control remains active. A real RGB-D SmolVLA train and
online run was also completed and retained RGB after the paired gate found no gain.

Diffusion has a Radeon training entry but only a one-step path smoke. VLA-Adapter
0.5B remains an unintegrated compatibility candidate. Third-party source, base
checkpoint, and derived-weight provenance are recorded in `THIRD_PARTY_NOTICES.md`
and `UPSTREAM_LOCK.json`.

## 8. AMD Radeon and ROCm use

The project checks `torch.version.hip`, visible device count, device name, and
VRAM before GPU work. The Genesis backend is initialized as `gs.amdgpu` and
PyTorch executes ACT through ROCm. The application uses the same single GPU for:

- Genesis physics kernel compilation and stepping;
- headless RGB-D rendering;
- ACT forward and backward passes;
- SmolVLA RGB/RGB-D mixed-precision training and 3 Hz online inference;
- mixed-precision training;
- checkpoint loading and real-time inference;
- batched simulation throughput and four-worker isolated closed-loop evaluation.

ROCm PyTorch intentionally uses the `torch.cuda` compatibility namespace.
Runtime evidence also records the HIP version and device name so a CUDA build
cannot be silently reported as a Radeon result.

The measured ACT training sweep showed that AMP with batch size 32 reached 80
samples/s, compared with 74 samples/s for FP32 batch size 8 and 65 samples/s for
FP32 batch size 32. The 128-environment Genesis run reached 46,582 environment-
steps/s and a peak observed GPU utilization of 83%.

## 9. Evaluation methodology

Task success requires the parcel to be released inside the assigned bin.
Secondary metrics include first-attempt success, recovery success, drop rate,
duration, successful parcels per hour, contact force, mean inference latency,
and P95 inference latency. Each output records the config, runtime, episode
parameters, per-episode terminal state, and aggregate metrics.

The deterministic expert was evaluated on 120 randomized episodes. A separate
fixed 10-seed set is retained as a calibration baseline. ACT checkpoints are
evaluated in Genesis with the same safety layer. `--start-episode` makes it
possible to use disjoint deterministic ranges and prevents checkpoint selection
from being dominated by episode zero.

## 10. Results

| Experiment | Result |
| --- | ---: |
| Formal randomized expert | 96 / 120 success (80.0%) |
| First-attempt expert success | 77.5% |
| Recovery success among retry episodes | 37.5% |
| Successful demonstrations | 96 episodes / 11,753 frames |
| Fixed 10-seed expert baseline | 90.0% success |
| Fixed 10-seed drop rate | 0% |
| Fixed 10-seed throughput | 727 successful parcels/hour |
| ACT final evaluation loss at 5,000 steps | 0.1384 |
| ACT 4,000, episodes 10-19 | 30.0% success |
| ACT 4,000 mean / P95 inference latency | 2.05 ms / 8.00 ms |
| ACT 5,000, episodes 10-19 | 10.0% success |
| Rejected 0.01 m approach candidate, matched 120 episodes | 75.0% success; 73.6% throughput retained |
| Parallel Genesis, 128 environments | 46,582 environment-steps/s |
| Peak observed GPU utilization | 83% |
| Twelve-profile catalog v2 one-episode regression | 8 complete; not a formal success rate |
| Mobile SmolVLA v2, frozen 100 trials | 96/100; zero force violations |
| Failure-bridge SmolVLA v3, same frozen set | 91/100; failed Wilson non-inferiority and was not promoted |
| Paired RGB-D, 42 stages | Harness MAE +1.35%, latency +9.65%; RGB retained |
| Left-arm residual, new frozen 100+100 | 94/100 vs 94/100; 1.40 cm vs 2.45 cm placement error; not promoted |
| Mobile-focused unit tests | 41 passing on Radeon |

The 96/100 mobile SmolVLA v2 holdout is the primary learned-policy result. The
120-episode single-arm expert and ACT runs remain historical controlled baselines.
The v3, RGB-D, and arm-residual candidates were all rejected by machine gates;
selection therefore follows frozen closed-loop task, safety, and accuracy evidence
rather than training loss, modality count, or nominal action freedom.

The ACT policy demonstrates a complete ROCm learning path: dataset ingestion,
training, checkpointing, reload, visual inference, and closed-loop physical
execution. Its present success rate is not competitive with the expert and is
reported as a baseline. The 5,000-step checkpoint produced a lower same-range
task success rate than the 4,000-step checkpoint despite continued offline loss
improvement. More training alone is therefore not assumed to solve the gap;
the next experiments should address dataset balance, hard failures, image
augmentation, depth fusion, and checkpoint selection by task success.

## 11. Failure analysis and limitations

Twenty-two of the 24 failed formal expert episodes ended at the force safety
boundary, and two lost the grasp during lift. The largest observed contact force
was approximately 109.8 N. A fixed 0.01 m final-approach limit was tested on the
same 120 episodes and rejected: it reduced success from 80.0% to 75.0%, raised
force aborts from 22 to 25, and retained only 73.6% of throughput. The next
controller experiment must therefore combine gap and force feedback with
phase-specific velocity or impedance shaping; neither a higher safety threshold
nor a fixed slowdown is accepted without closed-loop evidence.

Other current limitations are:

- ACT has been trained for only 5,000 steps on 96 successful episodes.
- The policy does not yet consume the available depth channel.
- The catalog v2 one-case regression still fails for `medium_carton`,
  `shoe_box_proxy`, `large_narrow_carton`, and `mailing_tube`.
- The retained tube contact strategy lifted the fixed tube center from 30.9 mm
  to 66.4 mm but did not complete transfer and placement. Higher close-force
  candidates were rejected for crossing the 35 N safety boundary.
- Diffusion has only a one-step path smoke and VLA-Adapter is not integrated.
- Selected SmolVLA controls base residuals only. The tested left-arm residual is
  disabled after its accuracy regression, and right-cradle cooperation is unverified.
- The 100-trial randomization covers size, mass, friction, and offset and does not
  establish unseen-geometry generalization.
- Evaluation is simulation-only; sim-to-real calibration is outside this
  submission's current evidence.
- The formal container definition is reproducible but the primary validated
  competition path used the supplied bare-metal cloud image.
- No upstream patch is claimed in this revision. The pinned dependency and AMD
  compatibility evidence provide a basis for a later focused upstream change.

## 12. Innovation and technical contribution

The contribution is a reproducible hybrid Physical AI workflow rather than a
single isolated model. Its main design choices are:

- deterministic, replayable domain randomization for failure reproduction;
- separation of policy state from privileged simulator state;
- one safety and action contract shared by expert and learned policies;
- bounded Harness-Lite policy drift and isolated failure-driven promotion;
- complete audit retention even when failures are excluded from imitation data;
- disjoint episode-range evaluation to reduce checkpoint-selection bias;
- a tri-suction mobile dual-arm embodiment with explicit parcel strata;
- one-GPU ROCm execution spanning simulation, training, inference, and holdout;
- explicit performance and limitation reporting alongside task success.

## 13. Deliverables

This source directory contains the complete original application code, tests,
configuration, pinned dependency metadata, ROCm bootstrap scripts, Dockerfile,
training and evaluation commands, benchmark tools, architecture notes, Chinese
operator documentation, and this report. Generated artifacts include JSONL
audit trajectories, LeRobotDataset episodes, ACT/SmolVLA checkpoints, frozen
gate and summary JSON, benchmark JSON, logs, and MP4 demonstrations.

Large generated datasets and weights are not committed to Git. They are
reproducible from the documented commands and can be attached to the final
submission through release storage without weakening source reproducibility.
Small raw summaries and logs are committed under `evidence/` with a SHA-256
index.

Paired model-selection and chronological development records are available in
`docs/MODEL_SELECTION*.md` and `docs/DEVELOPMENT_JOURNAL*.md`. The latest
step-by-step evidence and decisions are in
`docs/OPTIMIZATION_SESSION_2026-07-25*.md`.

## 14. Team and contributions

This Git revision is maintained as a single-participant project. The registered
legal name and exact Luma team name will be supplied in the final Pull Request
metadata. The participant is responsible for system design, simulation and
control integration, data collection, ROCm training and benchmarking,
evaluation, failure analysis, documentation, and demonstration production.

## 15. Reproduction entry points

The authoritative procedure is in `README.md`. The shortest validated path is:

```bash
bash scripts/preflight_radeon.sh
INSTALL_LEROBOT=1 bash scripts/bootstrap_radeon.sh
source scripts/activate_radeon_env.sh
python -m unittest discover -s tests -q
bash scripts/run_pipeline_radeon.sh outputs/radeon-run
```

All reported results should be regenerated with the exact config and upstream
revisions committed in this directory.
