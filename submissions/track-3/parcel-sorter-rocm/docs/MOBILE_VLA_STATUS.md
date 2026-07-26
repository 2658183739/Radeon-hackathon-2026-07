# Mobile Bimanual VLA Status (2026-07-26)

This iteration fixes a 43-D non-privileged state contract and a 19-D action contract for the
mobile Bi-Franka. A successful 30-frame, 224x224 RGB-D synchronized pregrasp trajectory was
recorded on one `gfx1100` Radeon. LeRobot SmolVLA was configured with `max_state_dim=48` and
completed one ROCm forward/backward/optimizer update, checkpoint save, reload, and finite 19-D
inference.

The VLA result remains an interface smoke, not learned task success. The separate v40 physical
experiment formed two cup seals, latched the 0.4 kg parcel, and lifted it 0.0811 m without breaking
the attachment. Peak compliant suction force was 10.10 N and peak physical cup contact was 2.37 N,
both below the 35 N task limit. This verifies mobile suction pickup and lift, not transport or place.
The next controlled step is base transport and release, followed by multi-profile data collection,
real SmolVLA fine-tuning, and matched Harness/failure-replay ablations.
