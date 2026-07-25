# Feedback Slip-Recovery Mechanism Probe

## Evidence boundary

This is a single, already observed development episode used to test a physical
mechanism. It is not an independent success-rate sample and does not open the
reserved confirmation namespace. The comparison reuses the feedback-limited
`4120001 medium_carton` trace from the transport-contract investigation.

Both runs used one `gfx1100` Radeon, ROCm 7.2, Genesis 1.2.3, the stock Panda
parallel-jaw gripper, and the unchanged 35 N measured-force abort threshold.
The candidate restored measured-pose transport by disabling bounded lookahead;
the only new active mechanism was the frozen slip detector and force response.

## Frozen mechanism

- Trigger only during payload `raise` or `transfer`.
- Require at least 8 mm single-frame relative displacement.
- Require at least 6 mm downward parcel motion relative to the hand.
- Require at least 1 N measured contact and 80 mm horizontal distance from the
  destination.
- Increase the close-force command from 20 N to 22 N for 15 control frames.
- Keep the command target at least 10 N below the fixed 35 N abort threshold.

The command-force margin is a configuration invariant, not a claim that
measured contact force cannot overshoot under rigid-body dynamics. The physical
probe remains the safety authority.

## Result

| Measure | Feedback baseline | Slip recovery |
| --- | ---: | ---: |
| Task success | no | no |
| Terminal stage | approach after one retry | approach after one retry |
| Duration | 19.97 s | 19.97 s |
| Peak measured contact force | 21.81 N | 22.92 N |
| First loss of bilateral contact | frame 159 | frame 159 |
| Final loss of contact | frame 260 | frame 261 |
| Recovery triggers | n/a | frames 159 and 261 |
| Boosted command frames | n/a | 30 |

The first trigger exactly reproduced the frozen frame-159 signal: 12.56 mm
relative displacement, 10.95 mm downward component, 16.52 N contact, and
337.90 mm destination distance. The 22 N command produced a 22.92 N measured
peak on the next frame and restored bilateral contact temporarily.

The response did not stabilize the payload. The carton continued to descend,
was no longer classified as lifted by frame 250, and lost contact at frame 261.
A second valid signal occurred at 167.93 mm from the destination, but bilateral
contact was already absent; increasing close force cannot recapture a carton
outside the jaws. Relative to the feedback baseline, the mechanism delayed
final loss by one frame without changing the task outcome or duration.

## Decision

Reject promotion and retain the implementation as a default-off negative
control. The primary episode failed, so the preregistered gate cancels the two
successful sentinels, threshold scans, force scans, repeats, and new-episode
validation. The 35 N limit remains unchanged.

Revisit only with a mechanism that changes capture geometry or recovery state,
such as an explicitly licensed longer-finger/cradle asset, a safe set-down and
regrasp transition, or a gripper that can establish a deeper grasp. A larger
force boost alone is not justified by this trace.

## Reproduction

```bash
source scripts/activate_radeon_env.sh
PYTHONPATH=src python scripts/run_expert.py \
  --config configs/catalog_v2.toml \
  --backend rocm \
  --episodes 1 \
  --start-episode 120001 \
  --profile medium_carton \
  --output outputs/radeon-slip-recovery-probe-v2/4120001-feedback \
  --collision-checked-reset \
  --geometry-aware-grasp-planning \
  --grasp-planning-reset-fallback-gate \
  --grasp-planning-transport-contract \
  --grasp-planning-disable-transport-lookahead \
  --grasp-planning-raise-step 0.02 \
  --grasp-planning-transport-step 0.01 \
  --grasp-planning-transfer-settle-steps 2 \
  --transport-slip-recovery
```

The compact JSON preserves the complete safety summary and hashes the omitted
full trace. `TRACE-COMPARISON.json` records the fixed comparison values and
source hashes. Full trace-rich summaries remain on the Radeon workspace.
