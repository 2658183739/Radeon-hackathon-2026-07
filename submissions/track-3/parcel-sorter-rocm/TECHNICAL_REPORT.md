# Parcel Sorter ROCm: Technical Report

## 1. Executive summary

Parcel Sorter ROCm is a complete simulated robot application for small-parcel
picking and destination sorting on a single AMD Radeon GPU. The project targets
a practical warehouse edge-workcell scenario: parcels vary in size, mass,
friction, position, and orientation, and the controller must pick each parcel,
transport it to the assigned bin, release it, and verify the result without
exceeding a force safety boundary.

The application uses Genesis for rigid-body physics and rendering, a Franka
Panda robot model, RGB-D and proprioceptive observations, an inverse-kinematics
expert, a closed-loop safety supervisor, LeRobotDataset for demonstrations, and
an ACT visual imitation policy. Physics, expert execution, training, inference,
and benchmarks were run on one `gfx1100` Radeon with ROCm 7.2.1. The submission
includes source, pinned upstream revisions, a clean-build container definition,
tests, configuration, and step-by-step reproduction commands.

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

1. **Simulation and sensing.** Genesis advances rigid-body physics at 240 Hz,
   executes control at 30 Hz, and renders the camera at 10 Hz. The scene
   contains the Franka robot, parcel, plane, and two destination bins.
2. **Task supervision.** A deterministic state machine implements detect,
   approach, grasp, verify, lift, place, release, complete, and abort stages.
3. **Action generation.** The scripted IK expert or an ACT, Diffusion, or
   SmolVLA policy produces a high-level Cartesian target and gripper command.
4. **Low-level execution.** Cartesian targets are step-limited, solved through
   IK, and executed by arm PD control and force-ramped gripper control.
5. **Evidence and evaluation.** Audit trajectories, LeRobot episodes, MP4
   recordings, runtime provenance, task metrics, and performance measurements
   are persisted for reproduction.

The learned model does not replace the safety supervisor. This hybrid boundary
allows data-driven action generation while retaining deterministic limits,
contact checks, retries, and safe abort behaviour.

## 4. Physics simulation and robot model

Genesis 1.2.3 provides AMD GPU physics and headless rendering. The Franka Panda
is loaded from the MJCF assets distributed with Genesis. Each episode creates a
rigid parcel and assigns a left or right destination. The simulator converts
Genesis depth output from millimetres to float32 metres before dataset storage.

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

The catalog defines seven weighted training profiles and four evaluation-only
industry-size boundaries. Genesis creates actual Box or Cylinder geometry. A
20-episode block has an exact profile allocation, and profile-specific
evaluation uses stable episode IDs even when the evaluator filters profiles.

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
present for both expert and ACT execution, so learned inference remains inside
the same control and safety envelope.

## 7. Dataset and robot learning

The formal collection contains 120 randomized attempts. Ninety-six successful
episodes were written to LeRobotDataset, producing 11,753 RGB-D frames. Failed
attempts were excluded from imitation targets but retained in JSONL audit data.
The dataset is self-generated and does not contain personal data or third-party
recordings.

ACT was selected as a compact, established open-source action-chunking policy.
The implementation uses a 52M-parameter configuration, a chunk size of 30, and
10 executed action steps. The formal run used batch size 32, automatic mixed
precision, 5,000 optimization steps, periodic checkpoints, and a 10% evaluation
split. Training ran locally on the Radeon; weights were not pushed to a model
hosting service.

Depth is stored in the dataset but the current ACT baseline uses RGB plus robot
state. This is an explicit limitation and provides a controlled next experiment:
an RGB-D fusion policy can be compared against the present RGB baseline without
recollecting demonstrations.

Generic image transforms now default to disabled for synthetic geometry. The
training entry point retains an explicit switch so augmentation can be evaluated
as a matched ablation rather than assumed to be beneficial. The recorded
5,000-step run used the previous enabled setting and remains the baseline.

Radeon training entries are also provided for Diffusion and SmolVLA. Diffusion
is the conventional imitation comparison and completed a one-step training-path
smoke. SmolVLA fine-tunes a locally staged open `lerobot/smolvla_base` with the
vision encoder frozen for the first run. Neither has a formal capability result.
A generic checkpoint adapter loads ACT, Diffusion, or
SmolVLA behind the same supervisor, IK/PD execution, and 35 N force boundary.

## 8. AMD Radeon and ROCm use

The project checks `torch.version.hip`, visible device count, device name, and
VRAM before GPU work. The Genesis backend is initialized as `gs.amdgpu` and
PyTorch executes ACT through ROCm. The application uses the same single GPU for:

- Genesis physics kernel compilation and stepping;
- headless RGB-D rendering;
- ACT forward and backward passes;
- mixed-precision training;
- checkpoint loading and real-time inference;
- batched simulation throughput measurements.

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
| Seven-profile one-episode catalog smoke | 4 complete; not a formal success rate |
| Deterministic unit tests | 48 passing |

The larger 120-episode expert run is the primary task-capability result. The
fixed 10-seed result is useful for regression testing but is not presented as a
replacement for the larger sample.

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
- Micro-box, upright-canister, and mailing-tube catalog smokes still fail.
- Diffusion has only a one-step path smoke; SmolVLA still needs a staged local
  base checkpoint. Neither has formal closed-loop evidence.
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
- complete audit retention even when failures are excluded from imitation data;
- disjoint episode-range evaluation to reduce checkpoint-selection bias;
- explicit multi-geometry parcel strata and geometry-aware control;
- one-GPU ROCm execution spanning simulation, training, and inference;
- explicit performance and limitation reporting alongside task success.

## 13. Deliverables

This source directory contains the complete original application code, tests,
configuration, pinned dependency metadata, ROCm bootstrap scripts, Dockerfile,
training and evaluation commands, benchmark tools, architecture notes, Chinese
operator documentation, and this report. Generated artifacts include JSONL
audit trajectories, LeRobotDataset episodes, ACT checkpoints, summary JSON,
benchmark JSON, logs, and MP4 demonstrations.

Large generated datasets and weights are not committed to Git. They are
reproducible from the documented commands and can be attached to the final
submission through release storage without weakening source reproducibility.
Small raw summaries and logs are committed under `evidence/` with a SHA-256
index.

Paired model-selection and chronological development records are available in
`docs/MODEL_SELECTION*.md` and `docs/DEVELOPMENT_JOURNAL*.md`.

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
