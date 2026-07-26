# 抓取评分器 V2 模型选择协议

机器可读真源是 `configs/grasp_candidate_model_selection_v2.toml`。它在训练目标与晋级门代码提交后
冻结，但冻结时完整 train 数据集、两份正式检查点和任何 development rollout 都还不存在。

只允许两个同容量候选：原样逐点 MLP 与组内安全优先目标。二者使用相同 28 维特征、6,276 参数
网络、2,000 步、`1e-3` 学习率、`1e-4` 权重衰减、seed 42 和单张 Radeon GPU。观察 development
后不得扫描学习率、宽度、seed 或损失权重。

必须先完成 train 采集，再只用 train 训练并哈希冻结两个检查点；只有两个检查点都存在，才能开始
development 采集。评测必须包含完整 16 组，四个 profile 各 4 组。若任一 profile 增加安全中止、
总体安全/成功均未优于静态排序，或 Radeon 六候选 warm batch P95 大于等于 5 ms，候选即失败。

合格候选依次按安全中止、成功、选中候选平均力、平均耗时、Radeon P95 和固定候选名排序。若两个
都失败，则不晋级、不复用 development 调参，也不打开 holdout；若选出一个，则先冻结其检查点与
全部超参数，再执行唯一一次 holdout。
