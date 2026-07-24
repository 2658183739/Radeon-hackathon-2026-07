# Model and Platform Selection

## 1. Decision

The project uses a layered system instead of assigning every responsibility to
one large model:

1. **Genesis and Franka Panda** provide physics, sensing, contact, and actuation.
2. A **deterministic supervisor with IK/PD** owns task phases, recovery, motion
   limits, and force safety.
3. **ACT** is the verified low-cost learned baseline on Radeon/ROCm.
4. **Diffusion Policy** is the second conventional imitation-learning baseline.
5. **VLA-Adapter 0.5B** is the preferred language-conditioned compatibility
   experiment after a ROCm and transitive-license audit.
6. SmolVLA is held until its checkpoint license is explicit; Pi0, Pi0.5,
   OpenVLA, and RDT remain compatibility-gated research references.

This ordering follows the competition's primary task-performance criterion. A
larger model cannot substitute for stable contact control, good data, closed-loop
evaluation, or Radeon evidence.

## 2. Non-negotiable constraints

| Constraint | Implementation |
| --- | --- |
| One AMD Radeon GPU | `HIP_VISIBLE_DEVICES=0`; preflight requires one visible device |
| Open ROCm stack | ROCm PyTorch, Genesis `gs.amdgpu`, and `torch.version.hip` evidence |
| Open source | Genesis, LeRobot, and PyTorch revisions are pinned |
| Cloud reproduction | Bare-metal scripts, configs, tests, Dockerfile, and stepwise README |
| No simulator leakage | The 7-D parcel pose is audit-only and excluded from policy input |
| Closed-loop safety | Every learned policy shares Cartesian, IK, PD, gripper, and 35 N limits |

ROCm PyTorch intentionally exposes its HIP device through the `torch.cuda`
Python API. The preflight rejects a build where `torch.version.hip` is empty.

## 3. Candidate comparison

| Candidate | Role | Strength | Main risk | Status |
| --- | --- | --- | --- | --- |
| Geometry expert | Data and capability upper baseline | Explainable and replayable | Coverage depends on rules | Implemented and measured |
| ACT | First learned baseline | Compact, fast, mature action chunking | Overfits small datasets | Trained and closed-loop evaluated |
| Diffusion Policy | Strong conventional comparison | Models multimodal actions | Iterative denoising adds latency | Training entry ready; no result claimed |
| VLA-Adapter | Language-conditioned 0.5B VLA | Small, MIT-tagged code/base/checkpoint candidates | CUDA-oriented setup and transitive license audit | Research spike only |
| SmolVLA | Language-conditioned lightweight VLA | LeRobot-native compact policy | Current checkpoint metadata has no license | Held; no strict-open result |
| Pi0/Pi0.5 | Frontier VLA comparison | Strong open implementation | Heavier dependencies and memory | Compatibility gate only |
| OpenVLA/RDT | Research extension | Broad community material | Outside the pinned main path | Not a promised deliverable |

## 4. Feature and responsibility contract

Policy inputs are overhead RGB (`3 x 224 x 224`), a 20-D non-privileged state,
and a natural-language task for VLA candidates. Corrected shards retain metric depth
for a controlled RGB-D experiment; historical ACT data must remain RGB-only.
The state contains joints, end-effector pose,
target position, and contact force. Ground-truth parcel pose is excluded.

All policies output an 8-D Cartesian action: position, quaternion, and gripper.
They do not directly command joint torque. Finite checks, quaternion
normalization, Cartesian limiting, IK, PD, stage-aware gripper control, and the
force abort remain outside the model.

## 5. Recommended sequence

1. Reproduce ACT and select checkpoints by non-overlapping closed-loop episodes.
2. Train Diffusion with `scripts/train_diffusion_rocm.sh`; start with horizon 32,
   eight executed actions, and ten denoising steps.
3. Stage VLA-Adapter locally only after its ROCm operators and transitive
   licenses are audited; keep this as a separate compatibility experiment.
4. Keep SmolVLA out of the strict-open path until its checkpoint terms are
   explicit; any later vision unfreezing must be a matched experiment.
5. Evaluate every admitted checkpoint through `scripts/evaluate_policy.py`,
   which keeps the same supervisor and safety path.

Example commands are in the paired Chinese document and project README.

## 6. Radeon optimization matrix

Change one major variable at a time: precision, batch size, Diffusion denoising
steps, VLA vision freezing, or compilation. Keep data, seed, checkpoint
budget, and evaluation episodes fixed. Report task success, safety, latency,
throughput, peak memory, and GPU utilization separately.

An optimization is rejected if it materially reduces success, continues after
the 35 N boundary, or hides collision by raising the threshold.

## 7. Current boundary

ACT data generation, training, save/load, ROCm inference, and Genesis closed-loop
evaluation are verified. Diffusion completed the original and a compact
one-step Radeon training smoke. The compact candidate changes the UNet widths
from `[512,1024,2048]` to `[256,512,1024]`, has 76.6M parameters, and is
recorded in `evidence/training/diffusion-compact-1step-rocm.md`. This is a
resource/path result, not a task capability result. SmolVLA matches the pinned
LeRobot 0.6.1 interface but needs a locally staged base checkpoint and explicit
license before it can be admitted. Neither policy has a formal capability
result. The 96 successful episodes
are insufficient for a broad VLA generalization claim. Cylinders still expose
parallel-jaw control limits, and corrected RGB-D is now an interface smoke whose
capability value remains unmeasured.

## 8. Acceptance gate

A model enters the demonstration only after a held-out 20-episode closed-loop
evaluation, profile-stratified reporting, correct 35 N behavior, latency and
memory evidence, SHA-256 hashes for artifacts, and reproduction from the final
Git commit.
