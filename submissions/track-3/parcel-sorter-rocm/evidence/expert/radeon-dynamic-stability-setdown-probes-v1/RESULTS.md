# Dynamic Grasp and Stateful Recovery Probes

## Scope

These are mechanism probes on three previously observed development episodes,
not success-rate or generalization claims. All physics ran on one `gfx1100`
Radeon through ROCm and Genesis 1.2.3. The 35 N abort line, catalog, seed, and
controller limits remained fixed. New features are disabled by default.

## Isolated dynamic-grasp diagnostic

The diagnostic restores one complete Genesis `SimState` between candidates,
including rigid positions, velocities, accelerations, mass/friction state, and
solver collision caches. Measured restore error was exactly `0.0` for every
probe. Six unique statically feasible candidates were each repeated twice;
both repeats produced identical reported metrics.

Each candidate underwent 24 closing steps, a 30 mm lift, settle, and a 30 mm
transfer toward the destination. The known failed `4120001` production grasp
passed both short tests. Its exact-score replacement led by only 0.00000849 m
in maximum one-frame relative motion. This is not enough predictive separation
to justify an online rollout or a ranking change. `5120003` produced 4/12
stable rollouts and `7120004` produced 12/12, but those known outcomes do not
repair the false negative on `4120001`.

Decision: retain the snapshot-isolated tool for diagnosis, but reject dynamic
ranking integration. No claim is made that a 30 mm test predicts long-distance
transport stability.

## Set-down and regrasp

The next default-off candidate changed the control state instead of increasing
force. The frozen slip signal at frame 159 entered
`recover_setdown -> recover_release -> retry`. The arm moved vertically at no
more than 10 mm per control step, kept the gripper closed, then released after
reaching the original grasp-height envelope or a 20-step cap.

The mechanism itself worked: frames 160--179 completed the set-down with a
21.81 N peak, frames 180--183 released the parcel, and a second grasp was
planned. Without a blacklist, retry selected the same `+40 mm` family and the
second transfer aborted at frame 322 with 129.45 N.

A separate feedback candidate blacklisted the failed pose family. Telemetry
proved that retry rejected `+40 mm` and selected `+45.1 mm`. It still aborted
during the second transfer at frame 300 with 129.98 N. The high force did not
occur during set-down; it occurred after a successful second grasp during the
next transport.

## Decision

Both candidates fail the primary task and safety gates. They remain disabled,
auditable negative controls. Successful sentinels, threshold scans, and new
episodes were cancelled. The next justified direction must change loaded
support geometry or plan transport using a longer-horizon stability model;
another adjacent-height or force sweep is not supported by this evidence.

## Reproduction

The exact commands and artifact contracts are in `RUN-METADATA.txt`. Full
dynamic traces are checked in. The two closed-loop compact summaries bind the
omitted remote frame traces by byte count and SHA-256.
