# Contact-Branch Diagnostic Protocol

## Purpose

The mass-aware 30 mm parcel adapter preserved the known `+40 mm` recovery but
changed the known-success `+45 mm` sentinel into an exactly repeated 38.3364 N
abort. The aggregate trace shows a jump from eight bilateral contacts to 19
unilateral contacts between control frames 202 and 203, but it does not identify
the colliding geometries or finger-actuator state.

This protocol is frozen before collecting the missing high-rate signals. It is
a mechanism diagnostic, not a performance, robustness, or model-selection
experiment. No scorer holdout or new episode may be opened.

## Fixed comparison

| Field | Frozen value |
|---|---|
| Profile / episode | `medium_carton / 4120001` |
| Candidate | `canonical-long-+0.000-up-0.045` |
| Simulator | Genesis 1.2.3 |
| Accelerator | one Radeon `gfx1100`, ROCm 7.2 |
| Controller | unchanged controller-faithful transport |
| Adapter geometry | 30 mm per finger |
| Effective density | 1240 kg/m3 |
| Safety abort | unchanged measured 35 N |
| Condition A | adapter collision geometry with stock explicit finger inertia |
| Condition B | same geometry with combined mass, center, and full inertia |
| High-rate window | control frames 196--204 inclusive, all 8 physics substeps |
| Rollouts | one fresh-scene rollout per condition |

The physical-model ablation must be explicit in configuration and telemetry.
Condition A is not a deployable physical claim; it only reproduces the earlier
lightweight geometry approximation under the current code.

## Signals

At every 240 Hz physics substep in the frozen window, record:

- command, transport phase, end-effector pose, and parcel pose;
- every active robot contact, including entity, global geom/link IDs, link
  names, adapter-versus-stock geom label, position, normal, penetration, and
  forces on both bodies;
- both finger DOF positions and velocities;
- both finger actual internal forces and position-controller forces;
- contact count, peak force, bilateral parcel support, and 35 N crossing.

The compact result must report the first condition divergence, first loss of
bilateral support, first force above 35 N, peak-force contact identity, and the
maximum absolute actual/control force per finger. Raw outputs remain ignored
but are bound by byte count and SHA-256.

Cross-condition divergence thresholds are frozen at an exact contact-signature
or bilateral-state change, 1 N parcel/contact or finger-force difference,
0.1 mm finger-position difference, and 0.01 m/s finger-velocity difference.
These thresholds describe the trace; they do not trigger controller actions.

## Decision tree

1. If the spike is adapter-to-parcel contact, investigate contact discretization,
   collision-edge geometry, and compliance under a separately frozen model.
2. If it is robot-to-bin, robot-to-plane, or self contact, add swept loaded-path
   clearance to the planner; do not tune the grasp height.
3. If contact identity is unchanged but finger actual/control forces diverge,
   test a bounded trajectory-modulation or impedance candidate; do not increase
   grip force or weaken the supervisor.
4. If no signal explains the branch, retain both results as a simulator contact
   sensitivity benchmark and do not start the multi-profile campaign.

No density, extension, friction, controller-gain, force-threshold, or candidate
scan is allowed on this observed sentinel. A follow-up intervention needs a
new preregistered mechanism gate before any larger evaluation.

## Literature rationale

- *Contact Models in Robotics: A Comparative Analysis* (T-RO 2024,
  DOI `10.1109/TRO.2024.3434208`) motivates treating contact-model sensitivity
  as an experimental variable rather than hidden simulator detail.
- *Reactive Diffusion Policy* (RSS 2025,
  DOI `10.15607/RSS.2025.XXI.052`) uses a slow visual policy with fast tactile
  reaction for contact-rich manipulation; it is a later learning layer after
  trustworthy high-rate signals exist.
- *Bioinspired trajectory modulation for effective slip control in robot
  manipulation* (Nature Machine Intelligence 2025,
  DOI `10.1038/s42256-025-01062-2`) reports trajectory adaptation as an
  alternative to grip-force escalation, matching this project's unchanged
  force boundary.
- *Diffusion Suction Grasping with Large-Scale Parcel Dataset* (IROS 2025,
  DOI `10.1109/IROS60139.2025.11246892`) is directly relevant to future parcel
  geometry coverage, but suction is a separate end-effector class and cannot
  explain the present parallel-jaw contact branch.

Retrieval used targeted OpenAlex and Crossref queries on 2026-07-26. The arXiv
API query timed out and is recorded as a partial-source failure, not an empty
literature result.
