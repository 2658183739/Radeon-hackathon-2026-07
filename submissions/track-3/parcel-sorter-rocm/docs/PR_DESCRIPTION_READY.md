# Recommended PR Title

`[Physical AI] 2658183739 - Parcel Sorter ROCm`

# PR Description

## Parcel Sorter ROCm

Parcel Sorter ROCm runs a Genesis parcel pick-and-place task on one AMD Radeon
GPU through ROCm. The repository contains a deterministic task agent,
SmolVLA/PI0.5 research routes, and an agent-guided VLA safety harness behind a
common action interface.

### What is included

- complete source, pinned ROCm container and reproduction commands;
- bilingual README with the five required sections;
- 59-second 1080p demonstration with overview and wrist views;
- a 2,800-step SmolVLA ROCm training log and curve;
- an audited 7-episode / 4,557-frame dataset manifest;
- offline action-envelope ablation and explicit result attribution;
- GPT-5.6 Luna development-agent, model, API and architecture documentation.

### Results

| Route | Result | Meaning |
| --- | ---: | --- |
| Scripted task agent | 8/10 | Source of the successful demo clips; uses privileged simulator state |
| Raw VLA offline envelope | 0/42 | Failed frozen action-validity checks |
| Safety-clipped VLA / Harness-Lite | 42/42 | Offline validity only |
| Strict pure VLA closed loop | 0/3 | Did not complete the task |

The hybrid architecture is agent + VLA, but the successful video uses the
scripted route. No real-robot or Sim-to-Real result is claimed.

### Links

- Video: `REPLACE_WITH_PUBLIC_BILIBILI_OR_YOUTUBE_URL`
- Repository demo: <https://github.com/2658183739/Radeon-hackathon-2026-07/blob/track3-parcel-sorter-final/submissions/track-3/parcel-sorter-rocm/videos/genesis_panda_8_success_reference_demo.mp4>
- Team member: `2658183739`
