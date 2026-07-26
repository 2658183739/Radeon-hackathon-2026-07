# 组内安全优先抓取排序器

## 动机

现有 6,276 参数 MLP 对每个候选独立预测四个标签，但逐点目标没有直接表达部署决策：从同一包裹的
静态可行候选中选一个。V2 因此加入组内训练目标，同时保持完全相同的特征 schema、网络、参数量、
推理接口和运行时字典序排序。这样比较只隔离训练目标，不混入模型容量差异。

## 冻结排序语义

候选按 `(profile, episode)` 分组。即使可行候选数不同，每组仍贡献相同权重。目标包含四个带校准
意义的逐点项和两个组内成对项：

1. safe 候选的 unsafe logit 必须低于力中止候选；
2. 只在 safe 候选内部，成功候选的 success logit 必须高于失败候选；
3. unsafe 概率、success 概率、对数峰值力和对数耗时继续使用校准损失。

安全 pair 权重为 2.0，safe-success pair 权重为 1.0；成功绝不能抵消安全中止。运行时仍先经过独立
硬 IK/碰撞门，再依次比较 unsafe 概率、success 概率、预测力、耗时和静态 rank。

## 实现与验证

`grouped_grasp_row_indices()` 生成稳定 episode 分组；
`groupwise_grasp_preference_pairs()` 只构造组内偏好；
`train_grasp_scorer_rocm.py --objective groupwise-safety-first` 使用组均衡校准与成对 logistic 损失。
默认 `pointwise` 目标保持不变，作为基线。

一次五步 Radeon smoke 使用两个已完成 V2 train 组，共 12 行，在 `AMD Radeon Graphics`、HIP 7.2
上用 1.39 秒生成有效检查点。训练内选择避开两个基线安全中止，并恢复一次成功。它只能证明接线：
两个已观察组、五步且训练内评估，不能支持泛化声明或模型选择。

## 评测边界

必须在执行 development split 前冻结逐点和组内模型的精确超参数。两种方法使用相同完整 train
数据与固定 seed。development 最多选择一个通过安全、任务、逐 profile 与 Radeon 延迟门禁的评分
器；该选择冻结前，holdout 始终不可用。
