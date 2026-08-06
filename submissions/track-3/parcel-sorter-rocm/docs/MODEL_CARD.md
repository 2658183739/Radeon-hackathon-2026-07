# Model Card / 模型卡

## Current Candidate / 当前候选

**English.** The current candidate is a local SmolVLA checkpoint trained for 2,800 updates on the audited 7-episode / 4,557-frame primitive dataset. The checkpoint and complete dataset payload remain on the remote training workspace and are not distributed by this repository.

**中文。** 当前候选是本地 SmolVLA checkpoint，在经审计的 7 episode / 4,557 帧 primitive 数据集上训练 2,800 step。checkpoint 与完整数据载荷仍位于远程训练工作区，本仓库不直接分发。

| Field / 字段 | Recorded value / 记录值 |
| --- | --- |
| Policy / 策略 | SmolVLA through LeRobot 0.6.1 / 通过 LeRobot 0.6.1 运行 |
| Inputs / 输入 | overhead RGB + 43-D non-privileged state + task text / 俯视 RGB + 43 维非特权状态 + 任务文本 |
| Output / 输出 | 20-D action including `primitive_progress` / 含 `primitive_progress` 的 20 维动作 |
| Parameters / 参数 | 450,061,536 total; 99,896,352 learnable / 总参数与可训练参数 |
| Training / 训练 | 2,800 updates; batch 8; AMP; one Radeon GPU / 2,800 step；batch 8；AMP；单张 Radeon |
| Runtime / 环境 | ROCm 7.2.53211; PyTorch 2.9.1 ROCm / ROCm 7.2.53211；PyTorch 2.9.1 ROCm |
| Loss / 损失 | 2.164 first; 0.056 final; first-100 mean 1.57606; last-100 mean 0.07332 |
| Efficiency / 效率 | 442 s; 6.33 steps/s; 2.32 GB reported peak memory / 442 秒；6.33 step/s；日志峰值 2.32 GB |

## Evaluation / 评估

| Evaluation / 评估 | Result / 结果 | Boundary / 边界 |
| --- | ---: | --- |
| Raw VLA action envelope / 原始 VLA 动作包络 | 0/42 | Offline correlated episode-stage samples / 离线相关样本 |
| Safety-clipped VLA / 安全裁剪 VLA | 42/42 | Offline action validity only / 仅离线动作合法性 |
| Harness-Lite | 42/42 | Offline action validity only; no expert fallback / 仅离线动作合法性；无专家回退 |
| Strict pure-VLA closed loop / 严格纯 VLA 闭环 | **0/3** | Not passed / 未通过 |

Loss reduction and offline MAE do not establish task completion. The successful 8/10 video was produced by `ScriptedPickPlaceExpert + ClosedLoopSupervisor`, not this checkpoint.

Loss 下降与离线 MAE 不能证明任务完成。8/10 成功视频由 `ScriptedPickPlaceExpert + ClosedLoopSupervisor` 产生，不是本 checkpoint 的成功结果。

## Evidence / 证据

- [Training summary JSON / 训练摘要](../evidence/training/pash-primitive-smolvla-rocm-2800step-v1.json)
- [Full training log / 完整训练日志](../evidence/training/pash-primitive-smolvla-rocm-2800step-v1.log)
- [Dataset audit / 数据审计](../evidence/training/pash-primitive-dataset-v2-audit.json)
- [Offline ablation / 离线消融](../evidence/training/pash-primitive-smolvla-2800step-offline-ablation-v1.json)
- [Training evidence report / 训练证据报告](TRAINING_EVIDENCE.md)

## Intended Use and Limits / 适用范围与限制

The checkpoint is a simulation research candidate for bounded parcel-manipulation experiments. It is not a real-robot controller, safety-certified system, general-purpose model, successful pure-VLA policy, or validated Sim-to-Real result. Seven episodes and one recorded training run (`n=1`) are insufficient for a generalization claim.

该 checkpoint 仅用于受限包裹操作的仿真研究，不是真机控制器、安全认证系统、通用模型、成功纯 VLA 策略或已验证的 Sim-to-Real 结果。7 个回合和一次训练（`n=1`）不足以支撑泛化结论。

## Legacy ACT Baseline / 历史 ACT 基线

The 52M ACT baseline trained on 96 episodes / 11,753 frames is separate historical evidence with a 20-D state and 8-D action contract. It did not train this SmolVLA candidate. Do not combine its counts, weights or metrics with the current model.

使用 96 episode / 11,753 帧训练的 52M ACT baseline 属于独立历史证据，状态为 20 维、动作为 8 维；它没有训练当前 SmolVLA 候选。不得把它的样本数、权重或指标与当前模型合并。

## Distribution / 发布

No uploadable model package is present locally. Before release, recover the exact checkpoint, verify the recorded model/config hashes, pin the code and dataset revisions, and review pretrained-backbone license terms.

本地没有可上传的模型包。发布前必须恢复精确 checkpoint，核验模型与配置哈希，锁定代码和数据版本，并审阅预训练骨干模型许可证。
