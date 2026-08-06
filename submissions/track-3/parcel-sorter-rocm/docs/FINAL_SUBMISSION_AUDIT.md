# Final Submission Audit / 最终提交审计

## Status / 状态

**English.** This audit is a repository review entry, not proof of external publication or registration. The final reviewer must recheck every external URL, account state, and deadline requirement.

**中文。** 本审计是仓库审阅入口，不是外部发布或注册的证明。最终提交者必须重新检查全部外部链接、账户状态和截止要求。

## Verified In Repository / 仓库内已核对

| English | 中文 | Evidence boundary / 证据边界 |
| --- | --- | --- |
| README has five bilingual submission sections and install instructions. | README 包含五个双语提交章节和安装说明。 | Documentation only. |
| The demo is a 59-second 1920x1080 H.264 Genesis simulation artifact. | 演示为 59 秒、1920x1080 H.264 的 Genesis 仿真工件。 | Not real-robot footage. |
| `ScriptedPickPlaceExpert + ClosedLoopSupervisor` produced the 8/10 development-screen demo clips. | `ScriptedPickPlaceExpert + ClosedLoopSupervisor` 产生 8/10 开发筛选视频片段。 | Deterministic expert/reference only. |
| Strict pure VLA is 0/3. | 严格纯 VLA 为 0/3。 | Not passed; never combine it with expert or hybrid results. |
| The audited primitive dataset has 7 independent episodes and 4,557 frames. | 经审计的 primitive 数据集有 7 个独立 episode、4,557 帧。 | Dataset/training scope, not a 96-episode claim. |
| GPT-5.6 Luna is documented as development/orchestration only. | GPT-5.6 Luna 被记录为仅用于研发/编排。 | Not a robot policy or video controller. |

## Bonus-Item Status / 加分项状态

| Item / 加分项 | Status / 状态 | Evidence / 证据 |
| --- | --- | --- |
| Training log and visual / 训练日志与图片 | Ready / 已就绪 | 2,800-step raw log, curve, 1920x1080 evidence board; single run `n=1` / 原始日志、曲线与证据板；单次运行 `n=1` |
| Expanded ablation / 扩展消融 | Ready / 已就绪 | 42-sample raw, clipped, Harness-Lite and expert comparison with latency and safety counts / 含误差、延迟与安全计数 |
| Dataset release package / 数据集发布包 | Pending payload recovery / 待恢复数据 | Current checkout lacks Parquet, MP4 and metadata; do not upload the unrelated 9-episode set / 当前缺二进制载荷，不得上传无关 9 回合集 |
| Sim-to-Real / 仿真到真机 | Protocol ready; result not performed / 协议已就绪，结果未执行 | Randomized paired protocol and pending result table; no real-robot claim / 随机配对协议与待测结果表，不宣称真机 |
| Technical communication / 技术传播 | Ready to publish / 文案已就绪 | Bilingual blog and social copy / 中英博客与社交文案 |
| Code review / 代码审查 | Ready / 已就绪 | Local links, JSON, secrets, file sizes, figures, video metadata and diff checks / 本地链接、JSON、敏感信息、文件大小、图片、视频元数据与 diff 检查 |

## External Checks Before Submission / 提交前外部检查

- **English:** Confirm AMD program registration, repository visibility, PR state, public-video availability, and any required upload fields in a signed-out browser. Do not mark an unverified external item as complete.
- **中文：** 在退出登录的浏览器中确认 AMD 项目注册、仓库可见性、PR 状态、公开视频可用性和必填上传字段。未核验的外部项目不得标为完成。

## Review Risks / 审阅风险

- **English:** Historical documents contain additional development results, including 96/100 frozen-holdout material. They are historical/internal evidence and must not replace the submission dataset statement of 7 episodes / 4,557 frames or the strict pure-VLA result of 0/3.
- **中文：** 历史文档包含其他开发结果，包括 96/100 的 frozen-holdout 材料。它们属于历史/内部证据，不得替代本提交的 7 episode / 4,557 帧数据集表述或严格纯 VLA 0/3 结果。

- **English:** Hybrid VLA offline envelope results (0/42 raw, 42/42 bounded variants) are not closed-loop task-success rates.
- **中文：** 混合 VLA 的离线动作包络结果（原始 0/42、受限版本 42/42）不是闭环任务成功率。

See [the Markdown review index](MD_REVIEW_INDEX_EN_CN.md) for the document map and [result attribution](RESULT_ATTRIBUTION.md) for controller-specific boundaries.
