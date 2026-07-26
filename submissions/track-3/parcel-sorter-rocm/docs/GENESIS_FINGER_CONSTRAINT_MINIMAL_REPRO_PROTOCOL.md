# Genesis Panda Finger Constraint Minimal-Reproduction Protocol

## Purpose

The mass-aware 30 mm parcel adapter produced a 162.19 N contact and 115.55 mm
penetration in one frozen `medium_carton / 4120001` trace. The stock-inertia
ablation used the same geometry and control commands but did not show that
failure. This protocol removes the sorter state machine, grasp planner, camera,
and learned policy before testing whether the physical-model branch survives a
fixed-command replay.

This is a mechanism test, not a task-performance or robustness evaluation. It
does not open a new episode or any scorer holdout.

## Upstream audit before choosing the candidate

Genesis 1.2.3 sanitizes every equality `solref` time constant to at least
`2 * substep_dt`. The Panda asset authors the finger equality with
`solref="0.005 1"`, so the value becomes 0.008333 s at 240 Hz. The previously
preregistered 0.010 s candidate failed earlier and is not scanned further.

Genesis issue [#3051](https://github.com/Genesis-Embodied-AI/genesis-world/issues/3051)
and PR [#3072](https://github.com/Genesis-Embodied-AI/genesis-world/pull/3072)
identified a separate MJCF default-armature bug. It is excluded here because:

- the locked Genesis revision `ec0efcc0` is later than merged PR #3072 and its
  parser contains the fix;
- the Panda MJCF itself explicitly authors `armature="0.1"` through the
  inherited `panda` default class, including both finger joints.

Therefore `default_armature=None` is not a valid intervention for this Panda
model. No undocumented solver option is introduced.

## Frozen reproduction

| Field | Frozen value |
|---|---|
| Runtime | one Radeon `gfx1100`, ROCm 7.2, Genesis 1.2.3 |
| Genesis revision | `ec0efcc0daf9b9932920e6b73f5f810961330997` |
| Source observation | `medium_carton / 4120001`, control frame 196 |
| Geometry | 30 mm adapter per finger, 1240 kg/m3 |
| Conditions | stock explicit inertia ablation; combined rigid-body inertia |
| Initial arm state | deterministic IK from the frozen reset pose to the recorded end-effector pose |
| Initial parcel state | recorded frame-196 pose and the frozen episode mass/dimensions/friction |
| Initial finger state | recorded positions 0.03228778 m and 0.03228711 m |
| Velocities | all reset to zero |
| Arm command | hold the reconstructed seven-joint position |
| Finger command | constant `[-20, -20]` N |
| Physics | 240 Hz, at most 64 substeps |
| Safety boundary | stop after first measured force above 35 N or penetration at least 1 mm |

Each condition runs in a separate process and a fresh scene. The script records
every physics substep using the existing contact-branch contract: all robot
contacts, geometry and link identities, position, normal, penetration, both
contact forces, finger positions, velocities, actual forces, and control
forces. It also records the generated MJCF SHA-256 and reconstructed pose error.

## Preregistered interpretation

- `mass_aware_instability_reproduced`: the stock-inertia reference remains
  below both gates while the mass-aware condition reaches either gate.
- `bounded_contact_sensitivity_only`: neither reaches a gate, but a frozen
  trace-difference threshold is crossed.
- `not_reproduced`: neither reaches a gate and no registered divergence occurs.
- `invalid_reference`: the stock-inertia reference reaches a gate; do not use
  the comparison to blame the mass-aware model.

Trace thresholds remain 1 N contact/finger force, 0.1 mm finger position, and
0.01 m/s finger velocity. A negative result means this static zero-velocity
reconstruction is insufficient; it does not clear the full sorter failure.

## Execution

```bash
python scripts/reproduce_genesis_finger_constraint.py \
  --variant stock-inertia --backend rocm \
  --output outputs/finger-constraint-minimal-repro-v1/stock-inertia.json

python scripts/reproduce_genesis_finger_constraint.py \
  --variant mass-aware --backend rocm \
  --output outputs/finger-constraint-minimal-repro-v1/mass-aware.json

python scripts/compare_genesis_finger_constraint_repro.py \
  --reference outputs/finger-constraint-minimal-repro-v1/stock-inertia.json \
  --candidate outputs/finger-constraint-minimal-repro-v1/mass-aware.json \
  --output outputs/finger-constraint-minimal-repro-v1/comparison.json
```

Do not scan physics rate, time constant, density, extension, friction,
controller gain, force threshold, pose, episode, or candidate after seeing the
result. Any dynamic-state capture or upstream patch requires a new protocol.
