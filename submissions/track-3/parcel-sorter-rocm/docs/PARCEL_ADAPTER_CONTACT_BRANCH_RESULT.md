# Parcel Adapter Contact-Branch Result

## Outcome

The preregistered diagnostic successfully attributed the deterministic mass-aware adapter regression to a high-frequency numerical contact branch, but the single preregistered constraint-time candidate did not fix it. No task parameter, controller gain, force threshold, density, adapter length, friction, grasp candidate, episode, or holdout was tuned.

This is a bounded development result for `medium_carton / 4120001 / canonical-long-+0.000-up-0.045`. It is not a robustness or simulator-wide claim.

## Differential Diagnosis

Both conditions used the same 30 mm adapter collision geometry, 1240 kg/m3 density declaration, controller, trajectory, 240 Hz physics, 30 Hz control, and measured 35 N abort. The only initial difference was whether adapter mass, center of mass, and full inertia were combined with each finger.

| Signal | Stock-inertia geometry ablation | Combined mass-aware inertia |
|---|---:|---:|
| Task outcome | success | safety abort |
| Control-frame peak force | 12.547963 N | 38.336445 N |
| First contact-signature difference | reference point | 197/2 |
| First force difference greater than 1 N | reference point | 197/4 |
| First finger-position difference greater than 0.1 mm | reference point | 202/0 |
| First bilateral-support loss | none | 203/5 in aligned comparison |
| High-frequency peak force | 10.909115 N | 162.186157 N |
| High-frequency maximum penetration | below 1 mm | 115.545757 mm |
| Maximum absolute finger speed | below 0.01 m/s | 2.585403 / 2.414580 m/s |
| Maximum absolute actual finger force | 0.076706 / 0.072491 N | 78.010399 / 72.132576 N |
| Maximum absolute controller force | 20 / 20 N | 20 / 20 N |

The first branch is subtle. At 197/2, the lightweight condition acquires a ninth stock fingertip contact while the mass-aware condition retains eight contacts. The controller commands are still identical. The mass-aware trajectory then remains apparently symmetric through 203/3. One 1/240-second step later, a `left_finger/stock_finger_collision_3 <-> parcel` contact reports 115.5 mm penetration and 162.19 N. Finger velocities and actual forces jump in the same step, while commanded forces do not change. The adapter collision geometry appears only after this instability and is not the peak contact.

The evidence therefore supports this ordering:

1. inertia changes the discrete stock-fingertip contact branch;
2. small force differences accumulate before measurable finger-position divergence;
3. the contact solve produces a nonphysical penetration/force impulse;
4. finger state and actual internal force diverge after that impulse;
5. the unchanged 35 N monitor correctly aborts the rollout.

It does not support a claim that the VLA, grasp selector, high-level controller, or adapter box directly caused the peak.

## Frozen Constraint-Time Test

The Panda MJCF contains a two-finger equality `solref="0.005 1"`, and Genesis logs a warning that a `0.005 s` constraint time constant is raised to `0.008333 s` at 240 Hz. A single candidate was preregistered before execution: change only the adapter asset's equality time constant to the documented Genesis default of `0.010 s`, retaining damping ratio 1 and every runtime/task value.

An initial setup-verification run changed only the generated adapter file. Environment construction immediately regenerated that file from the Genesis source asset, so the intervention was overwritten before either scene was built. Its value-identical trajectory is classified as an excluded no-op setup run, not candidate evidence.

For the valid run, the source asset was changed within the command scope before regeneration. Both the source and generated MJCF showed `solref="0.010 1"`, and the previous constraint-time warning disappeared. The candidate then failed earlier and more severely:

- the measured-force monitor aborted at control frame 134 instead of 204;
- control-frame peak force increased to `105.85269165039062 N`;
- terminal transport phase was `raise`, rather than the later `transfer` failure;
- the rollout ended before the frozen 196--204 branch window, so it correctly contains zero contact-branch samples rather than fabricated high-frequency evidence.

The source and generated MJCF files were restored to `0.005 s` after the run. The applied candidate is rejected and is not implemented in the production configuration. Per the preregistered stop rule, no constraint-time scan or alternative episode was opened.

## Safety and Engineering Decision

The mass-aware 30 mm adapter remains a physically honest model and a useful negative benchmark, but the known `+45 mm` sentinel is not deployment-ready in Genesis 1.2.3 at the current solver settings. The project must keep the 35 N measured-force abort and must not present the stock-inertia ablation as a physical solution.

The next allowed engineering work is upstream-facing: reduce the telemetry to a minimal Genesis reproduction, determine which solver constraint emits the warning, and test a simulator fix or documented solver option under a new preregistration. VLA fine-tuning, visual-model changes, and broad robustness evaluation remain blocked because they cannot repair or validly evaluate this low-level numerical failure.

## Artifact Integrity

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Lightweight raw rollout | 4,356,812 | `ede683c96eb84a918a99d6a27988709d6b1c38382552c36a26f13429fb82fa81` |
| Mass-aware raw rollout | 2,040,227 | `d29b268f58b3c232d6a8e3e43dd51567cd2f71db2c3e224345df25d77a74716f` |
| Frozen comparison | 13,786 | `12cf7d198f272e589a87547013ecd070b9ed8a28270116d2f150516ebd7c7fb1` |
| Excluded overwritten setup run | 2,040,225 | `af74e55abce61a11d54a4230aec50256463efd4a6d4f47f8653a88aaebfeca1d` |
| Rejected applied 0.010 s candidate | 619,908 | `0fc869e42060a2e3bb0a42570a441d6d3fc8ff30e4627ce3df2857d9683edf68` |
| Temporary 0.010 s MJCF | n/a | `9baed9de8ed912d717de998e966688875f453e552c4ddf1dfc514a1ab5f3e000` |
| Restored 0.005 s MJCF | n/a | `c1785752199e90c2631c3bff46eb6733545d35f707819686dec590c236e95e32` |

Raw rollout files remain excluded from Git; the committed evidence binds them by path, byte count, and digest.
