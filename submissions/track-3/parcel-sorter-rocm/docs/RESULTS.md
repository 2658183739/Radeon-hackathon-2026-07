# Results / 结果

## What produced the video / 视频由谁产生

`ScriptedPickPlaceExpert + ClosedLoopSupervisor` completed 8 of 10 fixed-seed
Genesis episodes. It reads privileged simulator state and reaches
`Stage.COMPLETE` before a clip is selected. The 45.6-second video concatenates
those eight overview streams in episode order without trimming or re-encoding.

`ScriptedPickPlaceExpert + ClosedLoopSupervisor` 在 10 个固定种子 Genesis episode 中完成 8 个。它读取仿真特权状态，只有到达 `Stage.COMPLETE` 的记录才会入选。45.6 秒视频按 episode 顺序直接拼接这 8 段 overview，没有裁剪或重新编码。

## Learned-policy measurements / 学习策略测量

| Controller and test / 控制器与测试 | Result / 结果 | Interpretation / 含义 |
| --- | ---: | --- |
| Raw VLA, offline action envelope / 原始 VLA 离线动作包络 | 0/42 | Raw actions exceed at least one execution limit / 至少越过一项执行边界 |
| Safety-clipped VLA, same offline test / 安全裁剪 VLA | 42/42 | Offline action validity only / 仅离线动作有效性 |
| Harness-Lite, same offline test | 42/42 | Offline action validity only / 仅离线动作有效性 |
| Strict pure VLA, closed loop / 严格纯 VLA 闭环 | 0/3 | Did not complete the task / 未完成任务 |

The offline rows are hybrid Agent+VLA measurements. They are not task-success
rates, and they are not the controller used in the video.

离线结果属于混合 Agent+VLA 测量，不是任务成功率，也不是视频使用的控制器。

## Training record / 训练记录

![SmolVLA training loss](assets/training_loss.png)

This is one 2,800-update SmolVLA run on a single Radeon GPU. The loss recorded
in the log falls from 2.164 to 0.056; the first-100 and last-100 means are
1.57606 and 0.07332. Mean throughput was 6.33 updates/s and reported peak GPU
memory was 2.32 GB. Because this is one run (`n=1`), the figure does not show
an uncertainty band.

这是单张 Radeon GPU 上一次完整的 2,800 update SmolVLA 训练。日志中的 loss
从 2.164 降至 0.056，前 100 次和后 100 次均值分别为 1.57606 与 0.07332；
平均速度为 6.33 updates/s，记录的显存峰值为 2.32 GB。该图只有一次运行
（`n=1`），因此不画误差带。

## Offline ablation / 离线消融

![Offline action-envelope ablation](assets/offline_ablation.png)

The left panel reports the same execution-envelope check as the table above.
The right panel adds the mean absolute component discrepancy against the
recorded reference action over the 19 control outputs; the 20th auxiliary
progress output is evaluated separately. The diagnostic averages heterogeneous
action fields and has no single physical unit. Harness-Lite has the lowest
value among the learned-action variants on these 42 samples.

左图对应上表的执行包络检查；右图比较前 19 个控制输出相对记录参考动作的分量平均
差异，第 20 个辅助阶段进度输出单独评估。该诊断量混合了不同类型的动作字段，没有
统一物理单位。Harness-Lite 在这 42 个样本的学习动作方案中数值最低。

Sources: `docs/RESULT_ATTRIBUTION.md`,
`evidence/training/pash-primitive-smolvla-2800step-offline-ablation-v1.json`,
`evidence/training/pash-primitive-smolvla-rocm-2800step-v1.log`, and
`videos/source_manifest.json`.
