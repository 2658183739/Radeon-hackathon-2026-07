# Evidence-Driven Optimization Session: 2026-07-25

Chinese companion: [OPTIMIZATION_SESSION_2026-07-25_CN.md](OPTIMIZATION_SESSION_2026-07-25_CN.md)

## Purpose and engineering standard

This record explains the reproducible reasoning behind one optimization session.
It follows a modern robotics/ML workflow: freeze the episode and safety limit,
inspect telemetry, change one major variable, test contracts before simulation,
retain negative evidence, run a cross-profile regression, and distinguish a
diagnostic smoke from a statistical capability claim.

The record captures evidence, alternatives, decisions, and implementation
techniques. It does not claim that one deterministic episode estimates a success
rate.

## Frozen conditions

| Item | Frozen value |
| --- | --- |
| Host | single AMD Radeon `gfx1100`, 47.98 GiB |
| Stack | ROCm 7.2.1, PyTorch 2.9.1 ROCm, Genesis 1.2.3 |
| Safety boundary | measured finger contact force must remain at or below 35 N |
| Diagnostic sample | catalog v2 `mailing_tube`, local episode 0 / namespaced episode 9,000,000 |
| Comparator | `catalog-v2-rolling-scoped.json` |
| Formal-claim rule | repeated held-out episodes are required; one case is only regression evidence |

## Step-by-step decision record

### 1. Audit the failure before editing control

**Observation.** The sampled horizontal cylinder used `dimensions[1] / 2` as
its radius but an independently sampled `dimensions[2] / 2` as spawn height.
The fixed sample therefore began about 5 mm above the surface and fell before
the robot approached.

**Alternatives.** Tune approach control around the motion, add rails, or correct
the inconsistent primitive first.

**Decision and reason.** Correct the primitive first. A controller must not be
optimized against a geometry-generation bug.

**Code capability.** Cylinder dimensions are canonicalized during sampling:
horizontal `(length, diameter, diameter)`, upright `(diameter, diameter,
height)`. Spawn height is derived from the same radius used to construct the
Genesis cylinder. Contract tests check both mappings.

### 2. Correct the gripper/tube orientation

**Observation.** The earlier horizontal-tube yaw made the finger direction
perpendicular to the tube axis. The gripper pushed along the wrong contact
geometry.

**Decision and reason.** Align finger length with the tube axis so jaw closure
crosses the diameter. This uses parallel-jaw symmetry while preserving the
existing wrist bound.

**Evidence.** Peak force fell from 72.92 N after the geometry correction to
43.54 N after axis alignment. This remained a failed diagnostic, but the
directional change was retained because it materially improved the intended
contact geometry.

### 3. Separate free-space speed from final approach speed

**Observation.** A 10 mm global final approach still crossed the 35 N boundary.
Making every motion slower would increase episode time without targeting the
contact phase.

**Decision and reason.** Add optional profile-level
`final_approach_step_m`. Mailing tubes use 5 mm only after horizontal
alignment; free-space motion retains the 40 mm bound.

**Evidence.** The same episode passed the approach safety gate at 34.26 N, then
lost the grasp during lift. The bottleneck moved from approach collision to
grasp retention.

### 4. Require stable bilateral contact before lift

**Observation.** One transient dual-finger contact was enough to enter lift.

**Decision and reason.** Add `grasp_stability_steps` to the supervisor and
initially require three consecutive contact frames. The state machine resets
the counter on any gap and retains the existing force abort.

**Evidence.** The tube had verified contact for three frames and retained
contact during the first lift frames, but then slipped. The second retry reached
48.05 N. Stable contact improved phase correctness but did not solve retention.

### 5. Limit lift acceleration by profile

**Observation.** With the 40 mm Cartesian request, contact disappeared as the
end effector accelerated upward. The first slow-lift test retained intermittent
contact for four additional frames.

**Decision and reason.** Add optional profile-level `lift_step_m=0.01`. This
keeps normal boxes unchanged and creates an explicit variable for fragile or
slip-prone objects.

**Evidence.** The diagnostic still failed at 35.12 N during recovery. The change
was insufficient by itself, but the trace supported keeping it as part of the
tube-specific contact strategy.

### 6. Model high-friction replaceable finger pads

**Observation.** The gripper moved upward while the tube remained on the table,
which is a slip signature. Genesis exposes runtime per-link friction setters;
the Panda/default rigid friction is approximately 1.0.

**Alternatives.** Increase normal force, use a staging fixture, add concave
geometry, or model a higher-friction pad.

**Decision and reason.** Test `finger_friction=2.0` first because it changes the
contact material without relaxing the 35 N safety limit. The parameter is
validated against Genesis' `(0, 5]` range and applied only to both finger links
for profiles that request it.

**Evidence.** Peak force fell to 15.62 N and all three attempts reached lift,
but the tube still slid out. The material model improved safety and retry
quality, not complete task success.

### 7. Center the pads before closing

