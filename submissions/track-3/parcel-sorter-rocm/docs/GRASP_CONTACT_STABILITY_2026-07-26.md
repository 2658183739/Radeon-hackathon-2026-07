# Grasp Contact Stability Investigation

## Scope and decision

This investigation asks why a collision-free static top grasp can still lose a
carton during transport. It uses development episode `4120001` and two
previously successful sentinels, so it is mechanism evidence rather than a
success-rate claim.

The first decision is to reject deeper side and oblique poses for the stock
Panda hand. Those generators remain available only through diagnostic CLI
flags. The production controller still generates the original top-down set.

## Step 1: separate static feasibility from loaded stability

The selected pose for all three transport-contract probes was the centered,
canonical, `+40 mm` top grasp. The failed parcel was neither the heaviest nor
the lowest-friction case:

| Episode | Profile | Mass | Friction | Outcome |
| --- | --- | ---: | ---: | --- |
| `4120001` | `medium_carton` | 0.456 kg | 0.616 | slipped during transfer |
| `5120003` | `shoe_box_proxy` | 0.709 kg | 0.305 | completed |
| `7120004` | `large_narrow_carton` | 0.591 kg | 1.044 | completed |

Therefore a force rule derived only from mass or parcel friction is not
supported. IK, collision clearance, and manipulability are necessary static
checks, but they do not prove loaded grasp stability.

## Step 2: test lower and alternative contact geometry

The original top-down sweep evaluated 24 poses with three IK seeds. Its lower
`0 mm` and `+20 mm` candidates collided with the hand; only the `+40 mm` and
approximately `+45 mm` bands contained feasible evaluations.

Three long-axis side sweeps moved the palm edge margin from 10 to 40 to 65 mm.
Each sweep evaluated 24 side pose/seed pairs and found zero that satisfied both
the frozen IK and collision contract. The 65 mm variant had 12 IK-valid and six
collision-free evaluations, but those sets did not intersect.

The 30 and 45 degree oblique sweep produced 24 IK-valid evaluations. All 24
had a disallowed `hand`/parcel collision. This is a useful negative result: the
stock short-finger geometry cannot reach closer to the carton center of mass by
tilting the palm.

## Step 3: preserve the capability boundary

Lengthened fingers, a concave adapter, or a suction end effector could change
the geometry, but silently modifying the stock robot would make the submitted
claim irreproducible. No such asset is introduced in this experiment.

The code records approach metadata and diagnostic generators so the rejection
can be reproduced. It deliberately does not connect side or oblique poses to
`GenesisParcelEnv._plan_grasp_pose`.

## Step 4: identify a measurable slip signal

Relative pose is defined as `end_effector_position - parcel_position`. During
the failed transfer, the signal was stable through frame 158, then changed by
12.56 mm in one control frame at frame 159. Its vertical component was
+10.95 mm, meaning the carton moved downward relative to the hand. Contact
became unilateral and measured force jumped from 5.06 N to 16.52 N.

An accumulated 5 mm threshold is invalid. Both successful sentinels exceeded
5 mm of accumulated relative displacement. Large single-frame changes also
occurred when `7120004` entered the destination bin. A valid candidate must
therefore combine:

- an active `raise` or `transfer` phase;
- a single-frame 3D relative displacement jump;
- a positive downward relative component;
- remaining contact force that can still be reinforced; and
- minimum horizontal distance from the destination, so normal in-bin release
  is excluded.

Replaying the frozen traces with `8 mm` 3D, `6 mm` downward, `1 N` contact, and
`80 mm` destination-distance gates selected frame 159 of `4120001` only. It
selected zero frames in `5120003` and `7120004`. This freezes the next
mechanism probe; it does not yet prove that added force will recover the task.

## Evidence and verification

The compact machine-readable record is
`evidence/expert/radeon-grasp-approach-diagnostics-v3.json`. It includes raw
artifact SHA-256 values because full per-pose JSON remains in the ignored
Radeon output directory. After adding the diagnostic candidates, the complete
Radeon suite passed 191 tests.

## Next gated experiment

Implement default-off slip telemetry and a short, bounded close-force boost.
The command must retain a substantial margin below the unchanged 35 N measured
force abort. Test `4120001` first, then rerun both successful sentinels. Only a
safe mechanism probe may proceed to new predeclared episodes.

