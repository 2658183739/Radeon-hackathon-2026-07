# Submission Checklist / 提交检查清单

| Requirement / 要求 | Status / 状态 | Evidence or next action / 证据或下一步 |
| --- | --- | --- |
| Public official fork / 官方仓库 Public Fork | Ready / 已就绪 | <https://github.com/2658183739/Radeon-hackathon-2026-07> |
| Official pull request / 官方 PR | User action / 需操作 | Push the final commit, update PR #119, and save the confirmation screenshot / 推送最终提交、更新 PR #119 并保存确认截图 |
| PR title / PR 标题 | User action / 需操作 | `[Physical AI] 2658183739 - Parcel Sorter ROCm` |
| Bilingual README with five required sections / 双语 README 含五个强制章节 | Ready / 已就绪 | `README.md` |
| License and dependencies / 许可证与依赖 | Ready / 已就绪 | MIT `LICENSE`, `requirements.txt`, `pyproject.toml` |
| One-command demo / 一键演示 | Ready / 已就绪 | `Dockerfile.rocm` defaults to `scripts/run_demo.sh` |
| Agent/VLA architecture / Agent/VLA 架构 | Ready / 已就绪 | `docs/ARCHITECTURE.md` |
| Successful episode sequence / 成功回合原始拼接 | Ready / 已就绪 | 45.6 s, eight successful episodes, stream-copy only; `videos/source_manifest.json` |
| Public Bilibili/YouTube video / 公开视频 | User action / 需操作 | Edit or subtitle the supplied raw sequence, upload it, then add the public link / 自行剪辑或加字幕后上传并回填链接 |
| Training evidence / 训练证据 | Ready / 已就绪 | 2,800-update log plus 300 dpi PNG and vector PDF |
| Offline ablation / 离线消融 | Ready / 已就绪 | Raw VLA `0/42`; bounded variants `42/42`; not task success / 仅动作包络，不是任务成功率 |
| Strict pure-VLA result / 严格纯 VLA 结果 | Ready / 已就绪 | `0/3`, recorded separately from the scripted demo |
| Success-trajectory dataset / 成功轨迹数据集 | Ready / 已就绪 | 7 episodes, 6,454 frames, overview and wrist RGB-D, hashes verified |
| Public dataset URL / 公开数据集地址 | User action / 需操作 | Upload the supplied dataset release and add its public URL / 上传交付的数据集并回填公开地址 |
| Code review / 代码审查 | Ready / 已就绪 | Focused tests, JSON, links, secrets, file sizes, figures, video and hashes checked |
| No secrets / 无敏感信息 | Ready / 已就绪 | Credential-pattern scan passed |
| No repository file over 100 MB / 仓库无超过 100 MB 文件 | Ready / 已就绪 | File-size audit passed; do not commit the delivery ZIP |
| AMD Developer Program registration | User verification / 需确认 | Confirm registration before submission / 提交前确认注册状态 |

The final delivery keeps project code, the raw video, and the independent
dataset in separate directories. / 最终交付将代码、原始视频和独立数据集分目录保存。
