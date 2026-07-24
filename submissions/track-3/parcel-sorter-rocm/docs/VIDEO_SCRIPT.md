# Demonstration Video Script (3-5 Minutes)

## 0:00-0:25 — Problem and architecture

- State the small-parcel sorting task and one-Radeon/ROCm constraint.
- Show the architecture: Genesis, RGB-D/state/contact, expert or ACT, safety
  supervisor, IK/PD/force control, physical outcome, evidence.

## 0:25-0:50 — Radeon environment

- Show `rocm-smi`, `torch.version.hip`, GPU name, VRAM, Genesis, and LeRobot.
- Run the preflight check.

## 0:50-1:40 — Closed-loop expert

- Show left and right destination episodes.
- Include one retry or safe abort and explain that failures remain in audit data.
- Show RGB-D, joint/pose state, contact force, and the final bin check.

## 1:40-2:25 — Dataset and ACT training

- Show LeRobotDataset features and the no-privileged-state input contract.
- Show the Radeon training command, AMP batch 32, checkpoints, and loss log.

## 2:25-3:10 — Learned closed loop

- Load the 4,000-step checkpoint and show model-driven Genesis execution.
- Report both 4,000 and 5,000 same-range results; explain task-based selection.

## 3:10-3:45 — GPU optimization

- Show the 1/16/64/128 environment benchmark and 46,582 env-steps/s result.
- Show FP32/AMP training comparison and inference mean/P95 latency.

## 3:45-4:20 — Failure analysis and improvement

- Show that 22/24 expert failures were force-safety aborts.
- Explain the phase-aware final approach, hard-example recollection, and RGB-D
  fusion roadmap.

## 4:20-4:40 — Reproduction and value

- Show the repository, pinned revisions, Dockerfile, tests, evidence, and
  reproduction command.
- Close with the intended warehouse, education, and personal research value.

Do not hide failed attempts or claim the current ACT baseline is converged.
