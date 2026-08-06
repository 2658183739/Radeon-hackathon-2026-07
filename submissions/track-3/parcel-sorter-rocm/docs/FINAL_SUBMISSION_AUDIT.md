# Final Submission Audit / 最终提交审查

Checked against the Feishu **作品提交指南** on 2026-08-06.

## Must Complete Before 23:59 / 截止前必须完成

| Action | Current state | What to do |
| --- | --- | --- |
| AMD AI Developer Program registration | Cannot be verified from the repository | Confirm that every team member has registered at <https://www.amd.com/zh-cn/developer.html>. |
| Push the final local commits | Local branch is ahead of the public branch | Push `track3-parcel-sorter-final` before the deadline, then reopen the public README and video links. |
| PR title format | Current PR title is `Track 3, 2658183739, Parcel Sorter ROCm` | Rename it to `[Physical AI] 2658183739 - Parcel Sorter ROCm`. |
| Public video platform | Local and repository MP4 are ready; Bilibili/YouTube is pending | Upload `videos/genesis_panda_8_success_reference_demo.mp4`, make it public, and add the URL to README and PR description. |
| Final external-link check | Pending after upload and push | Open the fork, PR, raw MP4 and Bilibili/YouTube URL in a signed-out browser. |

## Ready / 已完成

- Public fork and official PR #119 exist.
- README contains exactly the five required bilingual sections.
- MIT license, `requirements.txt`, `src/`, `configs/`, `data/`, `docs/` and
  `videos/` are present.
- README includes ROCm/License/Python badges and a five-second GIF.
- Demo is 59 seconds, 1920x1080 H.264, with burned-in Chinese and English text,
  an opening success hook, overview plus wrist views, and a final repository
  card.
- The video now labels the controller as a scripted agent and explicitly says
  it is not pure VLA.
- Training log, training curve, dataset audit and offline ablation are included.
- Agent, model, API and system architecture are documented.
- Focused secret scan found no credential-shaped value; no file exceeds 100 MB.
- PR confirmation screenshot is stored at `docs/assets/pr-119-confirmation.png`.

## Optional Additions / 可选加分项

| Item | Recommendation |
| --- | --- |
| TensorBoard screenshot | Do not fabricate one. The repository has a real training log and curve; add TensorBoard only if the original event file can be exported before the deadline. |
| Public dataset | Optional. Seven independent episodes are too small to advertise as a general-purpose dataset; publish only with the existing limitations and hashes. |
| Sim-to-Real | Not required by the guide. Keep the honest simulation-only boundary. |
| Technical blog or post | Useful only after the repository and video URLs are final. A short post about why decreasing loss did not produce closed-loop success would be more credible than a generic project announcement. |

## Code Review Result / 代码审查结论

One release-blocking container issue was fixed: `activate_radeon_env.sh` now
recognizes the ROCm Python environment already active in the base image through
`sys.prefix`. Previously, the image `CMD` could exit before preflight because it
looked only for the project `.venv` and `/workspace/rdna`.

The remaining broad-suite failures documented in `docs/TEST_REPORT.md` are
unchanged baseline hash/dependency issues in the non-ROCm Windows environment.
They should not be described as a fully green suite.
