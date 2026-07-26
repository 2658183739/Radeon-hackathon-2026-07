# Cylinder Static IK/FK/Collision Screen V1 Protocol

## Purpose

The analytic audit proves candidate existence only. This screen tests whether
those candidates satisfy the existing Genesis Panda IK position/rotation,
forward-kinematics, mesh-collision, manipulability, and exact state-restoration
checks under the three established IK seeds.

It executes no control action, advances no physics, closes no gripper, and
reads no success, force, drop, or placement outcome.

## Frozen population

The source is the passed 128-sample analytic population. Each profile uses 12
fixed offsets:

```text
0, 5, 11, 17, 23, 29, 35, 41, 47, 53, 59, 63
```

The resulting 24 keys must be a subset of the source artifact. Upright
episodes start at `10100000` and horizontal episodes at `10200000`. Selection
does not inspect IK, collision, or task results.

## Execution path

Each sample builds one ROCm Genesis scene with initialization settling
deferred, so no physics step is executed. Candidate generation uses the actual
parcel pose, the shape-aware expert hand clearance, and `2 * open_width_m` as
the total jaw aperture. The diagnostic adapter reuses the existing
`_evaluate_grasp_pose_candidate` path for identical IK, FK, mesh collision,
manipulability, and state-restoration checks.

The private interface is intentional for a diagnostic adapter and does not
modify shared `genesis_env.py`. Its hash is bound by the protocol.

## Preregistered gates

- all 24 samples complete;
- at least 75% of samples in each profile have a feasible candidate;
- all evaluation values are finite;
- maximum state-restoration error is at most `1e-7`;
- candidate-screen P95, excluding scene build, is at most 5,000 ms.

The screen does not require 100% feasibility because it is a development gate,
not the final paper population. A profile below 75% requires candidate redesign
on a new namespace. A pass authorizes only a separately frozen small physical
study, not runtime activation.

## Timing and resume contract

Scene build, complete candidate screen, and per-evaluation times are reported
separately, with per-profile P50/P95 and feasible-candidate distributions.
Each sample is written independently and the manifest is atomically updated.
Resume accepts a file only when protocol hash, profile, episode, completion
state, and recomputed sample hash all match.

## Execution order

Do not start while the V5 box confirmation occupies the Radeon. After V5:

```bash
cd /workspace/parcel-sorter-opt-v1
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/run_cylinder_static_screen.py \
  --protocol configs/cylinder_static_screen_v1.toml \
  --output-dir outputs/cylinder-static-screen-v1 \
  --backend rocm \
  --resume
```

The 75%, restoration, and latency thresholds cannot change after results are
observed.
