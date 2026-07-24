# Optimization Roadmap

This roadmap turns the current evidence into an ordered engineering program.
It separates changes that improve task capability from changes that only make
the implementation faster. Each item has a measurable acceptance criterion so
that an attractive demo cannot substitute for a reproducible result.

## 1. Current baseline

| Area | Current evidence | Main limitation |
| --- | --- | --- |
| Expert capability | 80% over 120 randomized episodes | 22/24 failures are force-safety aborts |
| Learned capability | ACT 4,000: 30% on episodes 10-19 | Small successful-only dataset; RGB only |
| Closed loop | Contact verification, retry, release check, safe abort | Force response is reactive, not predictive |
| Robustness | Size, mass, friction, pose, camera and delay randomization | No stratified held-out report yet |
| Simulation performance | 46,582 env-steps/s at 128 environments | Camera/data collection path is not batched |
| Training performance | 80 samples/s with AMP batch 32 | Augmentation and checkpoint policy need ablation |
| Multimodal sensing | RGB-D is stored | ACT currently consumes RGB and state only |
| Reproducibility | Pinned code, config, evidence, tests | Large artifacts still need release hashes |

## 2. Optimization principles

1. Optimize the largest measured failure mode first.
2. Change one causal variable per experiment.
3. Select checkpoints with closed-loop task metrics, not offline loss alone.
4. Keep physics, safety, and model metrics separate.
5. Preserve a deterministic replay key for every failure.
6. Profile before changing precision, synchronization, or memory movement.
7. Use a larger model only after the data and evaluation loop are trustworthy.

These principles follow current reproducible-robotics practice: configuration
as code, deterministic experiment manifests, held-out closed-loop evaluation,
dataset/model provenance, and explicit safety boundaries around learned actions.

## 3. Priority P0: improve the existing system

### P0.1 Phase-aware final approach

**Evidence.** The formal expert run has 22 force-safety aborts. The previous
global Cartesian limit allows 0.04 m per 30 Hz control step, which is too
aggressive near contact.

**Tested candidate.** Keep 0.04 m for transit, lift, and placement, but use
`final_approach_step_m = 0.01` after horizontal alignment with the parcel.

**Why.** A global slowdown would reduce throughput even in free space. A phase-
specific limit targets contact energy without changing the rest of the motion.

**Acceptance criteria.** On the identical 120 episode indices:

- force-safety abort rate at or below 5%;
- expert success at or above 90%;
- no increase in drop rate;
- successful throughput decreases by less than 15%.

**Measured decision.** Reject the candidate. On the same 120 episodes, success
fell from 80.0% to 75.0%, force aborts increased from 22 to 25, and throughput
retention was 73.6%. Maximum observed force fell from 109.8 N to 97.9 N, but
that isolated peak does not compensate for worse task and safety outcomes. The
baseline default is restored to 0.04 m while the separate parameter remains
available to reproduce the experiment.

**Next experiment.** Instrument vertical gap, force, and force derivative by
control phase. Compare 0.02/0.03 m limits and a contact-aware velocity/impedance
schedule on the same episodes. Change one controller factor per run and do not
raise the 35 N safety threshold.

### P0.2 Synthetic-image augmentation ablation

**Evidence.** The original ACT run enabled generic image transforms. The scene
is synthetic and the action depends on fine pixel geometry, so strong crop,
rotation, or color operations can create observations that are inconsistent
with the action label.

**Implemented decision.** `ACT_IMAGE_TRANSFORMS=false` is now the default, with
an explicit environment variable for the augmented comparison.

**Experiment.** Train otherwise identical runs with transforms off and on,
using three training seeds, the same data split, and the same checkpoint steps.

**Acceptance criteria.** Report mean and range over seeds for held-out loss and
30 closed-loop episodes. Keep augmentation only if closed-loop success improves
without increasing contact aborts.

### P0.3 Task-based checkpoint selection

**Evidence.** On the same episode range, ACT step 4,000 achieved 30% while step
5,000 achieved 10%, even though the offline evaluation loss continued to
improve before the final step.

