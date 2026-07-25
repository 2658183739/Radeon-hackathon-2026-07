# ROCm 结构化抓取评分器

## 当前状态

冻结的 train 与 development 阶段均已完成。12 个 train episode 中有 4 个、6 个 development
episode 中有 1 个触发正式 reset-fallback gate；其余均记录为结构化的非标签跳过。评分器没有接入
`GenesisParcelEnv`，正式行为继续使用静态排序，holdout 仍被锁定。唯一适用的 development 组不支持
升级，因此没有理由为了选模而打开 holdout。

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

reset-fallback gate 未触发时输出 `skipped_inactive_reset_gate`，且不生成 rollout 标签。数据集构建器
直接读取 manifest，只忽略这一显式状态，并校验每个接纳源文件的哈希。已知 Genesis 解释器清理阶段
的 `SIGSEGV/139`，只有在完整输出通过身份、控制器契约、重复次数和 rollout 数量后置条件后才接纳。

## 冻结 train 与 development 结果

train 采集得到 4 个适用组、24 行：`large_narrow_carton` 和 `medium_carton` 各 2 组，
`shoe_box_proxy` 为 0 组；另外 8 个 episode 没有进入该学习器负责的控制器分支。标签包含 3 条成功
和 14 条安全中止。固定 seed 42、2,000 步的 Radeon 训练耗时 2.502 秒。样本内重建保持 1 次成功，
并把选中候选的安全中止从静态基线 3/4 降到 0/4；这只是训练拟合，不是泛化证据。

development 只有 `large_narrow_carton:7140001` 一个适用组。六个候选全部超过 35 N，且没有一个
成功；静态排序与模型都选中安全中止失败。模型所选 rollout 实测 35.896 N，最低力候选为
35.521 N，但后者仍然中止。因此模型在 development 上既没有任务恢复，也没有安全恢复；保持断开，
不接入控制器，holdout 继续未查看。

显式选择的真实六候选 development 批次在预热 10 次后，P50/P95 为 0.901/0.921 ms，通过单独的
5 ms 延迟门禁。延迟通过不能覆盖行为和数据覆盖门禁失败。

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

冻结 train/development 使用 manifest 复现，不使用手工 glob：

```bash
python scripts/build_grasp_candidate_dataset.py \
  --protocol configs/grasp_candidate_learning_v1.toml \
  --manifest outputs/grasp-scorer-v1/collection/train/manifest.json \
  --manifest outputs/grasp-scorer-v1/collection/development/manifest.json \
  --output outputs/grasp-scorer-v1/train-development-dataset.json

python scripts/train_grasp_scorer_rocm.py \
  --dataset outputs/grasp-scorer-v1/train-dataset.json \
  --output-dir outputs/grasp-scorer-v1/train-v1 \
  --train-split train --steps 2000 --device cuda

python scripts/evaluate_grasp_scorer.py \
  --dataset outputs/grasp-scorer-v1/train-development-dataset.json \
  --checkpoint outputs/grasp-scorer-v1/train-v1/grasp_scorer.pt \
  --split development --device cuda \
  --latency-group-id large_narrow_carton:7140001 \
  --warmup 10 --benchmark-repeats 100 \
  --output outputs/grasp-scorer-v1/train-v1/development-evaluation.json
```

smoke 紧凑记录为 `evidence/training/grasp-scorer-smoke-rocm-v1.json`；冻结 train/development 记录为
`evidence/training/grasp-scorer-train-development-rocm-v1.json`。完整数据集、检查点、manifest、训练
summary 和预测保存在 Git 忽略的 `outputs/`，并由 SHA-256 绑定。

最终同步的 Radeon 源码树编译通过，全量 247 项单元测试通过。
