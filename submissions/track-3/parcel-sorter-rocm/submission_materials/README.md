# Submission Materials / 提交材料

This folder is the small reviewer hand-off: a short bilingual description,
result summary, and media notes. Start with the repository `README.md` for the
working command.

本目录用于评审交接：包含简短双语说明、结果摘要和媒体说明。可运行命令见仓库根目录 `README.md`。

The public demo is scripted simulation: `ScriptedPickPlaceExpert +
ClosedLoopSupervisor` produced 8 successful episodes from a 10-episode screen.
Hybrid Agent+VLA has only offline 42/42 bounded-action evidence. Strict pure
VLA is 0/3. These are separate results.

公开演示是脚本仿真：`ScriptedPickPlaceExpert + ClosedLoopSupervisor` 在 10 个 episode 中成功 8 个。混合 Agent+VLA 只有离线 42/42 受限动作证据。严格纯 VLA 为 0/3。三者互不混同。

The original checkpoint training payload is not included. The local hand-off
ships a separate seven-episode successful-trajectory dataset with its own card
and hashes; it is not attributed to the submitted checkpoint.

原 checkpoint 训练 payload 不在本目录。本地交付另带一套 7 episode 成功轨迹
数据集及独立数据卡和哈希，不把它归因到提交的 checkpoint。
