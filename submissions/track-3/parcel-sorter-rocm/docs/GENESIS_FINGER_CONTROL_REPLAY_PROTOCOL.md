# Genesis Panda Finger Control-Input Replay Protocol

## Trigger

The exact generalized-state plus open-loop force replay did not reproduce the
mass-aware adapter's 162.186 N closed-loop contact impulse. Both fresh scenes
reconstructed robot and parcel `qpos/qvel` with zero measured error. The stock
scene peaked at 10.586 N and the mass-aware scene at 7.316 N; neither crossed
the unchanged 35 N or 1 mm safety boundary.

This protocol tests the next bounded hypothesis: generalized state is
insufficient because the production scene retains position-control modes and
PD targets that cannot be reconstructed from post-step controller force.

## Frozen procedure

### Stage 1: one read-only source capture

Rerun only the already observed mass-aware
`medium_carton / 4120001 / canonical-long-+0.000-up-0.045` condition. Preserve
the production controller, candidate, 35 N force abort, 240 Hz physics, and
frame 196--204 telemetry window. In addition to the previously captured state,
record the raw nine-DOF Genesis `ctrl_mode`, `ctrl_pos`, `ctrl_vel`, and
`ctrl_force` arrays after every physics substep.

The source capture is admissible only if it selects the same candidate and
reproduces the already observed safety failure. These fields are read-only and
must not alter ranking, control, physics, or stopping behavior.

### Stage 2: paired exact-mode replay

Restore event `196/0` generalized state in one fresh stock-inertia scene and
one fresh combined-inertia scene. To produce each subsequent source event,
apply that event's recorded raw target through the public Genesis method for
its recorded mode: position, velocity, or force. Then advance exactly one
240 Hz step. Do not run the expert, planner, IK, camera, or learned policy.

State reconstruction must be within `1e-6`. Stop at the first contact above
35 N or penetration at least 1 mm. Run exactly one scene per condition and one
comparison.

## Registered interpretation

- Mass-aware only reaches a safety boundary: the missing mechanism is captured
  by raw control modes/targets plus generalized state.
- Neither reaches a boundary but a registered trace difference occurs: retain
  the result as bounded control/contact sensitivity.
- Neither differs materially: position targets/modes are insufficient, and a
  later protocol may inspect supported complete solver state or warm-start
  state.
- Stock reaches a safety boundary: invalidate paired attribution.

Do not scan source frames, modes, targets, gains, physics options, adapter
density/length, force limits, candidates, episodes, or holdout data.