## Gated experiment outcome

The implementation uses an 8 mm relative jump, 6 mm downward component, 1 N
contact floor, and 80 mm destination exclusion. A 2 N boost raises the close
command from 20 N to 22 N for 15 frames. It is default-off, requires the staged
transport contract, and exposes event and force telemetry. A separate ablation
switch disables transport lookahead so the probe reproduces the feedback trace
used to freeze the detector. Default behavior remains unchanged. The complete
Radeon suite passed 200 tests.

The `4120001` probe triggered at the expected frame 159 and again at frame 261.
Peak measured force was 22.92 N, below the unchanged 35 N line. The first boost
restored bilateral contact only temporarily. Final contact loss moved from
frame 260 to frame 261; both the feedback baseline and candidate failed after
one retry in 19.97 s.

This fails the primary task gate. The two successful sentinels, parameter scans,
and new-episode validation are therefore cancelled. Force-only recovery remains
a disabled negative control. The next valid mechanism must change capture
geometry or execute a safe set-down/regrasp transition.

## Dynamic screening outcome

The follow-up diagnostic used complete Genesis scene snapshots to isolate six
unique statically feasible candidates per episode, with two repeats each. The
maximum measured restore error was `0.0`; repeat metrics were identical. Each
rollout closed for 24 steps, lifted 30 mm, and transferred 30 mm.

The diagnostic did not pass its predictive gate. The `+40 mm` candidate known
to fail later in `4120001` was classified stable in both repeats. The
alternative `+45 mm` candidate improved maximum one-frame relative motion by
only 0.00849 mm. Short loaded rollouts remain useful for mechanism inspection,
but are not integrated into grasp ranking.

## State-changing recovery outcome

The next default-off response changed state rather than force. At a slip, it
kept the gripper closed, lowered vertically by at most 10 mm per control frame,
released at the original grasp-height envelope or a 20-frame cap, and then
replanned. On `4120001`, set-down and release completed at frames 160--183 with
a 21.81 N set-down peak.

The first retry reused `+40 mm` and reached 129.45 N during the second transfer.
A separate failed-candidate blacklist correctly forced `+45.1 mm`, but that
retry reached 129.98 N during its second transfer. The failure is therefore not
unsafe set-down and not merely repeated selection of one height. Both features
remain disabled. The next test must alter loaded support geometry or evaluate
stability over a horizon that includes the failure-producing transport.

## Full-horizon diagnostic and controller-faithful counterfactual

The diagnostic horizon was extended through raise, transfer, and descent with
bounded Cartesian waypoints. All six candidates passed, including the
production `+40 mm` candidate already known to lose the carton. This is a
second false negative: direct waypoint IK bypasses the production approach
error, two-step action delay, and feedback dynamics. The idealized rollout is
therefore rejected as a selector.

A separate runner then preserved the complete production closed loop and
created a fresh Genesis scene for every candidate. It disabled retries and
changed exactly one variable: an allowlist rejected every generated candidate
except the requested target. The production `+40 mm` candidate reproduced the
missed-destination failure at 21.81 N. Four of five alternatives completed;
centered `+45 mm` was best at 10.31 N and 16.93 s, while offset `+40 mm` on the
opposite side crossed the unchanged limit at 53.74 N. Requested, allowed,
rejected, and selected candidate IDs are recorded in every planning event.

Two additional centered `+45 mm` executions were identical on the reported
task metrics and both succeeded. The `shoe_box_proxy` and
`large_narrow_carton` sentinels do not have that exact candidate in their
statically feasible sets, so the tested fallback remained centered `+40 mm`;
both completed at 29.69 N and 9.95 N respectively.

This is a valid label-generation mechanism, not yet a production policy. One
observed development episode cannot justify a general `+45 mm` ranking rule.
The next gate is to freeze new episode IDs, collect controller-faithful labels,
train a small PyTorch/ROCm candidate scorer, and evaluate it on an untouched
paired holdout. Compact evidence is in
`evidence/expert/radeon-full-horizon-counterfactual-grasp-v1.json`.
The final Radeon compile and complete `unittest` suite passed 227 tests.
