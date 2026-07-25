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
