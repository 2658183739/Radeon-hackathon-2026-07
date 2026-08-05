# Submission Checklist

| Item | Status | Evidence or note |
| --- | --- | --- |
| AMD Radeon ROCm execution environment | recorded | ROCm 7.2.1; Genesis 1.2.3; `scripts/preflight_radeon.sh` |
| Install and run instructions | recorded | root `README.md` |
| Scripted expert-agent development result | recorded | 8/10; privileged simulator state; isolated from pure VLA |
| Strict pure-VLA evaluation | not passed | 0/3; `submission_materials/RESULTS.json` |
| Dataset audit | recorded | 7 episodes / 4,557 frames |
| Offline ablation | recorded | 42 action-contract samples; `docs/ABLATION_RESULTS.md` |
| Local training log and curve | recorded | `evidence/training/`; `docs/assets/` |
| TensorBoard export | pending | not supplied |
| Sim-to-Real experiment | pending | no claim |
| Real-robot footage | pending | no claim |
| Public dataset URL | pending | not supplied |
| Public demo-video URL | recorded | [GitHub blob](https://github.com/2658183739/Radeon-hackathon-2026-07/blob/track3-parcel-sorter-final/submissions/track-3/parcel-sorter-rocm/videos/genesis_panda_8_success_reference_demo.mp4); [raw MP4](https://raw.githubusercontent.com/2658183739/Radeon-hackathon-2026-07/track3-parcel-sorter-rocm/videos/genesis_panda_8_success_reference_demo.mp4); deterministic scripted expert-agent simulation only |
| Pull-request URL | open | [PR #119](https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/119), base `main`; confirmation: `docs/assets/pr-119-confirmation.png` |

Before packaging, rerun the Radeon preflight, verify the intended local artifact hashes, and confirm that no documentation converts reference or offline evidence into a pure-VLA success claim. The linked video is not real-robot footage and does not change the strict pure-VLA result of 0/3.
