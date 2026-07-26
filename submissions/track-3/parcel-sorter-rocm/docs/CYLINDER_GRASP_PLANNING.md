# Geometry-Aware Grasp Planning for Cylinders and Mailing Tubes

## Current result

The project now has a cylinder planner independent of the box planner. It
covers upright canisters, horizontal mailing tubes, explicit hardware and
rolling-safety gates, a conservative capsule-envelope distance, and a
deterministic low-risk candidate prior.

This step verifies geometry, gating, and coordinate transforms only. It does
**not** establish a closed-loop success improvement. The frozen V5 box study is
still running, so the module is not connected to `genesis_env.py` or
`grasp_planning.py`. The next admissible step is ROCm IK/collision screening,
followed by a separately frozen cylinder physics protocol.

## Why a cylinder is not a box proxy

A box has fixed faces and major/minor axes. A cylinder is rotationally
symmetric around its axis, and a horizontal tube can roll. A box proxy adds
nonexistent corners, does not prove that jaw closure crosses the diameter, and
can hide unsupported low-friction or oversized objects.

The implementation rotates the cylinder local z axis by the actual `wxyz`
pose. For horizontal candidates, the gripper local x axis is parallel to the
tube axis and its local z approach axis is orthogonal to the tube. This avoids
Euler-yaw extraction and remains defined under small physical roll or tilt.

## Representation

| Object | `dimensions_m` | Cylinder axis |
| --- | --- | --- |
| Upright cylinder | `(diameter, diameter, height)` | Local z |
| Horizontal tube | `(length, diameter, diameter)` | Local z transformed by the pose |

The radial dimensions must agree within numerical tolerance. Invalid
dimensions, non-finite values, and zero quaternions raise errors instead of
being mislabeled as controller failures.

## Capability gate

The current runtime has only the Franka Panda parallel-jaw gripper. Before
candidate generation, the planner computes:

```text
aperture margin = total jaw aperture - cylinder diameter
```

Defaults require at least 1 mm margin, no more than 0.320 m axial length, and
no more than 20 degrees of axis tilt from the declared orientation. Horizontal
tubes require rolling friction of at least `0.001`; otherwise the result is the
explicit `horizontal_tube_requires_guarded_support` boundary.

A `cradle_required` tube never produces parallel-jaw candidates, even if a
caller supplies an unrealistically wide aperture. The rolling-risk index is a
ranking and interpretation heuristic, not a calibrated probability.

## Candidate families

For an upright cylinder, the default half-circle symmetry set is 0, 45, 90,
and 135 degrees. Each has a `+pi` wrist alternative for a different IK branch
and two contact heights that retain at least 20 mm of side overlap. The default
set contains 16 candidates and approaches vertically.

For a horizontal tube, candidates use the centre and up to +/-50 mm along the
axis while retaining a 60 mm end margin. Duplicate offsets collapse for short
tubes. Radial approach angles are 0 and +/-20 degrees; top-down is primary and
oblique angles are fallbacks for IK or collision constraints. A 240 mm tube
produces 18 candidates with symmetric wrists.

The deterministic prior prefers lower rolling risk, a smaller centre-of-mass
moment arm, the canonical wrist, and then a stable candidate ID. It cannot
override subsequent IK, FK, swept-collision, 35 N, or dynamic-probe gates.

## Conservative envelope

`point_to_capsule_signed_distance` expands the cylinder axis segment by its
radius. Hemispherical ends over-approximate the cylinder and are conservative
near end caps. Negative values are inside, zero is on the surface, and positive
values are outside clearance.

This helper is not complete hand collision proof. Runtime integration must
check multiple palm/finger support volumes and retain Genesis mesh collision as
the final gate.

## Verification

Ten directed tests pass in the remote `/opt/venv` environment. They cover pose
axis extraction, malformed geometry, aperture and rolling gates, explicit
cradle rejection, upright and horizontal geometry, short-tube deduplication,
prior ordering, quaternion normalization, and capsule distance.

```bash
cd /workspace/parcel-sorter-opt-v1
PYTHONPATH=src /opt/venv/bin/python -m unittest \
  tests.test_cylinder_grasp_planning -v
```

## Frozen next-step order

1. Do not change the shared box runtime before V5 finishes.
2. Connect cylinder candidates to the generic IK/FK/collision evaluator while
   retaining a separate generator.
3. Report candidate counts, feasible counts, rejection reasons, and planning
   P50/P95 before full tasks.
4. Preregister paired historical-expert, incorrect-box-proxy, and analytic
   cylinder-planner closed loops.
5. Stratify results by diameter, length, mass, friction, yaw, and position.
6. Advance only after independent episodes show a stable task or safety gain.

The current state is "implemented, awaiting physical screening," not promoted.
