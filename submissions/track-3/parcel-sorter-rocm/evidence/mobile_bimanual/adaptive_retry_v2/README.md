# Adaptive Retry v2 Evidence

This compact evidence replays `primitive-v2-dry-run-holdout-005`, one of the
six failures already observed in the frozen 100-trial primitive-checkpoint
campaign. It does not add a new evaluation population.

The nominal `pash_arm@nominal` attempt reproduced the registered lift failure.
Harness then removed learned arm authority and selected
`pash_base@gentle_lift`: 0.75 approach and vertical speed, 0.5 mm additional
contact penetration, and 15 mm additional lift height. The second attempt
completed pickup, transport, placement, and release at 1.44 cm placement error,
4.84 N peak contact force, and zero suction breaks.

The successful attempt wrote 673 frames at 30 Hz with 43-D state, 19-D action,
RGB, metric depth, and task text. `recovery-dataset-audit.json` passed every
check. The 35 MB trajectory remains on the Radeon workspace at
`/workspace/parcel-sorter-opt-v1/outputs/pash-recovery-known-failure-005-v2/attempt-02-pash_base/recovery-dataset`;
it is intentionally not committed to Git.

This is a paired mechanism demonstration, not an estimate of retry recovery
rate. First-attempt and eventual success must remain separate in all reports.
