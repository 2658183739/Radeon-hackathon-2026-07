# ROCm 结构化抓取评分器

## 当前状态

数据契约、冻结划分、数据集构建器、训练入口、检查点加载器、独立评估器和延迟基准均已实现。
评分器尚未接入 `GenesisParcelEnv`，正式行为仍使用静态排序。剩余工作是按冻结编号采集正式闭环
train/development 标签、训练、只打开一次未查看 holdout，最后再做门控接入决策。

## 为什么选择这个模型

正式反事实已经证明：静态 IK/碰撞排序和理想化直接 IK 运输都可能漏掉正式执行失败。VLA 对这个
底层选择过大，也不能替代硬安全。因此第一版采用 6,276 参数 MLP，用 PyTorch/ROCm 训练；
确定性 IK、碰撞可行性和 35 N 监督器始终放在模型之外。

每个候选包含 28 个带版本的特征，覆盖包裹尺寸、估计质量与摩擦、初始位姿、动作延迟、目标侧、
候选位姿与偏置、wrist/IK 初值、可操作度、关节距离、碰撞净空和静态排名。四个输出分别学习
安全中止、任务成功、峰值力与时长。选择顺序为：预测安全风险、成功、力、时长，最后才是静态排名。

## 冻结协议

`configs/grasp_candidate_learning_v1.toml` 在执行任何新 episode 前写入。它为
`medium_carton`、`shoe_box_proxy` 和 `large_narrow_carton` 预留 12 个 train、6 个 development
和 6 个 holdout episode。已经观察过的 `4120001` 被明确隔离为 `smoke`，不能进入泛化声明。

留出集门禁也在采集前冻结：

1. 相比静态排序不能新增安全中止，也不能出现任何逐 profile 配对回归；
2. holdout 上至少恢复一个静态排序的任务失败；
3. 单张 Radeon 上预热批量推理 P95 小于 5 ms。

预览并开始冻结的训练采集：

```bash
python scripts/run_grasp_candidate_collection.py \
  --protocol configs/grasp_candidate_learning_v1.toml \
  --split train --output-dir outputs/grasp-scorer-v1/collection --dry-run

python scripts/run_grasp_candidate_collection.py \
  --protocol configs/grasp_candidate_learning_v1.toml \
  --split train --output-dir outputs/grasp-scorer-v1/collection --resume
```

每个 episode 都在新 Python 进程执行，隔离 Genesis 全局状态；manifest 记录精确命令、状态和源文件
哈希。完成模型选择前，holdout 默认锁定，只有显式提供 `--unlock-holdout` 才会执行。

## Radeon smoke 结果

已观察机理回合的 6 个正式闭环候选标签形成 1 个 smoke 组，每行 28 个特征。AMD Radeon 上使用
PyTorch 2.9.1、HIP 7.2 做 1,000 步全批量训练耗时 1.715 秒，最终训练损失为 0.000293。
离线重建选中了安全成功候选，而静态排名选中已知任务失败。这只是样本内拟合，不是留出收益证据。

独立加载检查点的冷启动批量耗时为 308.53 ms；预热 10 次后，100 个六候选批次的 P50/P95 为
0.883/0.902 ms，折合每候选 0.147/0.150 ms。所有报告都把冷启动与稳态延迟分开。

## 复现命令

```bash
export PYTHONPATH=/workspace/parcel-sorter-opt-v1/src
python scripts/build_grasp_candidate_dataset.py \
  --protocol configs/grasp_candidate_learning_v1.toml \
  --input outputs/counterfactual-grasp-v1/4120001-static-first.json \
  --input outputs/counterfactual-grasp-v1/4120001-alternatives.json \
  --output outputs/grasp-scorer-v1/smoke-dataset.json

python scripts/train_grasp_scorer_rocm.py \
  --dataset outputs/grasp-scorer-v1/smoke-dataset.json \
  --output-dir outputs/grasp-scorer-v1/smoke-train \
  --train-split smoke --steps 1000 --device cuda

python scripts/evaluate_grasp_scorer.py \
  --dataset outputs/grasp-scorer-v1/smoke-dataset.json \
  --checkpoint outputs/grasp-scorer-v1/smoke-train/grasp_scorer.pt \
  --split smoke --device cuda --warmup 10 --benchmark-repeats 100 \
  --output outputs/grasp-scorer-v1/smoke-train/evaluation.json
```

紧凑机器可读记录为 `evidence/training/grasp-scorer-smoke-rocm-v1.json`。完整数据集、检查点、训练
summary 和预测保存在 Git 忽略的 `outputs/`，并由 SHA-256 绑定。

最终同步的 Radeon 源码树编译通过，全量 237 项单元测试通过。
