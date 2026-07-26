# 2026 Frontier Method Roadmap: Multi-Shape Parcel Sorting, VLA, World Models, and ROS 2

## 1. Scope and position

This roadmap aligns the project with open robotics work published or released
from 2024 through July 2026. Its purpose is not to accumulate model names. It
decides which methods can produce attributable, reproducible evidence on one
AMD Radeon GPU with ROCm, Genesis, and the current Panda closed loop.

The paper contribution remains:

```text
parcel geometry/state -> feasible multi-pose grasp candidates
  -> IK + FK + collision + manipulability gates
  -> controller-faithful dynamic safety probe -> 35 N supervisor
  -> closed-loop transport and placement
```

Current evidence does not justify replacing low-level joint control with a
VLA. A VLA can later propose high-level candidate families or task goals, but
hard geometry and safety gates must remain outside the learned model.

## 2. What recent work changes

| Direction | Representative work | Value to this project | Decision |
| --- | --- | --- | --- |
| Unified VLA evaluation | `allenai/vla-evaluation-harness` v0.4.0, Apache-2.0 | Separates policy servers from simulation benchmarks and includes LeRobot/OpenVLA/PI-family adapters | Use later as an external adapter; it is not a trainable policy |
| Force-memory VLA | FM-VLA, arXiv:2607.18231 | Encodes force history for contact events that vision cannot disambiguate | Most relevant learned ablation after the dynamic veto; test compact force tokens first |
| Scene simplification | LENS, arXiv:2607.19633 | Closed-loop scene cropping or merging can help classical planning, MPC, and VLA | Defer until a cluttered multi-parcel conveyor exists |
| Physical world models | PhysCoRe, arXiv:2607.20653 | Combines analytic physics, learned residuals, and uncertainty for deformable interactions | Defer to soft mailers; rigid parcels do not justify MPM now |
| Real2Sim | Agentic Real2Sim, arXiv:2607.19190 | Recovers geometry and physics parameters from real video | Use after real recordings exist; it cannot replace the current controlled study |
| Data engines | AXIS, arXiv:2607.21588 | Large-scale trajectory quality control, perturbations, and held-out protocols | Reuse its data-card and quality-gate ideas, not its scale claim |
| Low-cost humanoid VLA | DEED, arXiv:2607.20345 | Emphasizes frequency alignment, data selection, and reduced dependence on giant VLAs | Supports system integration and data quality before model scaling |
| Classical grasp/planning baselines | MoveIt 2, GPD, Dex-Net, GraspNet, Contact-GraspNet | Supplies deployment, point-cloud, analytic, and learned grasp references | MoveIt 2 can become the ROS adapter; CUDA-heavy baselines remain external references unless ported |

The LeRobot bridge in `vla-evaluation-harness` reports formal LIBERO
reproduction for PI0.5, GR00T N1.7, MolmoAct2, and VLA-JEPA, but SmolVLA is
smoke-only and its pinned FastWAM path records an upstream 0/20 reproduction.
Repository support therefore cannot be treated as task-level evidence.

## 3. Ordered method programme

### P0: Finish the frozen V5 confirmation

V5 contains 80 new groups across eight profiles and at most 480 candidate
rollouts. It tests only `veto-static`. Promotion requires complete groups, no
success/safety/drop regression, no per-profile regression, at least six force
abort reductions in at least two profiles, one-sided exact paired `p <= 0.05`,
and selector P95 below 5 ms. It does not authorize immediate deployment.

### P1: Run true online parallel probes on one Radeon

If V5 passes, clone one deterministic initial state into several Genesis
environments, execute four to six candidates through approach, grasp, verify,
and micro-lift, stop all candidates at the first place boundary, and execute
the remaining transport/place path only in the main environment.

Report scene construction, state cloning, first compilation, batched probe,
selector, and main-trajectory latency separately. The current sequential run
uses only about 2% of VRAM and roughly 28% GPU activity, so parallelism is a
testable optimization rather than a marketing claim.

### P1: Add analytic cylinder and mailing-tube planning

Cylinders must not reuse the box generator. Upright candidates span equivalent
radial jaw yaws, heights, and symmetric wrist branches. Horizontal candidates
span axial offsets and radial approach angles while keeping fingers parallel
to the tube axis so closure crosses its diameter.

An explicit capability gate covers aperture, tool class, axis tilt, length,
and rolling friction. Low-friction tubes become guarded-support boundaries;
large tubes remain `cradle_required`. A conservative capsule envelope can
prefilter palm and finger volumes, while Genesis mesh collision remains final.
See `docs/CYLINDER_GRASP_PLANNING.md`.

### P1: Build a ROCm-native RGB-D geometry front end

The near-term perception path is lighter and more attributable than a VLA:

```text
depth -> PyTorch/ROCm back-projection -> table removal -> parcel cloud
      -> PCA/oriented box or cylinder fit -> shape, size, pose, confidence
      -> geometry candidates and safety probe
```

