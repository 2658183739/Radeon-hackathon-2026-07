# Genesis Panda Finger Dynamic-State Replay Protocol

## Trigger

The preregistered static zero-velocity reproduction completed 64 aligned
substeps in both inertia conditions. The stock reference peaked at 5.081 N and
0.267 mm penetration; the mass-aware condition peaked at 5.084 N and 0.263 mm.
No registered trace difference occurred. Therefore added finger inertia alone
does not reproduce the original 162.19 N transport failure in a static grasp.

This protocol tests the next bounded hypothesis: the failure requires the
transport-stage generalized velocity and force history.

## Frozen two-stage procedure

### Stage 1: one read-only source capture

Rerun only the already observed mass-aware
`medium_carton / 4120001 / canonical-long-+0.000-up-0.045` condition. Keep the
existing controller, planner, 35 N abort, 240 Hz physics, and frame 196--204
contact window unchanged. Add these read-only fields to every physics sample:

- full nine-value robot `qpos` and DOF velocity;
- full nine-value actual and controller force;
- seven-value parcel `qpos` and six-value parcel DOF velocity.

The capture is valid only if the same candidate is selected and the existing
mass-aware safety failure is reproduced. This is the same observed episode,
not a new evaluation sample.

### Stage 2: paired open-loop replay

Use event `196/0` as the exact initial generalized state in two fresh scenes:
stock explicit finger inertia and combined rigid-body inertia. Starting from
source event `196/1`, apply the recorded nine-DOF controller-force vector before
each 240 Hz step. Do not run the sorter state machine, planner, IK, camera, or
learned policy during replay.

Both scenes receive the same state and force sequence. Stop a replay after the
first measured contact above 35 N or penetration at least 1 mm. State
reconstruction must be exact within `1e-6` before stepping.

## Interpretation

The existing comparison classifier is reused:

- mass-aware only reaches a safety gate: dynamic inertia/contact interaction
  is reproduced independently of the high-level controller;
- neither reaches a gate but a frozen difference threshold occurs: retain as
  bounded dynamic sensitivity;
- neither differs: an open-loop applied-force trace is insufficient and the
  next investigation must capture PD targets or a fuller solver state;
- stock reaches a gate: invalidate the paired attribution.

The difference thresholds remain 1 N force, 0.1 mm finger position, and
0.01 m/s finger velocity. Do not scan the start frame, force sequence, state,
physics options, model parameters, or episode.
