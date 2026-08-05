# Training Evidence

This document names local files used for the reported training and offline evidence. It does not replace the files or claim an external experiment tracker.

| Item | Local evidence | Recorded fact |
| --- | --- | --- |
| Runtime | `evidence/training/pash-primitive-smolvla-2800step-offline-ablation-v1.json` | Python 3.12.3; Genesis 1.2.3; LeRobot 0.6.1; torch 2.9.1+rocm7.2.1; ROCm 7.2.53211 |
| Dataset audit | `evidence/training/pash-primitive-dataset-v2-audit.json` | passed; 7 episodes; 4,557 frames; 43-D state; 20-D action |
| Training log | `evidence/training/pash-primitive-smolvla-rocm-2800step-v1.log` | local ROCm training log |
| Curve | `assets/pash-primitive-smolvla-2800step-training-curve-v1.png` | unmodified copy of the local evidence PNG |
| Offline ablation | `evidence/training/pash-primitive-smolvla-2800step-offline-ablation-v1.json` | 42 episode-stage samples; action-contract metrics only |

The observed policy modality is RGB with `observation.state` and `observation.images.overhead_rgb`; privileged state is excluded. Training configuration uses the local audited backbone specified by `UPSTREAM_LOCK.json`. Its public download URL is **pending**.

TensorBoard export: **pending**. No TensorBoard charts are claimed in this submission.
