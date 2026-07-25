# Geometry-Aware Grasp Planning on Radeon

This note records observable engineering evidence, hypotheses, implementation
choices, experiments, and decisions. It is an auditable development record,
not a transcript of private model reasoning.

## Outcome

On one AMD Radeon `gfx1100` with ROCm 7.2, the fixed 20-episode
`large_narrow_carton` comparison improved from 5/20 to 15/20 successes. The
candidate recovered ten baseline failures, regressed none, retained zero drops,
and increased successful throughput from 98.25 to 359.36 parcels/hour. Force
aborts fell from 8/20 to 4/20 and maximum force fell from 111.30 N to 46.99 N.

The candidate is still experimental. It failed the preregistered 18/20 success
and at-most-1/20 force-abort gates, so `geometry_aware_grasp_planning_enabled`
remains false by default.

## Problem and causal boundary

Link-level Radeon diagnostics showed that many large cartons intersected the
historical reset pose before the 30 Hz controller could react. Collision-checked
reset improved the hard set from 1/20 to 5/20, but remaining high cartons still
stalled above the nominal grasp or generated unsafe contact. Expanding the
"at pregrasp" tolerance changed state timing without creating a feasible pose
and was rejected. The next intervention therefore had to change grasp geometry,
not completion semantics or the 35 N safety limit.

## Implemented pipeline

1. Planning is scoped to rigid boxes whose height is at least the 105 mm palm
   clearance plus 20 mm minimum side overlap: 125 mm. Lower boxes retain the
   historical controller, stability dwell, and motion limits.
2. The planner generates longitudinal offsets at the centre and up to +/-50 mm,
   vertical offsets at 0/20/40 mm and the geometry-limited maximum, and canonical
   plus equivalent pi-shifted wrist orientations.
3. Every pose is solved from the live joints, historical reset, and verified
   collision-free reset seeds. IK/FK error gates, finite-state restoration, and
   non-finger collision checks reject invalid solutions.
4. Feasible solutions rank centred and lower side contact first, then shorter
   joint travel, Jacobian minimum singular value, and non-finger clearance.
   Sub-threshold micrometre-scale IK noise is treated as a pass bucket rather
   than a ranking signal.
5. The selected XYZ and quaternion are shared by approach, capture, closure,
   and lift. A retry clears delayed actions and replans instead of reusing stale
   parcel geometry.
6. Planned grasps require five consecutive dual-finger contact frames. Planned
   placement descent is capped at 5 mm per control step.
7. The final grasp approach uses a geometry-derived two-stage limit: 5 mm for
   boxes from 125 mm to below 160 mm, and 2.5 mm from 160 mm upward. The 160 mm
   boundary equals 105 mm palm clearance plus the 55 mm maximum vertical grasp
   offset.

## Swept collision-gate negative result

An experimental gate interpolated each commanded joint segment at no more than
0.025 rad per joint sample and checked every sample for non-finger collision.
It preserved four known recoveries, but rejected zero waypoints in six force
challenge episodes. Those episodes still force-aborted at 37.21--50.66 N while
the gate added 1.66--7.76 seconds of synchronized checking per episode. The
feature remains available only through `--grasp-planning-waypoint-gate`; it is
off by default and is not part of the v2 result.

## Step-size experiments

The first scoped 5 mm candidate preserved the previous `7000005` regression
sentinel and recovered four of six force challenges, but `7000008` reached
115.11 N and `7000016` reached 42.78 N. A global 2.5 mm candidate fixed those
two episodes but regressed medium-height `7000001` and `7000002`. This
non-monotonic contact response ruled out one global speed scalar.

The final two-stage policy was re-executed without CLI overrides on the four
cross-sentinels. Medium boxes `7000001/2` selected 5 mm and succeeded at
31.38/21.42 N. Tall boxes `7000008/16` selected 2.5 mm and succeeded at
8.21/31.23 N. Only after these checks did the fixed 20+20 comparison run.

## Formal protocol and results

Both arms used the same `large_narrow_carton` profile, seed, episode indices
`7000000`--`7000019`, collision-checked reset, physics, controller, 35 N hard
abort, Radeon device, and ROCm runtime. The only allowed configuration
difference was `task.geometry_aware_grasp_planning_enabled`.

| Metric | Reset baseline | Geometry planner | Delta |
| --- | ---: | ---: | ---: |
| Success | 5/20 (25%) | 15/20 (75%) | +50 points |
| Force aborts | 8/20 (40%) | 4/20 (20%) | -20 points |
| Drops | 0/20 | 0/20 | unchanged |
| Successful throughput | 98.25/h | 359.36/h | 3.66x |
| Maximum force | 111.30 N | 46.99 N | -64.31 N |

The 95% Wilson interval for candidate success is 53.13%--88.81%, so this small
hard-set result must not be reported as production reliability.

## Remaining failures and next work

Episodes `7000006`, `7000015`, and `7000019` still abort during approach;
`7000014` aborts during lift after one retry; `7000017` reaches pregrasp but
times out after a lost grasp. The next work should target low-box contact
prediction, collision-free retry retreat, and lift retention. It should not
raise the 35 N limit or continue fitting height thresholds to this same set.

After a new candidate passes 18/20 success and at most 1/20 force abort, expand
to held-out box, flat parcel, and cylinder strata before reopening balanced
RGB-D collection and learned-policy ranking.

## Reproduction

```bash
source scripts/activate_radeon_env.sh
PYTHONPATH=src python -m unittest discover -s tests -v

bash scripts/run_geometry_aware_grasp_planning_ab_rocm.sh \
  configs/catalog_v2.toml \
  outputs/radeon-geometry-aware-grasp-planning-ab-v2-tiered
```

Committed compact evidence is indexed by
`evidence/expert/radeon-geometry-aware-grasp-planning-ab-v2-tiered-*`.
Trace-rich source summaries remain on the Radeon workspace and are bound by the
remote SHA-256 manifest.
