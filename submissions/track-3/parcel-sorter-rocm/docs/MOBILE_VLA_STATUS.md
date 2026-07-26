# Mobile Bimanual VLA Status (2026-07-26)

This iteration fixes a 43-D non-privileged state contract and a 19-D action contract for the
mobile Bi-Franka. A successful 30-frame, 224x224 RGB-D synchronized pregrasp trajectory was
recorded on one `gfx1100` Radeon. LeRobot SmolVLA was configured with `max_state_dim=48` and
completed one ROCm forward/backward/optimizer update, checkpoint save, reload, and finite 19-D
inference.

The VLA result remains an interface smoke, not learned task success. The separate v41 expert
experiment formed two cup seals, latched the 0.4 kg parcel, lifted it 0.0811 m, transported it 0.30 m,
placed it on the destination support, and released it with 0.0118 m final position error. The
attachment did not break. Peak compliant suction force was 11.84 N and peak cup contact was 2.37 N,
both below the 35 N task limit. This is one deterministic full-task expert episode, not a mobile
generalization result. It is now frozen as the collector seed for multi-profile data generation,
real SmolVLA fine-tuning, and matched Harness/failure-replay ablations.
