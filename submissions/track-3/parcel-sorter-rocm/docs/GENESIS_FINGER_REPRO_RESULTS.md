# Genesis Panda Finger Reproduction Results

## Outcome

Two preregistered reductions did not reproduce the mass-aware adapter's
162.19 N closed-loop impulse, but they narrowed the missing mechanism.

| Experiment | Stock inertia | Combined inertia | Conclusion |
|---|---:|---:|---|
| Static zero-velocity hold, 64 substeps | 5.081 N, 0.267 mm | 5.084 N, 0.263 mm | no registered difference |
| Dynamic state + open-loop force replay, 63 substeps | 10.586 N, 0.528 mm | 7.316 N, 0.280 mm | bounded force sensitivity only |

The dynamic comparison first crossed a registered threshold at `198/3`, where
peak parcel-contact force differed by 5.491 N. Contact identity/count,
bilateral support, finger position, velocity, actual force, and controller
force did not cross their thresholds. Neither condition reached the unchanged
35 N or 1 mm safety boundary.

## Source-capture validity

The one allowed source-capture rerun selected the same
`canonical-long-+0.000-up-0.045` candidate and exactly reproduced the original
mass-aware result: control-frame abort at 204, 38.336 N control-rate peak,
162.186 N high-rate peak, and 115.546 mm maximum reported penetration. The
capture contains 64 consecutive 240 Hz events from `196/0` through `203/7`.

Both dynamic replays reconstructed robot and parcel `qpos/qvel` with measured
maximum error `0.0`. Starting at `196/1`, both received the same recorded
nine-DOF control-force sequence. Therefore the negative replay is not caused
by pose rounding or a different command sequence at the exposed force level.

## Interpretation boundary

The result establishes three bounded facts:

1. added adapter inertia is safe in the frozen static grasp;
2. generalized position/velocity plus post-step control forces create a
   measurable contact-force difference, but not the nonphysical impulse;
3. the full failure still depends on state omitted by this open-loop replay,
   such as position-control targets/modes, contact-solver warm-start state, or
   another internal scene state.

This does not prove which omitted state is causal, and it does not establish a
Genesis-wide solver defect. Upstream issue #3051 and PR #3072 were audited, but
their armature bug is not applicable: the locked revision contains the fix and
Panda explicitly authors armature 0.1 through its default class.

No physics option, pose, start frame, force sequence, model parameter, episode,
or safety threshold was scanned. No holdout was opened. VLA, vision, and broad
profile evaluation remain blocked because they cannot repair this physical
baseline. The next admissible work is a separately preregistered capture of
position-control targets/modes or a complete supported Genesis scene state.

## Artifact integrity

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Static stock replay | 740,194 | `c6ad8e12e7db2736be039e7c46a363aabaa96e0f478a7801aea77c93b69953b7` |
| Static mass-aware replay | 740,254 | `2d33b46a093f1e0ee77a6f48a343f5718a614a55fb347ecb50898d5c2117a93b` |
| Static comparison | 1,440 | `d9fcc0daec5c5ea686b3ab78af3f889cb7cfdad4e27d5b8aa33a99f61496c894` |
| Dynamic source capture | 2,176,310 | `fccf7668190f3e64325490774196a27ee54c7fbdacfd85000f1e99235af0f0cb` |
| Dynamic stock replay | 829,413 | `b89824a6cee0538e5d4c2597396fa2f3c06f2eab57fbc44e30386974bdddb77c` |
| Dynamic mass-aware replay | 829,551 | `2d20a99d11cda2f38917a74ff2e6f747d7634a3299f6e002daeacca54bd3dfff` |
| Dynamic comparison | 1,689 | `73f807960452058b724934e4a96ceb3f5fc3fd2460453109c86003b20722a801` |

Raw outputs remain Git-ignored and are bound by path, byte count, and hash in
`evidence/expert/genesis-finger-reproduction-development-v1.json`.
That index also binds the exact pre-telemetry static runner/module hashes and
the final dynamic capture/replay hashes, so later read-only fields do not blur
which code produced each artifact.

The synchronized Radeon/ROCm source tree passed all 268 unit tests.
