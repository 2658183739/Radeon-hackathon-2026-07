# 数据集卡：Parcel Sorter RGB-D 专家演示

## 摘要

数据完全由 Genesis 快递分拣仿真和确定性 IK 专家生成。正式采集包含 120 次随机尝试，
其中 96 个成功回合、11,753 帧进入模仿学习数据；全部 120 次尝试保留 JSONL 审计轨迹。

## 字段

| 字段 | 形状 | 单位/含义 | ACT 是否使用 |
| --- | --- | --- | --- |
| `observation.images.overhead_rgb` | `3 x 224 x 224` | uint8 RGB | 是 |
| `observation.images.overhead_depth` | `1 x 224 x 224` | float 米制深度 | 仅修正后的新 shard 有效 |
| `observation.images.overhead_depth_rgb` | `3 x 224 x 224` | 固定量程深度视图 | 可选 RGB-D 输入 |
| `observation.state` | `20` | 关节、末端、目标、接触力 | 是 |
| `observation.privileged_state` | `7` | 仿真包裹真值位姿 | 否 |
| `action` | `8` | 位置、四元数、夹爪 | 训练目标 |

物理 240 Hz、控制 30 Hz、相机 10 Hz；两个相机更新之间保持最近一帧。

## 随机化

包裹尺寸、质量、摩擦、XY、yaw、目标、相机位置和动作延迟由 seed 与 episode 索引确定。
基础 ACT 数据使用 `configs/baseline.toml`；catalog v1 包含 7 类带权训练 profile，catalog v2
包含 12 类均衡训练 profile 和 9 类仅评测行业尺寸 profile。Box 与 Cylinder 按实际几何
创建，目录 evaluator 维持稳定的 profile episode 编号。

## 纳入规则

只有成功专家回合进入行为克隆数据。失败尝试保留在审计轨迹中，未来可用于困难样本、
恢复学习或偏好学习，但必须使用明确方法，不能直接当正确动作标签。

## 适用范围

- 本仿真工位的 ACT/模仿策略训练；
- RGB、RGB-D 和状态消融；
- 可复现教学；
- 困难样本与安全分析。

## 限制

- 只有仿真，没有真机标定；
- 成功样本训练存在选择偏差；
- 正式 120 回合数据仍主要覆盖当前平行夹爪可处理的刚性包裹；圆筒和行业尺寸边界需要
  单独采集/评测；
- 96 回合不足以支持广泛语义泛化；
- 历史 96 回合 shard 存在 1,000 倍深度尺度错误，只可用于 RGB/状态训练，不可用于 RGB-D；
- 修正 RGB-D 已完成一回合传感器/训练链路烟雾，尚无统计意义上的任务效果结论。

## 发布要求

对外发布前应提供 episode manifest、特征 metadata、准确 Git commit、上游版本、生成配置
和 SHA-256。必须审查模拟器资产的许可证影响并明确声明数据集许可证，不能直接把源码的
MIT 许可证自动套用到数据集。