**Observation.** The generic cylinder close window was 35 mm. In the trace, the
hand began closing roughly 33 mm above its intended pose, so the pad contacted
the top of the cylinder rather than its centerline.

**Decision and reason.** Add optional profile-level
`pregrasp_tolerance_m=0.01`. This makes the geometric close condition explicit
instead of adding a post-contact downward motion, which earlier experiments had
shown to be unsafe.

**Evidence.** This was the first candidate to lift the tube: center height rose
from 30.9 mm to 66.4 mm while bilateral contact persisted for about 75 frames.
The tube later slipped, so the result is a partial capability improvement, not
a successful episode.

### 8. Reject higher close-force candidates

**Observation.** After center alignment, retention rather than acquisition was
the limiting phase.

**Alternatives.** Keep 20 N, test 25 N, or test the 35 N command boundary while
leaving measured-force safety unchanged.

**Evidence.** The 25 N candidate reached 69.2 mm but later measured 36.46 N.
The 35 N candidate reached 69.9 mm and measured 35.19 N. Neither completed the
lift.

**Decision and reason.** Reject both and remove the profile close-force field
from production code. A 3.5 mm partial-height gain does not justify crossing
the fixed safety boundary or expanding the public configuration surface.

### 9. Reject global stabilization after catalog regression

**Observation.** The first full 12-profile regression fell from the frozen
8/12 diagnostic outcome to 5/12. `flat_mailer`, `book_box`, and
`near_limit_box` regressed even though all tube geometry/material overrides
were profile-specific.

**Root cause.** `grasp_stability_steps=3` had been placed in the global task
section.

**Decision and reason.** Restore the global value to one and add a profile-level
override used only by both mailing-tube profiles. This repeats the same
scope-minimization pattern used for Genesis rolling/torsional friction.

**Verification.** The 67-test Radeon suite passed before the final simulation.
The scoped full-catalog regression returned to 8/12 with the same per-profile
completion outcomes as the frozen comparator. This is a regression gate, not a
success-rate estimate.

## Retained implementation

| Capability | Retained behavior | Why retained |
| --- | --- | --- |
| Primitive correctness | shared cylinder diameter and radius-derived spawn height | fixes invalid initial physics |
| Geometry-aware grasp | horizontal fingers aligned to tube axis | lower force and correct closure geometry |
| Contact-phase motion | 5 mm final approach and 10 mm lift requests for tubes | isolates slow motion to hard phases |
| Contact verification | three consecutive bilateral frames for tubes | rejects transient contact without regressing boxes |
| Material model | finger friction 2.0 for tube profiles | lower force and better retry quality |
| Pose precision | 10 mm tube close tolerance | enabled actual lift from the table |
| Safety | unchanged 35 N measured-force abort | prevents optimization from redefining success |

## Rejected implementation

| Candidate | Reason rejected |
| --- | --- |
| Dual guide rails prototype | no measurable change in the fixed diagnostic |
| 25 N/35 N profile close force | negligible height gain, safety boundary crossed |
| Global three-frame stabilization | full catalog regressed from 8/12 to 5/12 |
| Claiming tube success | no episode completed transfer and placement |

## Current capability and next optimization work

| Scoring axis | Current capability | Next evidence-producing action |
| --- | --- | --- |
| Simulation | Box and true Cylinder primitives, scoped rolling physics, deterministic catalog | add a versioned concave finger adapter or V-cradle and run matched ablation |
| Learning | ACT train/eval path; compact Diffusion one-step path; VLA-Adapter gated research route | collect at least 300 successful balanced RGB-D episodes, then run three seeds |
| Robustness | size/mass/friction/pose/camera/delay randomization and profile summaries | freeze held-out episode IDs and report confidence intervals per profile |
| Closed loop | approach, stable grasp, lift, place, release, force abort, retry | make recovery collision-aware after a slipped tube before adding more retries |
| GPU optimization | Radeon-only enforcement, AMP training, simulation throughput evidence | profile physics, rendering, transfer, and inference separately before tuning |
| Multimodal | RGB, metric depth, proprioception, contact, task text in the data contract | implement depth late fusion and compare matched RGB versus RGB-D checkpoints |

## Reproduction ladder

Run from the project directory on the prepared Radeon instance:

```bash
source /workspace/rdna/bin/activate
export PYTHONPATH=src

python -m unittest discover -s tests -v

python scripts/evaluate_catalog.py \
  --config configs/catalog_v2.toml \
  --episodes-per-profile 1 \
  --profile mailing_tube \
  --output outputs/tube-diagnostic

python scripts/evaluate_catalog.py \
  --config configs/catalog_v2.toml \
  --episodes-per-profile 1 \
  --output outputs/catalog-regression
```

For a formal result, replace the one-case smoke with a predeclared multi-episode
held-out set. Preserve the config, episode IDs, environment versions, raw JSON,
and SHA-256 hashes with the report.
