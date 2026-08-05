# Optional Evidence Index / 可选加分证据索引

This index deliberately distinguishes verified artifacts from material that
still needs an external publishing account. It does not turn an offline gate
or an expert rollout into a pure-VLA score.

本索引明确区分已经验证的材料和仍需要外部发布账号的材料，不会把离线门或专家
轨迹伪装成纯 VLA 成绩。

| Item | Evidence prepared | Submission note |
| --- | --- | --- |
| Training log / 训练日志 | `evidence/pi05_vla/mvp_competition_v20_mode_only_20260805/calibration.log` plus `PI05_HEAD_CALIBRATION_CONTRACT.json` | Include the log and hashes in the delivery archive. |
| TensorBoard / TensorBoard 截图 | Calibration is a deterministic head-calibration run; no TensorBoard claim is made unless a real event file exists. | Use the supplied loss history JSON or add a screenshot only after checking the event file. |
| Ablation / 消融 | V18 baseline, V19c all-head calibration (offline stop), and V20 mode-only calibration are bound by separate preregistrations. | Report the negative V19c result; do not cherry-pick it away. |
| Sim-to-real / Sim-to-Real | The repository contains the Genesis-to-Radeon execution harness and runtime evidence. | Do not claim physical-hardware transfer without a matching hardware log. |
| Dataset / 开源数据集 | The admitted two-episode LeRobot dataset and manifests are archived locally with hashes. | Publish only the scrubbed dataset if licensing and privacy checks pass. |
| Technical blog / 技术博客 | `PROJECT_DESCRIPTION_EN_CN.md` and the technical report are ready as source material. | Replace the placeholder URL in `submission_links.json` after publishing. |
| Demo video / 演示视频 | Three strict pure-VLA MP4s and a <=3 minute montage are generated only after the V20 closed-loop gate passes. | Every MP4 is decoded and fingerprinted before packaging. |