Compare ground-truth state, noise-corrupted ground truth, and RGB-D-estimated
geometry. Report pose/size error as well as closed-loop task metrics. A small
confidence or residual head may be trained on Radeon, but the analytic path
must work first.

### P2: Compare ACT and one compact VLA proposal head

Formal fine-tuning begins only after:

- geometry and cylinder methods show a stable positive result;
- at least 500 trajectories pass data-quality audit;
- train/development/holdout are grouped by physical episode and profile;
- action frequency, image keys, state dimensions, normalization, and chunks
  are frozen before development;
- the model cannot bypass the 35 N supervisor.

The order is ACT RGB-D, then SmolVLA LoRA or action-expert-only tuning as a
high-level candidate proposer, then an FM-VLA-style force-history ablation.
Only after those comparisons should PI0.5, VLA-JEPA, or a larger world model be
considered. Every model needs a capacity-matched no-vision or no-force control
and Radeon VRAM, throughput, compile, warm P50/P95, and stability reporting.

### P2: Add ROS 2 and MoveIt 2 as deployment adapters

ROS 2 is not a contest requirement and will not repair current simulation
success, so it follows algorithm freeze. The minimal deployment graph is:

```text
/camera/rgb + /camera/depth + /joint_states
        -> parcel_perception_node
        -> grasp_candidate_node
        -> safety_probe_node
        -> FollowJointTrajectory / gripper command
        -> safety_monitor_node (35 N, drop, timeout)
```

Use rosbag2 for fixed-input replay. MoveIt 2 supplies the real-robot motion
interface; it must not be mislabeled as the paper's algorithmic contribution.

## 4. Shortcuts to reject

- `torch.cuda` names are not NVIDIA evidence; PyTorch ROCm uses the same API.
- A model loading successfully is not closed-loop efficacy. Unseen physical
  episodes are required.
- V5 thresholds, minimum gain, and profile gates cannot change after outcomes
  appear.
- Carrier-size parcels outside the 79 mm parallel-jaw envelope cannot be
  claimed as graspable; they remain suction or cradle capability boundaries.
- Vision, planner, controller, and model cannot all change in one experiment,
  because the effect would be unidentifiable.
- CUDA-only custom operators cannot be the AMD primary path without a verified
  ROCm port.
- A world model's visually plausible video is not task success. Physics state,
  force, drop, and closed-loop outcomes remain authoritative.

## 5. Paper-scale experiment matrix

| Experiment | Required controls | Main outcomes |
| --- | --- | --- |
| Box main method | Historical reset, collision-reset baseline, full planner | Success, force abort, drop, peak force, duration, planning latency |
| Geometry ablation | No collision filter, no manipulability, no symmetric wrist, no retry replanning | Paired changes and failure taxonomy |
| Dynamic safety | Static first choice, V5 veto, online parallel veto | Success loss, safety gain, probe cost |
| Multi-shape | Box, long box, flat rigid mailer, upright cylinder, horizontal tube | Per-profile and macro averages |
| Perception | Ground truth, noisy ground truth, RGB-D estimate | Pose/size error and closed-loop success |
| Learning | ACT, compact VLA proposal, force-memory candidate | Unseen profiles, robustness, VRAM, latency |
| GPU | Sequential scene, parallel probe, batched perception | Utilization, VRAM, throughput, end-to-end P95 |

Use paired McNemar tests and Wilson 95% intervals for binary outcomes, paired
bootstrap or sign permutation for continuous outcomes, and a mixed-effects
logistic model only when profile and perturbation levels are numerous enough.
Every method must use the same episode, random sample, and 35 N boundary.

## 6. Reproducible search provenance

Sources were accessed on 2026-07-26. Literature metadata was queried through
the arXiv export API and OpenAlex, then checked by exact identifier. Repository
metadata, READMEs, trees, and a small number of target files were inspected
through GitHub. These sources establish method or interface existence only;
project-local ROCm smoke tests and frozen closed-loop evaluation must establish
compatibility and efficacy.

- [FM-VLA](https://arxiv.org/abs/2607.18231)
- [LENS](https://arxiv.org/abs/2607.19633)
- [PhysCoRe](https://arxiv.org/abs/2607.20653)
- [Agentic Real2Sim](https://arxiv.org/abs/2607.19190)
- [DEED](https://arxiv.org/abs/2607.20345)
- [AXIS](https://arxiv.org/abs/2607.21588)
- [allenai/vla-evaluation-harness](https://github.com/allenai/vla-evaluation-harness)
- [huggingface/lerobot](https://github.com/huggingface/lerobot)
- [moveit/moveit2](https://github.com/moveit/moveit2)
- [atenpas/gpd](https://github.com/atenpas/gpd)
- [BerkeleyAutomation/dex-net](https://github.com/BerkeleyAutomation/dex-net)
- [graspnet/graspnet-baseline](https://github.com/graspnet/graspnet-baseline)
- [NVlabs/contact_graspnet](https://github.com/NVlabs/contact_graspnet)
