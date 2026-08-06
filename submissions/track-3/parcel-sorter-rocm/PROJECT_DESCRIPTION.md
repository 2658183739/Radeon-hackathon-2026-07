# Project Description

Parcel Sorter ROCm is a Genesis manipulation project built and evaluated on one
AMD Radeon GPU with ROCm. A Franka Panda must pick a randomized parcel, carry it
across the workcell and release it in the requested left or right destination.

The project grew out of a gap we repeatedly saw during training: a policy could
improve its loss while still producing actions that were unsafe or ineffective
in closed loop. Instead of hiding that gap behind one aggregate score, we built
three explicit execution routes.

The first is a deterministic scripted task agent. It reads privileged Genesis
state, runs a finite-state supervisor and provides reproducible demonstrations.
It completed 8 of 10 development episodes and produced the clips in the demo
video. The second is an agent-guided VLA route: SmolVLA or PI0.5 proposes an
action or residual, while Harness-Lite checks Cartesian progress, force, IK and
tool limits before execution. This hybrid route passed all 42 frozen offline
action-envelope samples, but it is not claimed as closed-loop task success. The
third route gives the learned policy ownership of the declared task actions.
That strict pure-VLA evaluation scored 0/3.

The learned-policy input contract uses overhead RGB, language and a 43-D
non-privileged state. With primitive progress enabled, the output is a 20-D
action. The local SmolVLA checkpoint was trained for 2,800 steps on an audited
dataset containing 7 independent episodes and 4,557 frames. PI0.5 experiments
use a persistent local policy service so one GPU-resident checkpoint can span
multiple episodes without being reloaded.

The engineering contribution is the boundary between these parts: a common
`ActionPolicy` API, a reproducible scripted teacher, versioned Panda tool
adapters, bounded hybrid action selection, and an evidence ledger that ties
every result to its controller and checkpoint. The project also documents the
development-agent layer: delegated Codex work used GPT-5.6 Luna through
Responses-style tool calls. The model helped implement, orchestrate and audit
the submission; it was not part of robot inference.

The recorded runtime is Genesis 1.2.3, ROCm 7.2.1, PyTorch 2.9.1 ROCm,
LeRobot 0.6.1 and Python 3.12. This submission is simulation-only. Sim-to-Real,
real-robot footage and a successful pure-VLA result are future work rather than
claims made here.

Review material:

- [59-second demo](videos/genesis_panda_8_success_reference_demo.mp4)
- [Agent, model, API and architecture](docs/AGENT_MODEL_ARCHITECTURE.md)
- [Training evidence](docs/TRAINING_EVIDENCE.md)
- [Ablation results](docs/ABLATION_RESULTS.md)
- [Result attribution](docs/RESULT_ATTRIBUTION.md)
- [PR #119](https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/119)
