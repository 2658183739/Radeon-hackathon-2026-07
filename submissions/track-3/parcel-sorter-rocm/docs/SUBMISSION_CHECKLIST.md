# Submission Checklist

| Item | Status | Evidence or note |
| --- | --- | --- |
| AMD Radeon ROCm execution environment | recorded | ROCm 7.2.1; Genesis 1.2.3; `scripts/preflight_radeon.sh` |
| Install and run instructions | recorded | root `README.md` |
| Expert/reference development result | recorded | 8/10; isolated from pure VLA |
| Strict pure-VLA evaluation | not passed | 0/3; `submission_materials/RESULTS.json` |
| Dataset audit | recorded | 7 episodes / 4,557 frames |
| Offline ablation | recorded | 42 action-contract samples; `docs/ABLATION_RESULTS.md` |
| Local training log and curve | recorded | `evidence/training/`; `docs/assets/` |
| TensorBoard export | pending | not supplied |
| Sim-to-Real experiment | pending | no claim |
| Real-robot footage | pending | no claim |
| Public dataset URL | pending | not supplied |
| Public demo-video URL | pending | not supplied |
| Pull-request URL | pending | not supplied |

Before packaging, rerun the Radeon preflight, verify the intended local artifact hashes, and confirm that no documentation converts reference or offline evidence into a pure-VLA success claim.
