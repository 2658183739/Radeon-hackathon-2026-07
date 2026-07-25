# Reset-Fallback Risk-Gated Grasp Planning

## Why this method exists

The balanced 180-episode Radeon screen rejected universal geometry-aware grasp
planning. Collision-checked reset and complete planning both achieved 38/60
successes and 15/60 force aborts, while planning cost 5.57 seconds per attempt
and increased mean episode peak force by 1.65 N. Planning helped one truly
activated `large_narrow_carton` episode but regressed one truly activated
`medium_carton` episode.

The useful distinction was not another box-size threshold. The successful
recovery had an initial robot/parcel intersection and required the verified
fallback reset pose. The regression began collision free and did not need that
intervention. This motivates a conservative risk gate based on a measured
pre-action event.

## Activation rule

The planner is active only when all four conditions hold:

```text
planner_active = planning_enabled
                 AND geometry_eligible
                 AND (gate_disabled OR reset_fallback_used)
```

For the proposed method, the gate is enabled, so `reset_fallback_used` must be
true. That signal is produced by a Genesis robot/parcel collision query after
the scene is built but before physics settling and before the first policy
action. If the historical reset intersects the parcel, the robot moves to the
fixed collision-free fallback and a second query must report zero cross-entity
collision pairs. A failed second query aborts initialization rather than
silently enabling planning.

## Closed-loop integration

`GenesisParcelEnv` first computes static box eligibility, initializes planning
as inactive, builds the scene, and executes collision-checked reset. It then
resolves the final planner state from the observed fallback event. The public
`geometry_grasp_planning_active` property also controls the supervisor's stable
dual-finger contact dwell. This prevents an inactive planner from changing the
historical state-machine timing.

When active, the existing planner still generates box-relative positions and
symmetric wrist orientations, evaluates IK/FK error, restores state after each
candidate, rejects non-finger collisions, ranks manipulability and joint travel,
and replans after retries. The risk gate changes only whether this expensive
path is entered.

## Audit telemetry

Every episode reports:

- static geometry eligibility;
- whether the reset-fallback gate was configured and satisfied;
- final planner activation;
- collision pairs before and after fallback reset;
- planner attempts, selected candidates, events, and synchronized compute time.

The matched comparison report aggregates eligible, gate-satisfied, active, and
gate-avoided episodes together with total and per-attempt planning time. This
makes the latency and GPU-work reduction measurable instead of inferred.

## Reproduction

Run the three mechanism probes:

```bash
bash scripts/run_reset_fallback_gate_probes_rocm.sh
```

Run the frozen 120-episode validation campaign:

```bash
bash scripts/run_reset_fallback_gate_campaign_rocm.sh
```

The validation uses 12 supported profiles, five new local episodes per profile,
and two matched groups. Local IDs `120000`--`120004` are development validation;
the final confirmatory range `200000`--`200039` remains untouched.

## Initial Radeon mechanism evidence

All three mechanism probes passed on one Radeon GPU with ROCm:

| Episode | Reset fallback | Planner | Result | Peak force |
|---|---:|---:|---:|---:|
| `4100004 medium_carton` | no | inactive, 0 attempts | success | 6.05 N |
| `7100002 large_narrow_carton` | yes | active, 1 attempt | success | 9.23 N |
| `1100000 small_carton` | no | inactive, 0 attempts | success | 7.18 N |

These probes validate mechanism and preserve one known recovery; they are not a
performance claim. The matched validation campaign and execution repeats are
required because the earlier trace audit found Genesis/GPU state divergence in
episodes where the planner never activated.
