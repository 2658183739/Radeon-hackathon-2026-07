# Project Description

Parcel Sorter ROCm is a simulation-first Physical AI submission for sorting parcels with a Franka Panda model on one AMD Radeon GPU. It uses Genesis 1.2.3, ROCm 7.2.1, PyTorch 2.9.1 ROCm, and LeRobot 0.6.1.

**What it does.** The system picks a randomized parcel and routes it to a requested left or right bin in Genesis simulation. It records deterministic expert/reference trajectories, builds a local audited primitive dataset, and runs policy experiments under explicit safety and attribution gates.

**Method.** Overhead RGB and a 43-D non-privileged state feed a policy with a 20-D action contract when primitive progress is enabled. A fixed-rate physics/control loop applies finite-value, Cartesian, tool-command, IK, and force checks. The same evidence ledger names dataset audits, ROCm logs, offline ablations, and media boundaries.

**Innovation.** The contribution is not a claim of passing pure VLA. It is an auditable separation of reference demonstrations, offline action-contract analysis, and strict pure-VLA evaluation, together with structured generation of versioned Panda-MJCF tool adapters from the locked upstream asset.

The work has three intentionally separate evidence tracks:

- Deterministic expert/reference development: 8/10 successful reference trajectories. This establishes demonstration provenance only.
- Offline policy ablation: 42 episode-stage action-contract samples. Raw VLA passes 0/42 envelope checks; safety-clipped VLA and Harness-Lite pass 42/42.
- Strict pure-VLA evaluation: 0/3 successes. This track did not pass and must not be represented as a successful VLA result.

The audited primitive dataset has 7 independent episodes and 4,557 frames. It provides RGB plus a 43-D non-privileged state and a 20-D action contract with primitive progress. The source evidence is local: dataset audit, training log, ablation JSON, and PNG curve are named in `docs/TRAINING_EVIDENCE.md`.

The repository does not claim Sim-to-Real transfer, real-robot footage, a TensorBoard export, public dataset hosting, a public demo-video URL, or a pull-request URL. Each external publication item is pending. See `docs/SIM_TO_REAL_STATUS.md` for the boundary.
