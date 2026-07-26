# 抓取评分器 V2：训练冻结结果

## 结论

2026-07-26，单张 AMD Radeon `gfx1100` 在 ROCm 7.2 上完成 V2 训练集采集和两份同容量模型拟合。
训练集包含 32 个物理 episode 组、四个 profile 各 8 组、每组 6 个候选，共 192 次候选闭环执行；
32 组全部完成，无采集失败。development 和 holdout 在检查点冻结前均未创建。

两份正式模型都使用 28 维特征、6,276 个参数、2,000 步、学习率 0.001、权重衰减 0.0001 和
seed 42。pointwise 训练耗时 2.872 秒，groupwise-safety-first 训练耗时 46.162 秒。两者的检查点、
摘要、数据集和协议均通过 SHA-256 绑定。PyTorch 摘要中的 `device=cuda` 是 ROCm 兼容 API 命名；
实际设备字段为 `AMD Radeon Graphics`，HIP 版本为 `7.2.53211-e1a6bc5663`。

## 结果边界

训练集内，静态首选为 7/32 成功、17/32 安全中止；pointwise 重建选择为 12/32 成功、4/32
安全中止，groupwise-safety-first 为 10/32 成功、4/32 安全中止。这些数字只证明两种目标都能拟合
已观察训练组，不能用于选择模型，也不能声明泛化提升。正式选择只允许使用一次冻结的 16 组
development；holdout 继续锁定。

groupwise 训练更慢，是因为它除逐点校准外还在每个 episode 内构造安全优先和成功优先 pair。
训练时延不参与晋级；部署约束使用冻结的六候选预热推理 P95 小于 5 ms。

## 决策与原因

1. 先完整采集 32 组，再训练。这样不会让部分训练结果影响后续样本或超参数。
2. 只比较两份预先冻结且容量相同的模型。差异只能归因于 pointwise 与 groupwise 目标，不能归因于
   参数量或训练预算。
3. 学习器只重排通过静态 IK/碰撞门的候选。碰撞检查复位、35 N 中止器和控制状态机继续独立执行。
4. Git 只保存冻结清单、训练摘要和紧凑索引。226 MiB 原始轨迹、数据集与检查点留在 Radeon 工作区，
   通过字节数和 SHA-256 引用，避免普通仓库膨胀。
5. 只有冻结清单通过独立哈希和 AMD/HIP 元数据核验后，才启动 development。该顺序由脚本门禁执行，
   不是人工约定。

## 核心哈希

| 产物 | SHA-256 |
| --- | --- |
| collection 协议 | `1e9d644e68f0d2ead3d9f5012c6ec1de0c3e0d4da36150ef39f84431c7989f30` |
| 模型选择协议 | `091c8e28efcab4b59663e07b03ec51daa609d057fbff97a79b26adc9233241ee` |
| 训练数据集文件 | `71761164467ba3b29866d87639b73474a5d5f2cc1fdb8907d62957a6c73703d5` |
| pointwise 检查点 | `9e0945b57906f703b1cfa8764a4446eab3ecdf6958fca2e3d65f157a8c9952a5` |
| groupwise 检查点 | `d2edbb9f66fe8279f303ea80e2bed46eb631232222ed357efd4fff372afce621` |

机器可读证据见 `evidence/training/grasp-scorer-v2-train-evidence.json`。

## 下一门禁

development 必须完整得到 16 组、四个 profile 各 4 组。两份冻结模型随后在相同候选组上评估：任何
profile 不得增加安全中止，总体至少减少一次安全中止或增加一次成功，六候选 warm P95 必须小于
5 ms。只有通过者才可能被选中；若两者都失败，则登记 `no_promotion`，不得复用 development 调参，
也不得打开 holdout。
