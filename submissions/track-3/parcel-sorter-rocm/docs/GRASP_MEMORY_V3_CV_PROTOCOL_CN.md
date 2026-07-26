# 保守抓取记忆 V3：Train-only 交叉验证协议

## 状态与目的

本协议在任何 V3 交叉验证结果产生前冻结。V2 的两份 6,276 参数 MLP 在一次性 development 上均
发生四 profile 安全回归，因此被拒绝，V2 holdout 保持未打开。本协议只回答一个更窄的问题：
V2 已观察训练集能否支持一个低容量、可拒绝、默认回退的记忆式候选排序器，从而值得为 V3 采集
全新物理总体。

通过 train-only CV 也不直接授权新物理执行。若存在合格候选，仍必须先另写并冻结完全不重叠的
V3 train/development/holdout 协议；若全部失败，则停止该学习分支并保留静态几何基线。

## 冻结输入

- 数据：V2 `train-dataset.json`，SHA-256
  `71761164467ba3b29866d87639b73474a5d5f2cc1fdb8907d62957a6c73703d5`。
- 只允许 `train` 的 32 个物理组、192 行候选；development 与 holdout 禁止输入。
- 四个 profile 各 8 组。
- 按 `SHA-256(seed, profile, group_id)` 确定性排序并做 4 折，每折每 profile 2 组；一个物理组的
  6 个候选不能跨折。

## 算法

每折只用其余 24 个组建立同 profile KNN 记忆。28 维特征使用训练折中位数与 MAD 缩放；MAD 为零
时回退总体标准差，再为零时取 1。距离计算由 PyTorch ROCm 在单张 Radeon 上批量执行。

一个候选必须同时满足以下条件才允许替换静态首选：

1. `k` 个同 profile 近邻中没有安全中止；
2. 至少一半近邻是安全成功；
3. 近邻最大峰值力不超过未修改的 35 N 安全线；
4. 第 `k` 近邻距离不超过训练折的逐 profile 留一组距离分位数；
5. 静态 rank 不超过候选的冻结信任范围。

若没有候选同时通过，必须回退静态几何首选。多个候选通过时，依次比较安全成功支持数、近邻最大
力、第 `k` 距离、静态 rank 和候选 ID。该方法不会输出能覆盖硬 IK、碰撞检查复位或 35 N 运行时
中止器的权限。

## 候选网格

协议只比较 6 个预先固定组合：`k` 为 3/5/9，静态 rank 上限为 3/6/15，OOD 分位数为
0.90/0.95。精确组合见 `configs/grasp_memory_v3_cv.toml`。35 N、50% 成功支持、4 折、seed、
profile 集、延迟组和全部晋级门在候选间保持相同。

## 晋级门

候选必须满足：

- 32 个 OOF 组和每 profile 8 组完整；
- 任一 profile 不得增加安全中止；
- 任一折不得增加安全中止；
- 总体至少减少一次安全中止或增加一次成功；
- Radeon 六候选 warm P95 小于 5 ms。

合格候选依次按安全中止少、成功多、平均峰值力低、偏离基线次数少、P95 低和名称选择。即使选出
候选，输出也固定为 `new_physics_authorized=false`。

## 复现

先审计冻结协议和实际数据：

```bash
cd /workspace/parcel-sorter-opt-v1
PYTHONPATH=src /opt/venv/bin/python \
  scripts/audit_grasp_memory_v3_cv_protocol.py \
  --dataset outputs/grasp-scorer-v2/model-selection/train-dataset.json \
  --output outputs/grasp-memory-v3/cv-protocol-audit.json
```

审计通过后，唯一允许的 CV 命令是：

```bash
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/cross_validate_conservative_grasp_memory.py \
  --dataset outputs/grasp-scorer-v2/model-selection/train-dataset.json \
  --protocol configs/grasp_memory_v3_cv.toml \
  --output outputs/grasp-memory-v3/train-only-cv.json
```

协议文件 SHA-256 为
`80911bf25a2642fe0b099ab27d22fbd8e04ffdc40bc91434aa465405e4893b02`。
