# Planned-grasp transport-contract mechanism probe

## Evidence boundary

This probe reuses three already observed development episodes with stable nested-repeat behavior:
`4120001 medium_carton`, `5120003 shoe_box_proxy`, and
`7120004 large_narrow_carton`. They are mechanism cases, not independent performance samples or
a substitute for the sealed confirmation set. Every probe ran in a fresh Python/Genesis process on
one `gfx1100` Radeon with ROCm 7.2, Genesis 1.2.3, and the unchanged 35 N abort limit.

## Candidate

The original planner validated only the grasp pose through IK, FK, static collision, and
manipulability checks. The default-off candidate added a monotonic
`raise -> raise_settle -> transfer -> transfer_settle -> descend` contract, separate raise and
transport reference increments, bounded reference lookahead, phase telemetry, pose/slip-oriented
trace fields, typed configuration, validation, and CLI controls.

## Observations

| Version | `4120001` | `5120003` | `7120004` | Interpretation |
| --- | --- | --- | --- | --- |
| Original planned execution | fail, 159.27 N | success, 29.69 N | fail, 69.00 N | one recovery and two repeatable regressions |
| 10 mm feedback step, 5-frame dwell | timeout, 12.82 N | not run | not run | force avoided, but height oscillation reset dwell |
| 20 mm feedback step, 2-frame dwell | fail, 158.81 N | not run | not run | faster motion restored the impact |
| Monotonic raise, 10 mm feedback step | fail, 21.81 N | timeout, 32.25 N | success, 13.88 N | one regression fixed; slow transport caused slip |
| Monotonic raise and transfer handoffs | fail, 21.81 N | success, 29.69 N | already successful above | original recovery retained; long transport still lost `4120001` |
| 10 mm bounded lookahead | fail, 39.95 N | not expanded | not expanded | faster transport exceeded 35 N |
| 5 mm bounded lookahead | fail, 40.95 N | not expanded | not expanded | smaller increment still failed the safety gate |

The traces explain the intermediate timeouts. `5120003` fell from 201 raise/handoff frames to 20;
before monotonic transfer latching it accumulated 126 `transfer_settle` frames. With both latches it
succeeded in 10.4 s. `4120001` required 301 transport frames without lookahead and lost contact at
frame 259. Lookahead reduced duration but still produced 39.95--40.95 N peaks.

## Decision

Reject promotion and do not start repeats, ordinary-profile sentinels, or confirmation runs. The
contract repaired `7120004` and retained `5120003`, but could not make `4120001` satisfy both task
and 35 N safety requirements. More step-size scans on the same development episode would be
post-hoc tuning.

Keep the implementation default off as an auditable negative control. The next mechanism should
change grasp stability itself through payload-aware candidate scoring, a side-grasp family, or
closed-loop slip detection and regrasp. Any performance claim requires newly frozen episodes.
