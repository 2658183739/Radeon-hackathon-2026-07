# Genesis Panda 双指约束最小复现协议

## 目的

质量感知的 30 mm 快递夹指适配器在冻结的 `medium_carton / 4120001` 轨迹中出现了
162.19 N 接触力和 115.55 mm 穿透；相同几何、相同控制命令的 stock 惯量消融没有出现该故障。
本协议先移除分拣状态机、抓取规划器、相机和学习策略，再验证物理模型分支能否在固定命令下独立重现。

这是机理实验，不是任务性能或鲁棒性评测；不打开新 episode，也不查看评分器 holdout。

## 候选确定前的上游审计

Genesis 1.2.3 会把所有 equality `solref` 时间常数限制为至少 `2 * substep_dt`。
Panda 资产把双指 equality 写成 `solref="0.005 1"`，所以在 240 Hz 下实际变为 0.008333 s。
此前唯一预注册的 0.010 s 候选更早失败，因此不继续扫描时间常数。

Genesis [#3051](https://github.com/Genesis-Embodied-AI/genesis-world/issues/3051) 和
[#3072](https://github.com/Genesis-Embodied-AI/genesis-world/pull/3072) 还发现过另一项
MJCF 默认 armature 缺陷，但该缺陷不是本轮候选：

- 项目锁定的 Genesis 提交 `ec0efcc0` 晚于 #3072，解析器已包含修复；
- Panda MJCF 自身通过继承的 `panda` 默认类显式声明 `armature="0.1"`，两个手指关节也继承该值。

所以对这个 Panda 模型设置 `default_armature=None` 不应成为干预。本轮不引入无文档依据的求解器选项。

## 冻结复现

| 字段 | 冻结值 |
|---|---|
| 运行环境 | 单张 Radeon `gfx1100`、ROCm 7.2、Genesis 1.2.3 |
| Genesis 提交 | `ec0efcc0daf9b9932920e6b73f5f810961330997` |
| 来源观测 | `medium_carton / 4120001`，控制帧 196 |
| 几何 | 每指 30 mm 适配器，1240 kg/m3 |
| 两个条件 | stock 显式惯量消融；合并刚体惯量 |
| 初始手臂状态 | 从冻结 reset 位姿确定性 IK 到已记录末端位姿 |
| 初始包裹状态 | 帧 196 位姿，以及冻结 episode 的质量、尺寸和摩擦 |
| 初始手指位置 | 0.03228778 m、0.03228711 m |
| 初始速度 | 全部清零 |
| 手臂命令 | 保持重建的 7 关节位置 |
| 双指命令 | 恒定 `[-20, -20]` N |
| 物理步进 | 240 Hz，最多 64 个子步 |
| 安全边界 | 实测力首次超过 35 N 或穿透达到 1 mm 后停止 |

两个条件分别使用独立进程和全新场景。每个物理子步都沿用现有接触分支契约，记录所有机器人接触、
geom/link 身份、位置、法向、穿透、双方接触力、手指位置、速度、实际力和控制力；同时记录生成
MJCF 的 SHA-256 及位姿重建误差。

## 预注册解释

- `mass_aware_instability_reproduced`：stock 惯量条件不越界，质量感知条件触发任一门禁；
- `bounded_contact_sensitivity_only`：两者都不越界，但达到冻结的轨迹差异阈值；
- `not_reproduced`：两者都不越界，也没有达到已注册差异阈值；
- `invalid_reference`：stock 惯量条件也越界，此时不能把结果归因于质量感知模型。

轨迹差异阈值保持为接触力/手指力 1 N、手指位置 0.1 mm、手指速度 0.01 m/s。
负结果只说明这个静态、零速度重建不足以独立复现，不能据此解除完整分拣任务中的故障门禁。

## 执行命令

```bash
python scripts/reproduce_genesis_finger_constraint.py \
  --variant stock-inertia --backend rocm \
  --output outputs/finger-constraint-minimal-repro-v1/stock-inertia.json

python scripts/reproduce_genesis_finger_constraint.py \
  --variant mass-aware --backend rocm \
  --output outputs/finger-constraint-minimal-repro-v1/mass-aware.json

python scripts/compare_genesis_finger_constraint_repro.py \
  --reference outputs/finger-constraint-minimal-repro-v1/stock-inertia.json \
  --candidate outputs/finger-constraint-minimal-repro-v1/mass-aware.json \
  --output outputs/finger-constraint-minimal-repro-v1/comparison.json
```

看到结果后不得扫描物理频率、时间常数、密度、延长量、摩擦、控制增益、力阈值、位姿、episode 或候选。
若需要捕获动态状态或验证上游补丁，必须重新预注册。
