# Architecture and Experiment Plan

## Competition mapping

| Competition area | Baseline implementation | Measured evidence |
| --- | --- | --- |
| Simulation | Genesis rigid-body scene with a Franka arm, parcels, bins, RGB-D, and contact sensors | simulation steps/s and parallel environments |
| Learning | Scripted IK demonstrations followed by ACT or behavior cloning | training curves and task success |
| Robustness | Domain randomization over parcel, camera pose, friction, and action delay | held-out success and drop rate |
| Closed loop | Grasp verification, force safety, retry, and abort supervisor | first-attempt and recovery success |
| GPU optimization | ROCm simulation, batched environments, mixed-precision visual policy, reduced transfers | latency, throughput, VRAM, utilization |
| Multimodal | RGB, depth, proprioception, gripper state, and contact force | modality ablation |

## Delivery gates

### Gate 1: ROCm smoke test

- Verify one visible Radeon GPU and a non-null `torch.version.hip`.
- Install the pinned Genesis revision without replacing ROCm PyTorch.
- Run a headless rigid-body and robot-control example.
- Record device, software versions, and a screenshot or log.

### Gate 2: deterministic closed-loop MVP

- Spawn one parcel at a known pose.
- Move to pregrasp with IK.
- Close the gripper and verify contact.
- Lift and place into one destination bin.
- Retry after a deliberately failed grasp.

This gate has been validated on the competition Radeon instance. The remaining
control work is focused on lowering approach force in randomized heavy-parcel
episodes.

### Gate 3: parallel data generation

- Run randomized scenes in parallel.
- Use the deterministic controller as an expert.
- Save RGB/depth frames, robot state, actions, and outcomes.
- Write successful RGB-D episodes directly to LeRobotDataset and retain every audit trace as JSONL.

### Gate 4: learned visual policy

- Start with behavior cloning or a small ACT policy.
- Predict end-effector deltas and gripper commands, not raw torques.
- Keep IK, PD control, safety checks, and retries outside the model.

### Gate 5: robustness and optimization

- Evaluate unseen parcel dimensions, masses, friction, and poses.
- Compare state-only, RGB, and RGB-D plus state policies.
- Compare open-loop execution with closed-loop retry.
- Sweep environment count and inference precision on the same GPU.

## Profiling rules

- Keep physics and control numerics in FP32 for the first stable baseline.
- Render cameras less frequently than physics steps.
- Keep observations on the GPU whenever the backend permits it.
- Use `rocm-smi`, PyTorch Profiler, and `rocprofv3` for evidence.
- Report median and P95 inference latency, not only averages.
- Preserve raw logs and the exact config used for every reported result.
