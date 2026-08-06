# Sim-to-Real Status and Protocol / Sim-to-Real 状态与实验协议

## Current Status / 当前状态

**Not performed; no Sim-to-Real result is claimed. / 尚未执行，不宣称已有 Sim-to-Real 结果。**

All reported task results are from Genesis simulation. The scripted-agent result is **8/10** and uses privileged simulator state. Strict pure VLA is **0/3** in simulation. The 42-sample ablation is an offline action-contract measurement. None of these is real-robot evidence.

当前所有任务结果均来自 Genesis 仿真：脚本 Agent 为 **8/10**，并读取仿真特权状态；严格纯 VLA 在仿真中为 **0/3**；42 样本消融是离线动作合约测量。三者都不属于真机证据。

The repository has no real-robot deployment log, hardware calibration record, safety approval, synchronized real-camera capture, or measured transfer experiment. It must not be described as ARX-X5 validation, real-robot footage, or successful transfer.

仓库中没有真机部署日志、硬件标定记录、安全审批、同步真机相机录像或迁移实验测量，因此不能表述为 ARX-X5 验证、真机视频或成功迁移。

## Pre-Registered Validation Protocol / 预注册验证协议

This section is an executable plan for future measurement, not a result. Every field marked `[pending]` must remain pending until raw real-robot evidence is archived.

本节是后续可执行实验计划，不是已有结果。所有 `[待测]` 字段必须在真机原始证据归档后才能填写。

### Experimental Units / 实验单位

- Independent randomized pick-and-place episodes are the replicates. / 以独立随机抓放回合作为重复单位。
- Use the same frozen object-set, start-pose blocks, target regions and success tolerance in simulation and reality. / 仿真与真机使用同一冻结物体集合、起始位姿分块、目标区域和成功容差。
- Randomize route order within each block and alternate simulator/robot measurement order where practical. / 在每个分块内随机策略顺序，并在可行时交替仿真与真机测量顺序。
- Do not replace failed trials or allow expert completion. / 不替换失败回合，不允许专家补全。

### Required Calibration and Safety / 必需标定与安全条件

| Requirement / 条件 | Required record / 记录 | Status / 状态 |
| --- | --- | --- |
| Robot and gripper identity / 机器人与夹具型号 | serial, firmware, payload / 序列号、固件、负载 | `[pending / 待测]` |
| Camera calibration / 相机标定 | intrinsics, extrinsics, timestamp / 内参、外参、时间戳 | `[pending / 待测]` |
| Workspace alignment / 工作空间对齐 | base-to-camera transform and residual / 基座到相机变换及残差 | `[pending / 待测]` |
| Control matching / 控制匹配 | action rate, limits, latency / 动作频率、边界、延迟 | `[pending / 待测]` |
| Safety review / 安全审查 | speed, force, workspace, E-stop test / 速度、力、空间、急停测试 | `[pending / 待测]` |

### Frozen Outcomes / 冻结指标

1. Complete-task success under the same terminal rule. / 同一终止规则下的完整任务成功率。
2. Final placement error in millimetres. / 最终放置误差（毫米）。
3. Human intervention rate and expert-fallback count. / 人工干预率与专家回退次数。
4. Force/torque aborts and emergency stops. / 力/力矩中止与急停次数。
5. End-to-end action latency, mean and p95. / 端到端动作延迟均值与 P95。
6. Transfer gap: real success minus matched simulation success. / 迁移差距：真机成功率减去匹配仿真成功率。

### Result Table / 结果表

| Route / 路径 | Simulation success / 仿真成功 | Real success / 真机成功 | Placement error / 放置误差 | Intervention / 干预 | Transfer gap / 迁移差距 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Scripted supervisor / 脚本监督器 | `[pending matched run / 待匹配实验]` | `[pending / 待测]` | `[pending / 待测]` | `[pending / 待测]` | `[pending / 待测]` |
| Hybrid Agent+VLA / 混合 Agent+VLA | `[pending matched run / 待匹配实验]` | `[pending / 待测]` | `[pending / 待测]` | `[pending / 待测]` | `[pending / 待测]` |
| Pure VLA / 纯 VLA | `[pending matched run / 待匹配实验]` | `[pending / 待测]` | `[pending / 待测]` | `[pending / 待测]` | `[pending / 待测]` |

## Evidence Needed Before Claiming Transfer / 宣称迁移前必须具备的证据

- Immutable episode manifest with seeds, condition assignments and failures. / 不可变回合清单，包含随机种子、条件分配和失败记录。
- Synchronized overview and wrist-camera video for every trial. / 每次试验的同步全景与腕部视频。
- Robot state, action, force, timing and safety-event logs. / 机器人状态、动作、力、时序和安全事件日志。
- Calibration files, code commit, model/dataset hashes and evaluation script. / 标定文件、代码提交、模型/数据哈希和评估脚本。
- A report that includes all attempted episodes, not only successful clips. / 报告必须包含全部尝试回合，不能只保留成功片段。

Until these records exist, the correct bonus-item wording is: **“Sim-to-Real protocol prepared; real-robot measurement pending.”** / 在这些记录齐全之前，加分项的正确表述只能是：**“已准备 Sim-to-Real 协议，真机测量待完成。”**
