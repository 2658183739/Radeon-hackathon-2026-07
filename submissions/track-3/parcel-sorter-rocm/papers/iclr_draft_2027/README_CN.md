# ICLR 论文草稿说明

`root.tex` 是双盲、会场中立的 ICLR 风格研究草稿。ICLR 2027 Author Guidelines 已于 2026-07-29 可访问，要求投稿正文不超过 9 页，讨论修订和终稿不超过 10 页，并要求单列 AI Use Statement、建议单列 Reproducibility Statement。指南链接的 `iclr2027.zip` 当日仍返回 404，官方 `ICLR/Master-Template` 仓库也尚无 2027 资产，因此当前继续使用标准 `article` 排版；正式归档可下载后只替换导言区和参考文献样式，不改变证据内容。

官方来源：

- `https://iclr.cc/Conferences/2027/AuthorGuidelines`
- `https://iclr.cc/Conferences/2027/AIPolicyForAuthors`
- `https://github.com/ICLR/Master-Template/raw/master/iclr2027.zip`（2026-07-29 检查时为 404）

草稿只写入已经有机器证据的结果：本地 PI0.5 LIBERO 400 回合为 96.25%，Radeon eager 长稳通过，max-autotune 因成功与能效门失败而被拒绝，B3 增量 SE(3) 因动作保真回退未晋级；action-step 开发筛选选择了 8-step（40/40），但完整 400+400 开发配对和一次性确认尚未完成。LIBERO 最终候选、B3-SW、快递冻结闭环和验证式恢复仍标为 `TBD`。

摘要和结论应最后完成。任何开发集结果、专家控制结果、离线动作误差或重复测量都不得写成冻结纯 VLA 成功率。方法总览图已作为 Figure 1 加入；最终版本还需加入评测流程图和由原始 JSON 生成的结果图，图中不得填入预测分数。