**Implemented decision.** `summarize_act_evaluations.py` merges non-overlapping
episode ranges, rejects duplicate episode indices, recomputes metrics, and ranks
checkpoints by success, drop rate, P95 latency, and force.

**Acceptance criteria.** Evaluate every candidate on at least three disjoint
10-episode ranges. Do not call a checkpoint “best” from fewer than 30 episodes.

## 4. Priority P1: improve learning capability

### P1.1 Hard-example recollection

Create a failure table keyed by mass, friction, size, yaw, position, delay, and
terminal reason. Oversample the bins responsible for force aborts and grasp
loss. After the expert is improved, recollect those exact episode indices and
append successful recoveries to the dataset.

Recommended data mix:

- 50% uniform in-domain episodes;
- 30% previously failed or neighbouring hard conditions;
- 20% held-out edge conditions, kept out of training for final evaluation.

This is a lightweight dataset-aggregation loop. It should precede collecting a
large number of redundant easy episodes.

**Acceptance criterion.** At least 300 successful episodes, with every selected
mass/friction/yaw bin represented and a published distribution table.

### P1.2 Curriculum randomization

Train first on nominal pose and medium mass/friction, then widen one range at a
time. The final policy must still be evaluated on the full randomization range.
Curriculum is a training aid, not permission to narrow the benchmark.

**Acceptance criterion.** Full-range success improves by at least 10 percentage
points over the no-curriculum baseline on the same held-out indices.

### P1.3 RGB-D fusion

Depth is already stored in metres. Compare:

1. RGB + state baseline;
2. depth + state baseline;
3. RGB-D late fusion with separate lightweight encoders;
4. RGB-D early fusion only if the policy implementation supports calibrated
   channel normalization.

Late fusion is the conservative first choice because RGB and metric depth have
different statistics. Do not copy a one-channel depth map into three channels
without documenting normalization and validating that it adds information.

**Acceptance criterion.** At least a 10-point success improvement or a 25%
reduction in grasp-position error under camera/appearance randomization.

### P1.4 Better action targets

Compare absolute Cartesian targets with bounded delta position plus a normalized
rotation representation. Delta actions often simplify imitation learning, but
they can accumulate error. Keep the deterministic supervisor and IK boundary in
both variants.

**Acceptance criterion.** Lower action error and higher closed-loop success on
the same data; no increase in IK or force faults.

## 5. Priority P1: robustness and safety

### P1.5 Stratified robustness report

Report success and confidence intervals by:

- light/medium/heavy parcel mass;
- low/medium/high friction;
- small/medium/large scale;
- yaw quadrant;
- workspace region;
- camera perturbation and action-delay level.

Aggregate success alone can hide a systematic unsafe subgroup. Use at least 30
episodes per reported coarse stratum or combine strata honestly.

### P1.6 Force-aware approach controller

After the phase-aware speed limit is validated, add a near-contact controller
that reduces vertical velocity as contact force rises. Keep the hard 35 N abort
as the independent final boundary.

**Acceptance criterion.** Lower P95 and maximum contact force without reducing
successful throughput by more than 15%.

### P1.7 Sensor perturbations

Add depth noise, dropped frames, exposure/lighting variation, partial occlusion,
and camera calibration offsets. Each perturbation needs a realistic range and a
separate clean baseline. Avoid visually dramatic randomization with no link to
the intended deployment.

## 6. Priority P2: Radeon/ROCm performance

### P2.1 Profile the complete frame

Use PyTorch Profiler and `rocprofv3` to divide latency into rendering, image
conversion, host-to-device transfer, policy forward, synchronization, IK, and
physics. Preserve the raw trace and exact command.

Do not remove `torch.cuda.synchronize()` from a latency benchmark without
replacing it with correct HIP event timing. Asynchronous timing without a
barrier reports enqueue time rather than completed inference.

### P2.2 Reduce image transfer overhead

