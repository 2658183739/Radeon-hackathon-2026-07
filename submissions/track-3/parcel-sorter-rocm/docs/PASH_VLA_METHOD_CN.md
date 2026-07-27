# PASH-VLA：负载感知安全 Harness VLA

## 方法定位

PASH-VLA（Payload-Aware Safety-Harness VLA）是本项目在 SmolVLA 之上的系统级方法，
不是重新训练一个更大的基础模型。它针对单张 AMD Radeon、移动双臂和快递搬运的约束，
把低频视觉语言策略、接触力短时记忆、确定性专家和失败驱动近线改进组合成一个可审计闭环。

```text
RGB + 43-D state + task text
        -> SmolVLA (3 Hz, 19-D proposal)
        -> force-memory temporal gate
        -> Harness-Lite residual candidates
        -> progress / deadline / contact / IK safety gates
        -> 240 Hz expert + tri-suction/V-cradle execution
        -> failure replay -> bridge curriculum -> Radeon retraining
        -> frozen holdout + Wilson promotion gate
```

模型仍然只能在安全契约内贡献动作残差；它不能直接发送力矩，也不能覆盖吸盘、托架、
放置确认或 35 N 中止逻辑。

## 三项可归因创新

### 1. 负载感知双臂协同末端执行器

左臂三杯实体柔顺吸盘承担密封，右臂实体 V 型托架承担连续支撑。只有两个吸盘密封、
托架接触保持 24 个物理步后才允许抬升；左右臂抬升和放置分别采用增量 IK。它把超出
平行夹爪长度范围的长箱搬运转化为可检查的负载分担问题。

### 2. Force-Memory Harness VLA

每次 VLA 推理保留最近 6 次接触力摘要。如果峰值超过 20 N，或窗口内上升超过 8 N，
系统按风险连续收紧 VLA 残差比例；低载荷稳定时不改变策略。它使用 2 N 上升死区避免
仿真噪声触发回退，并且永远保留 35 N 硬中止。实现入口是
`force_memory_scale_cap()`，通过 `--force-memory-harness` 显式开启，默认关闭以保护
已经冻结的 SmolVLA v2 基线。

### 3. 失败驱动近线自我改进

失败轨迹按失败阶段、载荷边界和安全事件排序，生成桥接课程；采集、训练、离线 Harness
包络检查、冻结评估和 checkpoint 晋级彼此隔离。候选只有在成功率、Wilson 非劣性、零力
越界、VLA 实际执行和单 Radeon/ROCm 证据同时通过时才能晋级。运行中的 episode 不会修改
模型权重，因此自我改进是可回放、可撤销、可答辩的近线流程，而不是无约束在线学习。

## AMD/ROCm 实现

Genesis 物理、离屏 RGB-D、SmolVLA AMP 训练、HIP 推理和冻结评估都使用单张 Radeon。
Force-Memory Harness 是 CPU/Python 侧的轻量确定性门，避免引入 CUDA-only 算子；VLA
仍通过 ROCm PyTorch 执行。它不增加可训练模型参数，主要优化端到端安全响应和有效 GPU
预算，而不是用更大模型掩盖接触控制瓶颈。

## 已有证据与尚未完成的证据

- SmolVLA v2 正式冻结集：96/100，0 次 35 N 越界。
- tri-suction/V-cradle v24：一个 1.44 m 超长箱案例成功，2.16 cm 误差、0 断吸、
  30.65 N 峰值托架力；这是机理集成证据，不是泛化率。
- PASH-VLA 的 Force-Memory 分支已完成 Radeon 单回合开发回归：68 次推理中 11 次收紧残差、
  2 次完全回退，0 次紧急停止；同一超长箱任务成功，2.11 cm 误差、0 断吸、30.64 N
  托架峰值。它仍未替换正式基线，因为这不是 `off / on` 的统计配对评估。
- v3 失败驱动候选为 91/100，Wilson 门拒绝；它证明晋级门能阻止退化，而不是证明所有
  自我改进都会有效。

## 论文级消融矩阵

| 组别 | 对照 | 主要指标 |
| --- | --- | --- |
| Harness | 原始 VLA / 数值限幅 / Harness-Lite / PASH-VLA | 动作 MAE、选中比例、回退、力中止 |
| 力记忆 | 无历史 / 6 样本历史 / 不同软门 | 成功、峰值力、首次接触冲击、P95 延迟 |
| 自我改进 | 无 replay / replay 无晋级门 / 完整隔离晋级 | 冻结成功率、Wilson 区间、回归数 |
| 末端执行器 | 单臂吸盘 / 双臂无托架 / 三吸盘+V 托架 | 抬升、断吸、负载分担和放置误差 |
| 模态 | RGB / RGB-D | MAE、显存、P50/P95、分 profile 成功 |

不能用单个 v24 案例支持 80% 泛化或 SCI 结论。正式论文声明至少需要新的尺寸、质量、
摩擦和偏置冻结集、多 seed、置信区间以及所有关键消融的同回合比较。
