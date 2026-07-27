# Mobile Tri-Suction/V-Cradle Cooperative-Carry Ablation

## Scope and claim boundary

This experiment tests whether the mobile dual-Franka robot can cooperatively
carry an extra-long rigid carton with three left-arm suction cups and a physical
right-arm V cradle, and whether SmolVLA v2 can participate in base control under
Harness-Lite. Every run used one AMD Radeon `gfx1100`, ROCm 7.2.1, and Genesis
1.2.3.

The fixed development parcel is `1.44 x 0.12 x 0.18 m`, `0.40 kg`, with friction
`0.90`; transport is 30 cm. It deliberately exceeds the parallel-jaw range and
is a mechanism case, not a success rate, unseen-geometry generalization, carrier
coverage, or sim-to-real result. The formal learned-policy result remains
SmolVLA v2 at `96/100` on its independent frozen campaign.

## Robot and control path

- a three-DoF holonomic base and two seven-DoF Franka Panda arms;
- three left-arm cups with collision, contact, compliant force, and breakable
  attachment constraints;
- a two-rail physical V cradle on the right arm;
- a 240 Hz Genesis physics/safety loop and 3 Hz SmolVLA/Harness loop;
- lift only after two cups seal and cradle contact persists for 24 physics steps;
- separate left/right incremental IK every eight physics steps during lift and
  place, avoiding joint-branch changes from one-shot coupled IK;
- unchanged 35 N force, 8 cm lift, 1 cm base, 4 cm parcel XY, and 2.5 cm
  pre-release Z gates.

## Closed-loop placement

The v18 one-shot place IK drifted about 6.6 cm laterally. v19 replaced it with
independent incremental IK and reduced final error to 2.26 cm, but continued
descending after arrival and broke suction at step 708. v20 retained the exact
position gate and stopped descent only after it held for 24 consecutive physics
steps. It confirmed placement at step 268, accepted all 34 place IK updates,
released deliberately, and succeeded.

## Payload-aware Harness

SmolVLA v2 consumes top RGB, 43-D non-privileged state, and task text and emits a
19-D action. Arms, suction, and cradle remain under expert and safety control;
the VLA contributes bounded base residuals.

The ordinary-parcel Harness preserves at least 50% expert directional progress.
v21 showed this was insufficient for the extra-long cooperative payload. v22
raised the cooperative floor to 75%, reducing error without meeting the fixed
deadline.

A one-way deadline-liveness gate was therefore added. If remaining distance is
greater than remaining time times expert forward speed times a conservative
actuator-capacity ratio, transport is handed to the expert for the rest of the
episode. The ratio is 0.60, calibrated from the independent v20 expert shadow
run. v23 used an uncalibrated 0.75 ratio, handed off too late, and failed. The
gate does not extend time, raise speed, relax success, or update model weights.

## Paired development results

| Run | Main change | Result | Final error | Interpretation |
| --- | --- | ---: | ---: | --- |
| v19 | Incremental dual-arm place IK | fail | 2.26 cm | post-arrival overdrive broke suction |
| v20 | 24-step placement confirmation | pass | 2.26 cm | expert mechanism passed |
| v21 | VLA, 50% progress floor | fail | 11.03 cm | insufficient transport progress |
| v22 | VLA, 75% progress floor | fail | 8.31 cm | static floor still insufficient |
| v23 | deadline gate, capacity 0.75 | fail | 7.72 cm | handoff at step 1793 was too late |
| v24 | deadline gate, capacity 0.60 | pass | 2.16 cm | VLA execution retained; task completed |
| PASH-v25 | v24 + Force-Memory Harness | pass | 2.11 cm | tightened 11/68 calls; two full fallbacks |

v24 lifted 8.53 cm and completed transport, placement, and release with zero
suction breaks. Peak cradle, attachment, and cup-contact forces were 30.65 N,
27.03 N, and 16.95 N, all below 35 N. All 90 lift and 34 place IK updates were
accepted. SmolVLA ran 68 inferences and controlled 647 physics steps across the
episode, including 95 transport steps before the irreversible handoff at step
96. Mean selected Harness scale was 0.926 with zero emergency stops. Warm mean
and P95 inference latency were 199.59 and 201.63 ms.

PASH-v25 changes neither SmolVLA weights, the deadline gate, nor task thresholds; it only enables
the six-sample contact-force memory. It lifted 8.52 cm, completed 30 cm transport, placement, and
release with zero suction breaks and 30.64 N peak cradle force. VLA materially actuated 657 physics
steps. Force-Memory tightened 11 of 68 calls, requested two full fallbacks, and produced zero
emergency stops; warm mean/P95 inference was 204.52/207.94 ms. This verifies integration on the
Radeon loop without breaking the development case, not a statistical success improvement.

## Decision

Keep tri-suction/V-cradle geometry, incremental dual-arm IK, stable placement
confirmation, and the cooperative-payload deadline gate. SmolVLA v2 weights and
the ordinary-parcel 50% Harness configuration remain unchanged. v24 and PASH-v25 are
integration and mechanism evidence only. They do not supersede the formal
96/100 baseline before a new frozen campaign varies size, mass, friction, and
offset over at least 100 episodes.

Compact results, full remote-summary hashes, and the claim boundary are under
`evidence/mobile_bimanual/cooperative_cradle_v1/`. Full traces and logs remain
in the Radeon workspace under `outputs/mobile-cooperative-cradle-*`.