The current camera returns a NumPy frame and ACT copies it to the GPU. Profile
before adding complexity. Candidate optimizations are reusable buffers, pinned
host memory, non-blocking copies, and batched preprocessing. Accept a change
only if end-to-end P95 improves, not merely a microbenchmark.

### P2.3 Precision and compilation matrix

Keep physics and control in FP32. For the visual policy, compare FP32, FP16 AMP,
and BF16 where the target Radeon supports it. Test `torch.compile` only as an
optional measured experiment because operator coverage and compile overhead are
version dependent.

**Acceptance criterion.** At least 15% training or inference improvement with
no NaNs and no statistically meaningful task-success regression.

### P2.4 Parallel data generation

The physics benchmark already scales to 128 environments, while RGB-D expert
collection uses a single rendered environment. Separate physics-only rollout,
batched camera rendering, and dataset encoding to identify the actual limit.
Use bounded queues so video encoding cannot exhaust memory.

## 7. Priority P2: VLA and frontier models

LeRobot currently exposes ACT, Diffusion policies, and multiple VLA families,
including SmolVLA. For this project, a VLA should initially perform high-level
instruction grounding or destination selection while ACT or a compact policy
retains continuous manipulation control.

Recommended sequence:

1. make ACT exceed 60% on at least 30 held-out episodes;
2. add multiple package classes or natural-language sorting rules;
3. fine-tune an open lightweight VLA with LoRA or another parameter-efficient
   method on the single Radeon;
4. compare VLA high-level decisions against a deterministic rule baseline;
5. keep the low-level safety supervisor unchanged.

Do not add a VLA solely for presentation. It earns technical value only when
language or semantic generalization changes the task.

## 8. Competition-score alignment

| Score area | Highest-value next evidence |
| --- | --- |
| Robot capability, 30 | Same-seed expert force improvement and 30+ episode learned-policy success |
| Radeon/ROCm, 20 | Full-frame profiler trace, AMP/precision ablation, reproducible container |
| Innovation, 20 | Safe hybrid policy plus hard-example loop and RGB-D confidence-aware fusion |
| Application value, 20 | Parcel strata, throughput, failure cost, and deployment assumptions |
| Upstream contribution, 10 | Minimal reproducible AMD issue and accepted Genesis/LeRobot fix or documentation patch |

## 9. Upstream contribution strategy

Do not manufacture a cosmetic patch. First isolate an AMD-specific limitation
with a minimal script, exact ROCm/PyTorch/Genesis version, expected versus actual
behaviour, and profiler evidence. Candidate contributions include:

- Genesis AMD installation or `gs.amdgpu` documentation improvements;
- an RDNA-specific failing kernel reproducer and fix;
- LeRobot ROCm CI or device-detection documentation;
- a generic depth-feature or checkpoint-evaluation improvement accepted upstream.

An upstream issue with a high-quality reproducer is useful, but the competition
score is strongest when the fix is merged.

## 10. Experiment record template

Every optimization run should record:

```text
experiment_id:
git_commit:
upstream_revisions:
hardware_and_vram:
rocm_torch_genesis_lerobot_versions:
config_diff:
dataset_hash_and_episode_indices:
training_seed_and_eval_seed_ranges:
command:
primary_metric_and_acceptance_threshold:
secondary_safety_and_latency_metrics:
raw_artifact_paths_and_sha256:
decision: keep / reject / repeat
decision_reason:
```

## 11. Official references

- [Genesis World](https://github.com/Genesis-Embodied-AI/genesis-world): AMD
  ROCm backend, parallel environments, sensors, controllers, and simulation.
- [LeRobot](https://github.com/huggingface/lerobot): standardized datasets,
  ACT/Diffusion policies, VLA families, and policy evaluation tooling.
- [AMD ROCm PyTorch installation](https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/frameworks/pytorch/install.html):
  tested images and version-specific ROCm/PyTorch environments.

The submission remains pinned to its verified ROCm 7.2.1 environment even when
upstream documentation moves to newer production releases.
