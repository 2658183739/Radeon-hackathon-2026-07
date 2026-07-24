# End-Effector Capability Contract

## Current implementation

The reproducible runtime currently implements one end effector: the Franka
Panda parallel jaw gripper (`parallel_jaw`). The capability gate is checked
before Genesis scene construction. Profiles marked `suction_required` or
`cradle_required` remain evaluation-only catalog boundaries and are rejected
by the current closed-loop runtime.

This is an intentional truthfulness and safety boundary. A profile describing a
large flat parcel is not evidence that a parallel jaw can reliably manipulate
it.

## Extension contract

An end-effector implementation may be enabled only after all of the following
are provided:

1. A versioned Genesis asset and collision geometry.
2. A control adapter that exposes the same observation/action contract.
3. A deterministic reset and release procedure.
4. Contact-force and failure metrics appropriate to that tool.
5. Dedicated train, validation, and held-out episodes.
6. A reproducible ROCm smoke test and closed-loop report.

The implementation should then add the new handling class to the capability
registry through an explicit runtime configuration, rather than changing the
default parallel-jaw result.

## Current score implication

The current project can make evidence-backed claims for box and cylinder
profiles handled by parallel jaws. It must not claim suction or cradle support
until the extension contract is satisfied. This separation preserves the
robot-capability score's credibility and prevents an unsupported profile from
contaminating model comparisons.
