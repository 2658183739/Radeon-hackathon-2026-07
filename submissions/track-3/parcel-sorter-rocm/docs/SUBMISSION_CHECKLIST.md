# Submission Checklist / 提交检查清单

| Requirement | Status | Evidence or next action |
| --- | --- | --- |
| Public fork of the official repository | ready | <https://github.com/2658183739/Radeon-hackathon-2026-07> |
| Official pull request | ready | [PR #119](https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/119), base `main` |
| PR title follows guide | action required | Rename to `[Physical AI] 2658183739 - Parcel Sorter ROCm` |
| Bilingual README with five required sections | ready | root `README.md` |
| MIT or Apache-2.0 license | ready | `LICENSE`, MIT |
| Install and run instructions | ready | README section 5; `Dockerfile.rocm` |
| Agent model, API and architecture | ready | `docs/AGENT_MODEL_ARCHITECTURE.md` |
| Public Bilibili/YouTube video | action required | Upload the 59-second MP4 and replace the placeholder in `docs/PR_DESCRIPTION_READY.md` |
| Video under 3 minutes, 1080p, bilingual text | ready | 59.0 s, 1920x1080 H.264; `videos/video_metadata_decode.json` |
| Five-second hook and final repository card | ready | `docs/assets/hook_5_seconds.gif`; final six seconds of MP4 |
| Training evidence | ready | real 2,800-step log and curve in `evidence/training/` and `docs/assets/` |
| Dataset audit | ready | 7 episodes / 4,557 frames; `evidence/training/pash-primitive-dataset-v2-audit.json` |
| Ablation | ready | `docs/ABLATION_RESULTS.md` |
| Sim-to-Real | not supplied | optional; no claim |
| Real-robot footage | not supplied | optional; no claim |
| TensorBoard screenshot | not supplied | optional; do not fabricate |
| Public dataset URL | not supplied | optional; local audit and generation path are included |
| No secrets | ready | focused credential-pattern scan passed |
| No file over 100 MB | ready | file-size audit passed |
| PR confirmation screenshot | ready | `docs/assets/pr-119-confirmation.png` |
| AMD developer registration | user verification required | Confirm registration for every team member |

The final user actions and code-review result are in
[`FINAL_SUBMISSION_AUDIT.md`](FINAL_SUBMISSION_AUDIT.md).
