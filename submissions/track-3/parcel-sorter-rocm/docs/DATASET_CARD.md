# Dataset Card: Parcel Sorter RGB-D Demonstrations

## Summary

The dataset is generated entirely in the Genesis parcel-sorting simulation by
the deterministic IK expert. The formal collection contains 120 randomized
attempts; 96 successful episodes and 11,753 frames form the imitation dataset.
All 120 attempts remain in JSONL audit traces.

## Features

| Feature | Shape | Unit / meaning | ACT use |
| --- | --- | --- | --- |
| `observation.images.overhead_rgb` | `3 x 224 x 224` | uint8 RGB | Yes |
| `observation.images.overhead_depth` | `1 x 224 x 224` | float depth, metres | Stored; not in baseline |
| `observation.state` | `20` | joints, EE pose, target, contact force | Yes |
| `observation.privileged_state` | `7` | simulator parcel pose | No |
| `action` | `8` | position, quaternion, gripper | Target |

Physics runs at 240 Hz, control at 30 Hz, and camera rendering at 10 Hz. The
latest camera frame is held between camera updates.

## Randomization

Parcel size, mass, friction, XY position, yaw, destination, camera position, and
action delay are deterministic functions of seed and episode index. The baseline
ACT data uses `configs/baseline.toml`; the catalog generator uses
`configs/catalog_v1.toml` with seven weighted training profiles and four
evaluation-only industry-size profiles. Genesis creates Box and Cylinder
geometry explicitly, and the catalog evaluator keeps stable profile episode IDs.

## Inclusion policy

Only successful expert episodes enter behaviour-cloning data. Failed attempts
remain in audit traces and should be used for failure analysis, hard-example
selection, recovery learning, or preference learning with an explicit method.

## Intended use

- ACT or other imitation-policy training for this simulated workcell;
- RGB/RGB-D/state ablation;
- reproducibility and robotics teaching;
- hard-example and safety analysis.

## Limitations

- Simulation-only and no real sensor calibration;
- successful-only imitation targets create selection bias;
- the formal 120-episode set is concentrated on rigid parcels feasible for the
  current parallel gripper; cylinders and industry-size boundaries need separate
  collection/evaluation;
- 96 episodes are insufficient for broad semantic generalization;
- current baseline does not use depth in ACT.

## Release requirements

Before external release, publish the episode manifest, feature metadata, exact
Git commit, upstream revisions, generation config, and SHA-256. Review the
license implications of simulator-provided assets and declare a dataset license
explicitly; do not infer it automatically from the source-code MIT License.
