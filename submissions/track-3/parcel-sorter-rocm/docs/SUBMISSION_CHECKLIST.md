# Submission Checklist / 提交检查清单

| Requirement / 要求 | Status / 状态 | Evidence or next action / 证据或下一步 |
| --- | --- | --- |
| Public official fork / 官方仓库 Public Fork | Ready / 已就绪 | <https://github.com/2658183739/Radeon-hackathon-2026-07> |
| Official pull request / 官方 PR | Ready / 已就绪 | [PR #119](https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/119), base `main` |
| PR title follows guide / PR 标题符合规范 | Action required / 待操作 | Rename to / 改为 `[Physical AI] 2658183739 - Parcel Sorter ROCm` |
| Bilingual README with five required sections / 双语 README 含五个强制章节 | Ready / 已就绪 | root `README.md` |
| MIT or Apache-2.0 license / MIT 或 Apache-2.0 许可证 | Ready / 已就绪 | `LICENSE`, MIT |
| Install and run / 安装与运行 | Ready / 已就绪 | README section 5; `Dockerfile.rocm` |
| Agent model, API and architecture / Agent 模型、API 与架构 | Ready / 已就绪 | `docs/AGENT_MODEL_ARCHITECTURE.md` |
| Public Bilibili/YouTube video / 公开视频 | Action required / 待操作 | Upload the 59 s MP4 and replace the placeholder / 上传 59 秒成片并回填链接 |
| Video under 3 minutes, 1080p, bilingual / 视频小于 3 分钟、1080p、中英字幕 | Ready / 已就绪 | 59.0 s, 1920x1080 H.264; `videos/video_metadata_decode.json` |
| Overview and wrist views / 全景与腕部视角 | Ready / 已就绪 | episodes 0 and 7 show both views / 回合 0 与 7 含双视角 |
| Five-second hook and final repository card / 5 秒钩子与结尾仓库卡 | Ready / 已就绪 | `docs/assets/hook_5_seconds.gif`; final six seconds / 成片最后 6 秒 |
| Training log and screenshot-grade evidence / 训练日志与截图级证据 | Ready / 已就绪 | 2,800-step log, curve and `training_evidence_board_1920x1080.png` |
| TensorBoard screenshot / TensorBoard 截图 | Not claimed / 不宣称 | Log-derived board is real; TensorBoard was not used / 使用真实日志证据板，不伪造 TensorBoard |
| Dataset audit / 数据集审计 | Ready / 已就绪 | 7 episodes / 4,557 frames; audit + manifest |
| Public dataset URL / 公开数据集地址 | Blocked on payload recovery / 待恢复数据载荷 | Remote Parquet/MP4/meta must be copied and hash-verified first / 先复制远端数据并核验哈希 |
| Expanded ablation / 完整消融 | Ready / 已就绪 | `docs/ABLATION_RESULTS.md` and `docs/assets/ablation_comparison.png` |
| Sim-to-Real protocol / Sim-to-Real 协议 | Ready / 已就绪 | `docs/SIM_TO_REAL_STATUS.md` |
| Sim-to-Real result / Sim-to-Real 结果 | Not performed / 未执行 | No real-robot claim / 不宣称真机迁移 |
| Real-robot footage / 真机视频 | Not supplied / 未提供 | Optional; no claim / 可选，不作声明 |
| Technical blog and social copy / 技术博客与社交文案 | Ready / 已就绪 | `docs/TECHNICAL_BLOG_AND_SOCIAL_EN_CN.md` |
| Markdown review manifest / Markdown 审阅清单 | Ready / 已就绪 | complete generated inventory in `docs/MD_REVIEW_INDEX_EN_CN.md` / 索引覆盖全部 Markdown 文件 |
| Code review / 代码审查 | Ready / 已就绪 | link, JSON, secrets, size, image, video and diff checks / 链接、JSON、敏感信息、大小、图片、视频与 diff 检查 |
| No secrets / 无敏感信息 | Ready / 已就绪 | focused credential-pattern scan / 凭证模式扫描 |
| No file over 100 MB / 无超过 100 MB 文件 | Ready / 已就绪 | file-size audit / 文件大小审计 |
| PR confirmation screenshot / PR 确认截图 | Ready / 已就绪 | `docs/assets/pr-119-confirmation.png` |
| AMD Developer Program registration / AMD Developer Program 注册 | User verification required / 需用户确认 | Confirm registration for every member / 确认每位成员已注册 |

Final user actions and the latest audit are in [`FINAL_SUBMISSION_AUDIT.md`](FINAL_SUBMISSION_AUDIT.md). / 最终人工操作与最新审计见 [`FINAL_SUBMISSION_AUDIT.md`](FINAL_SUBMISSION_AUDIT.md)。
