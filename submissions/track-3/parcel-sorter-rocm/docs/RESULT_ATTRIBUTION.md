# Result Attribution / 结果归因

| Result | Controller | How it is obtained | Claim |
| --- | --- | --- | --- |
| 8/10 successful trajectories | Deterministic scripted controller (`ScriptedPickPlaceExpert` + `ClosedLoopSupervisor`) | Runs 10 fixed-seed Genesis episodes using privileged simulator state. An episode is successful only when the supervisor reaches `Stage.COMPLETE`; only records with `_result.json` `success=true` enter the demo. | Scripted-controller demonstration provenance only. Not VLA or LLM-agent success. |
| 0/3 | Strict pure VLA | Learned policy supplies the declared task actions in closed loop without expert completion. | Not passed. |
| 0/42, 42/42, 42/42 | Raw VLA, safety-clipped VLA, Harness-Lite offline action-envelope checks | Replays 42 action-contract samples through offline validity gates. | Offline ablation only. Not task-success evidence. |

The demo video contains the eight successful scripted-controller episodes. The
controller reads parcel and robot poses from Genesis and uses a finite-state
task supervisor for approach, grasp, lift, transport, and release. The video is
not evidence that the fine-tuned VLA completed the task.

| 结果 | 控制器 | 结果如何得到 | 可主张内容 |
| --- | --- | --- | --- |
| 8/10 条成功轨迹 | 确定性脚本控制器（`ScriptedPickPlaceExpert` + `ClosedLoopSupervisor`） | 使用仿真特权状态运行 10 个固定种子的 Genesis 回合。只有监督器到达 `Stage.COMPLETE` 且 `_result.json` 为 `success=true` 的回合才进入演示视频。 | 仅证明脚本控制器的示范来源，不是 VLA 或大模型 Agent 成功率。 |
| 0/3 | 严格纯 VLA | 学习策略在没有专家补全的情况下提供闭环任务动作。 | 未通过。 |
| 0/42、42/42、42/42 | Raw VLA、Safety-clipped VLA、Harness-Lite 离线动作包络检查 | 42 个动作合约样本的离线有效性门测试。 | 仅为离线消融，不是任务成功率。 |

演示视频只包含 8 个成功的脚本控制器回合。该控制器从 Genesis
读取包裹和机器人位姿，并用有限状态任务监督器完成接近、抓取、抬升、搬运和
释放；视频不证明微调后的 VLA 完成了任务。
