# Mobile Bimanual VLA Status (2026-07-26)

This iteration fixes a 43-D non-privileged state contract and a 19-D action contract for the
mobile Bi-Franka. A successful 30-frame, 224x224 RGB-D synchronized pregrasp trajectory was
recorded on one `gfx1100` Radeon. LeRobot SmolVLA was configured with `max_state_dim=48` and
completed one ROCm forward/backward/optimizer update, checkpoint save, reload, and finite 19-D
inference.

This is an interface smoke, not a learned task-success result. The mobile physical suction lift
remains failed: the top-down dynamic approach diverged before a two-cup seal formed. The next
controlled change is bounded Cartesian tracking from the already verified synchronized pregrasp,
followed by pick/lift/place data collection and matched Harness/failure-replay ablations.
