# Shape-dispatched grasp planning

## Purpose

`src/parcel_sorter/shape_grasp_planning.py` is a pure boundary between parcel
geometry and the candidate evaluator. It dispatches boxes to the registered
box candidate family and cylinders to the independent analytic cylinder
family. It does not construct a Genesis scene, step physics, or claim a
successful grasp.

## Why this boundary exists

The earlier box runtime cannot be reused for a cylinder without changing the
meaning of the wrist frame and the approach direction. Upright cylinders need
radial and height alternatives; horizontal tubes need fingers aligned with the
tube axis and a guarded rolling policy. Keeping these families separate makes
the capability boundary auditable and avoids silently evaluating
`cradle_required` parcels with a parallel gripper.

`ShapeGraspPlan` intentionally separates:

- `supported`: the current end effector and geometry are representable;
- `activation_eligible`: the current experiment scope permits runtime use;
- `reason`: a machine-readable rejection such as an aperture or handling-class
  failure;
- `candidates`: the finite, deterministic candidate set passed to later IK.

For boxes, the existing height scope remains in force. For cylinders, the
planner applies the frozen static-screen parameters: an 80 mm aperture, a
1 mm minimum margin, a 320 mm parallel-jaw length limit, a 20 degree axis tilt
limit, and guarded horizontal rolling friction. The large-cylinder catalog
profiles remain explicitly `cradle_required`.

## Test and evidence boundary

The nine dispatch tests and the existing cylinder tests cover candidate
family selection, upright and horizontal geometry, disabled planning, low
rolling friction, unsupported handling classes, and shape-aware ranking. Box
ordering is exactly unchanged. Once hard feasibility and collision gates pass,
cylinder ranking prefers low rolling risk and a small centre-of-mass moment
arm before joint-travel and manipulability tie-breaks. These tests prove only
the pure interface. The frozen 24-sample Radeon static screen is still the authority for
IK/FK and mesh-collision feasibility. A screen pass would authorize a new
closed-loop protocol; it would not itself prove force safety, lifting, rolling
retention, or placement.

## Planned integration

After the static screen completes, the Genesis environment may replace its
box-only candidate call with this dispatcher under a new protocol and source
hash. The integration must preserve the existing reset gate, candidate
blacklist, waypoint collision gate, 35 N supervisor, retry re-planning, and
per-candidate telemetry. The frozen V5 box campaign must remain immutable.
