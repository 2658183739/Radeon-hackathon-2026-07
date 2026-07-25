# Parcel Finger Constraint Stability Protocol

## Purpose

The mass-aware 30 mm parcel adapter recovers the frozen `+40 mm` case but turns the previously successful `+45 mm` development sentinel into a deterministic safety abort. The preregistered 240 Hz contact-branch comparison localized the failure without changing the controller:

- the two conditions first differ in contact count at control step 197, physics substep 2;
- their measured parcel-contact force first differs by more than 1 N at 197/4;
- finger position does not differ by 0.1 mm until 202/0;
- at 203/4, the mass-aware model reaches 115.5 mm penetration, 162.19 N stock-finger contact force, about 2.5 m/s finger speed, and 78.01/72.13 N actual finger force;
- the commanded finger force remains `[-20, -20] N` in both conditions;
- the peak is `left_finger/stock_finger_collision_3 <-> parcel`, not an adapter collision.

The Panda MJCF couples `finger_joint1` and `finger_joint2` with `solref="0.005 1"`. Genesis 1.2.3 warns that this time constant is below `2 * dt` at 240 Hz and replaces it with the limiting value `0.008333 s`. Added finger inertia therefore interacts with a constraint running at its discrete-time stability boundary. This protocol tests that mechanism before any controller, model, or task tuning.

## Frozen Intervention

Exactly one candidate is allowed:

- set the mass-aware adapter asset's finger equality-constraint time constant to `0.010 s`;
- retain the original damping ratio `1`;
- retain the exact 30 mm geometry and combined 1240 kg/m3 inertia;
- retain 240 Hz physics, 30 Hz control, the unchanged controller, and the measured 35 N safety abort.

`0.010 s` is the documented Genesis 1.2.3 `constraint_timeconst` default and is greater than `2 * dt = 0.008333 s`. It is not selected from an outcome scan.

## Fixed Case

| Field | Frozen value |
|---|---|
| Config | `configs/catalog_v2.toml` |
| Profile / episode | `medium_carton / 4120001` |
| Candidate | `canonical-long-+0.000-up-0.045` |
| Adapter | 30 mm, 1240 kg/m3, combined rigid-body inertia |
| Runtime | single Radeon `gfx1100`, ROCm 7.2, Genesis 1.2.3 |
| Rates | 240 Hz physics, 30 Hz control |
| Safety abort | measured parcel contact greater than 35 N |
| Rollouts | one fresh-scene rollout |

No new episode, holdout, density, extension, friction, gain, force threshold, grasp candidate, physics rate, or constraint-time scan may be opened.

## Required Evidence

The candidate must record the same 240 Hz contact-branch signals over control frames 196 through 204, plus:

- configured finger constraint time constant and damping ratio;
- outcome and control-frame peak contact force;
- first high-frequency 35 N crossing;
- peak high-frequency contact identity, force, and penetration;
- maximum finger speed, actual force, and controller force;
- raw artifact byte count and SHA-256;
- runtime and GPU identity.

## Decision Rule

The mechanism candidate passes the development sentinel only if the rollout succeeds without a safety abort, all recorded values are finite, peak high-frequency penetration stays below 1 mm, and the configured 35 N gate is never crossed. Passing this one observed sentinel is mechanism evidence, not a robustness claim.

If it fails, retain the result as a Genesis contact-sensitivity benchmark and stop. Do not scan the constraint time constant or weaken the gate. If it passes, implement the setting as an explicit, versioned, default-off adapter option, add unit tests and provenance, then run the already-defined regression checks. A new episode or scorer holdout still requires a separate preregistration.
