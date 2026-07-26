# 抓取候选学习 V2 样本选择结果

## 结果

V2 采集总体已冻结，可以在 Radeon 主机上只执行训练集。无物理选择得到 32 个训练组、16 个
开发组和 16 个锁定 holdout 组，并在 `medium_carton`、`shoe_box_proxy`、
`large_narrow_carton`、`near_limit_box` 四种 profile 间保持均衡。选择过程中没有构建
Genesis 场景、没有执行机器人动作，也没有读取任务结果。

精确分组写在 `configs/grasp_candidate_learning_v2.toml`。来源证据为
`evidence/training/grasp-candidate-learning-v2-episode-selection.json`，SHA-256 是
`38198aa77cb3567899f088110907b0dd3aa2e54f04bdd90b1a16beb991ac4b8c`。

## 步骤与决策原因

1. 不直接扩大 V1。V1 的 reset-fallback 激活只让 12 个训练组中的 4 个、6 个开发组中的 1 个
   产生完整标签；问题是总体覆盖不足，而不是已经证明需要更大的网络。
2. 提交 `af88121` 在任何新 episode 执行物理仿真前冻结 V2 选择器和激活契约，把实验设计与
   已观察结果分离。
3. 选择器只读取确定性包裹随机化和既有盒高谓词，在四个全新命名空间内按 ID 升序选前 16 个
   合格样本，再按 8/4/4 分给训练、开发和 holdout。
4. 新审计器核对证据哈希、catalog 哈希、选择器哈希、确定性随机样本、几何谓词、TOML 精确
   分组、各 split 数量、单卡 ROCm 契约、碰撞复位要求和 holdout 锁。
5. 审计器第一次把 JSON 往返后的 tuple/list 等价表示误判为差异。比较方式改为规范 JSON 后
   通过；数值、ID 和选择证据均未修改。
6. Radeon 纯计划得到 32 个训练组、最多 192 次 rollout，以及 16 个开发组、最多 96 次
   rollout。每条子命令都带 `--planning-activation geometry-eligible`；holdout 请求在生成运行
   计划之前被拒绝。
7. CLI 最初的精简输出漏掉激活策略字段，虽然子命令本身正确。现在摘要也输出该字段，使保存的
   dry-run 证据可以独立审计。

## 能力与安全边界

当前代码已经能选择、审计、规划、断点续跑并验证控制器保真的候选标签采集。学习模型只能在静态
可行候选内部重新排序。硬 IK/碰撞可行性、碰撞检查复位、单调运输契约和独立 35 N 中止器均位于
学习评分器之外。

本阶段尚未证明 MLP 或组内排序器提升了机器人能力。必须先完成训练采集，训练完成后才能打开开发
集。只有冻结唯一评分器和全部超参数后，才能执行一次 holdout。结构化排序证明开发集价值之前，
视觉、ACT、Diffusion、VLA 和 ROS 2 继续暂停。

## 复现

开始采集前先执行审计：

```bash
cd /workspace/parcel-sorter-opt-v1
PYTHONPATH=src /opt/venv/bin/python \
  scripts/audit_grasp_candidate_learning_v2_protocol.py \
  --output outputs/grasp-scorer-v2/protocol-audit.json
```

下一条唯一允许的物理执行命令是训练 split：

```bash
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/run_grasp_candidate_collection.py \
  --protocol configs/grasp_candidate_learning_v2.toml \
  --split train \
  --output-dir outputs/grasp-scorer-v2/candidates \
  --config configs/catalog_v2.toml \
  --backend rocm \
  --max-candidates 6 \
  --repeats 1
```

训练和模型开发期间不得传入 `--unlock-holdout`。
