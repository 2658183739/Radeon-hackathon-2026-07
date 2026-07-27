# PASH 自适应重试与技能获取

## 目的

该扩展补齐两个时间尺度之间的空白：Harness 在一次回合内约束 VLA，自我改进周期在回合之间
重新训练权重；此前没有“同一任务失败后，安全地再尝试两三次并记住哪种策略有效”的执行层。

新模块实现 **PASH Episodic Adaptation Loop**。它最多执行三次独立、可审计的场景尝试；每次
失败后定位第一个失败 primitive，并在不改变 35 N 门和冻结权重的前提下选择下一种控制权限。

## 从参考工作吸收的设计

- Harness VLA 的关键启发是：VLA 只负责适合学习控制的原语，解析控制负责确定性移动，Planner
  依据任务阶段、Task-Specific Memory 和 Global Memory 决定调用、回退与重试。
- InSight 的关键启发是：把完整轨迹切成 primitive，定位 primitive gap，只采集缺失技能的
  成功恢复轨迹，再经过数据审计写回统一 VLA，而不是每次从头学习完整任务。

本项目没有照搬两者代码。实现针对 Radeon、三吸盘、双 Panda 和快递搬运重新设计，并保持
SmolVLA、Harness、物理执行和权重晋级相互隔离。

开发参考入口：Harness VLA [项目页](https://harnessvla.github.io/)、
[RPent 代码](https://github.com/RLinf/RPent) 与 [arXiv:2607.08448](https://arxiv.org/abs/2607.08448)；
InSight 原始论文已核验为 [arXiv:2606.24884](https://arxiv.org/abs/2606.24884)，DOI
`10.48550/arXiv.2606.24884`。公众号文章只作为发现来源，不替代原始引用。

## 三层自适应

1. **回合内，3 Hz：**Force-Memory Harness 从五档残差选择安全动作，必要时回退 240 Hz 专家。
2. **尝试间，最多三次：**失败 primitive 决定下一控制策略；任务记忆和全局记忆共同排序候选。
3. **数据周期间：**成功恢复轨迹进入技能获取清单，经过 RGB-D/动作审计后才允许加入 Radeon
   再训练；冻结 100 回合和 Wilson 门决定新 checkpoint 是否晋级。

运行中的机器人永远不修改权重，因此这里的“在线自适应”是策略权限和 primitive 调度，
“权重自我改进”仍是回合之间的近线过程。

## 策略与安全规则

| 策略 | VLA 权限 | Force-Memory | 用途 |
| --- | --- | --- | --- |
| `pash_dual_arm` | 底盘 + 刚体投影双臂运输残差 + 深度侧路 | 开 | 协同托举的默认高能力尝试 |
| `pash_arm` | 底盘 + 运输阶段左臂有界残差 | 开 | 默认高能力尝试 |
| `pash_base` | 仅底盘残差，双臂专家控制 | 开 | 接触、抬升或精度失败后的安全恢复 |
| `expert_recovery` | VLA 只做 shadow 推理 | 关 | 力越界或前两种策略失败后的保守恢复 |

若出现 35 N 力越界，下一次只能选择 `expert_recovery`。吸附、抬升、放置或释放失败后，禁止
继续使用学习型机械臂残差。协同 V 型托架任务可以使用 `pash_dual_arm`：其差分残差强制为零，
左右目标通过同一次多末端 IK，并在放置前逐渐撤权；独立左臂的 `pash_arm` 仍被协同任务排除。

v2 将策略权限与小范围物理恢复参数组成同一个可记忆决策。吸附失败只允许在正负 6 mm 内搜索
吸盘中心；抬升失败使用 0.75 倍接近/垂直速度、增加 0.5 mm 接触和 15 mm 抬升；放置失败把
释放间隙从 15 mm 收紧到 10 mm；力中止只能使用 0.5 倍接近速度和减少 1 mm 接触的专家恢复。
所有参数在命令行入口再次校验，不能绕过三次上限或 35 N 门。

## 双层经验记忆

记忆键同时写入：

```text
task context   = profile : mass_band : previous_failed_primitive
global context = *       : mass_band : previous_failed_primitive
```

每种策略保存尝试数、成功数和力中止数。选择分数使用带先验的成功均值、有限探索奖励和较强的
力中止惩罚；任务上下文占 75%，全局上下文占 25%。这让同类快递优先复用具体经验，同时允许
“中等重量 + 抬升失败”之类的跨 profile 经验迁移。

## Primitive 写回

闭环按 `scene_stability -> suction_latch -> lift -> transport -> placement -> release` 顺序确定
第一个缺口。若后续尝试成功，`primitive-acquisition-manifest.json` 会把失败摘要、恢复策略、
成功摘要、实际 LeRobot 数据根和 primitive 文本写成候选。只有成功尝试真实保存轨迹且通过
传感器帧、动作维度、任务标签和数据隔离审计后，候选才允许进入 SmolVLA 训练；仅有 summary
会被明确标记为 `blocked_missing_trajectory`。

## Radeon 开发验证

0.40 kg 小纸箱在第一次 `pash_arm` 尝试即成功，因此系统没有执行多余重试：抬升 8.11 cm，
运输 30 cm，放置误差 2.20 cm，零断吸，接触峰值 6.25 N。SmolVLA 推理 84 次，实际参与
4694 个物理步；左臂残差执行 2343 步，30 次 IK 全部接受。Force-Memory 收紧一次，最低 cap
为 0.292，紧急停止为零。热推理平均/P95 为 200.54/209.89 ms。

该结果只验证新入口和记忆写入可运行，不能证明重试提高成功率。完整证据见
`evidence/mobile_bimanual/adaptive_retry_v1/`。

## v2 已知失败恢复验证

v2 没有扩大测试总体，而是复用 100 回合冻结评估中的已知失败
`primitive-v2-dry-run-holdout-005`。第一次 `pash_arm@nominal` 再次在 `lift_success` 门失败；
第二次自动选择 `pash_base@gentle_lift` 并成功，放置误差 1.44 cm，接触峰值 4.84 N，断吸和
力中止均为零。成功尝试保存 673 帧 RGB-D/状态/动作数据，数据审计全部通过，并产生一个可进入
primitive 切分的再训练候选。证据与哈希位于 `evidence/mobile_bimanual/adaptive_retry_v2/`。

这是一个配对机理验证，只能说明恢复链路真实执行并生成可训练数据，不能估计总体恢复率或支持
“自进化提高成功率”的统计结论。

## 运行

```bash
PYTHONPATH=src:. python scripts/run_mobile_adaptive_retry_rocm.py \
  --output outputs/pash-adaptive-retry \
  --strategy-memory outputs/pash-strategy-memory.json \
  --smolvla-checkpoint configs/active_mobile_smolvla.json \
  --backend rocm --max-attempts 3 --policy-hz 3 \
  --parcel-profile small_carton \
  --parcel-size-m 0.20 0.12 0.20 \
  --parcel-mass-kg 0.40 --parcel-friction 0.80
```

论文消融必须分别报告首试成功率、最多三次最终成功率、平均尝试数、力中止和策略分布；不得把
重试后的最终成功率写成单次成功率。
