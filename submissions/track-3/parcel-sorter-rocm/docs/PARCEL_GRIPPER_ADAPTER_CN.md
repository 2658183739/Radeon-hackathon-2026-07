# 开源包裹夹爪适配器

## 范围

本开发里程碑只检验一个物理假设：stock Panda 指尖的承托长度不足，导致部分高纸箱在完整反馈运输中
滑落。方法改变承托几何，不继续拟合评分阈值、力阈值或控制增益。

适配器**默认关闭**，不修改 35 N 实测力中止线、抓取排序、运输控制器或重试策略；本轮没有打开
任何 holdout episode。

## 设计与开源来源

运行时由 `build_parcel_gripper_mjcf` 解析锁定 Genesis 1.2.3 源码树自带的 Panda MJCF，生成引用
上游 mesh 目录的新 MJCF，并为每根手指加入一个盒形碰撞体和一个青色视觉体。仓库不复制第三方
mesh。

冻结设计把 stock 指尖延长 30 mm。每个盒体的半尺寸为 `10 x 4 x 15 mm`，局部中心为
`(0, 5.5, 68) mm`，因此从 stock 指垫局部 `z=53 mm` 末端连续延伸到 `z=83 mm`。采用的上游
来源是 Genesis 1.2.3 Apache-2.0 Panda MJCF。

Radeon 在线几何探针显示：每根手指的可碰撞 geom 从 6 个增加到 7 个，世界坐标 AABB 长轴由约
56 mm 增至 85 mm。生成 XML 共包含 4 个命名适配器 geom，即每指一个碰撞体和一个不参与碰撞的
视觉体。

## 复现

在赛事 Radeon 实例的项目根目录执行：

```bash
export PYTHONPATH="$PWD/src"
python scripts/probe_gripper_adapter_geometry.py \
  --backend rocm \
  --profile large_narrow_carton \
  --episode 4120001 \
  --extension-m 0.030 \
  --output outputs/gripper-adapter-development-v1/geometry-probe.json
```

保持控制器不变，复现已观察机理对照：

```bash
python scripts/diagnose_counterfactual_grasp_candidates.py \
  --config configs/catalog_v2.toml \
  --profile medium_carton \
  --episode 4120001 \
  --backend rocm \
  --candidate-id canonical-long-+0.000-up-0.040 \
  --contact-wrench-telemetry \
  --contact-wrench-backend cpu \
  --parcel-gripper-adapter \
  --parcel-gripper-extension-m 0.030 \
  --output outputs/gripper-adapter-development-v1/4120001-canonical-40-adapter.json
```

其中 CPU 只计算微小的只读诊断评分；Genesis 仿真、接触求解和闭环任务仍通过 ROCm 在单张
Radeon 上运行。

## 开发证据

| 冻结对照 | Stock | 30 mm 适配器 |
|---|---:|---:|
| `4120001`，中心 `+40 mm` | 未入箱，21.81 N | 完成，24.07 N |
| `4120001`，中心 `+45 mm` 成功哨兵 | 完成，10.31 N | 完成，12.55 N |
| `7130001`，6 个冻结训练候选 | 3/6 完成 | 5/6 完成 |
| `7130001`，安全中止 | 2/6 | 1/6 |

8 个配对候选执行中，stock 的 4 次成功全部保留，并恢复 3 次 stock 失败。剩余候选越过未修改的
安全线，在 36.95 N 中止；适配器成功回合中的最高力为 32.69 N，且没有适配器回合掉落包裹。

这些数据只来自两个确定性 episode 的 8 次候选执行，不是 8 个独立包裹样本，也不能解释成成功率。
它支持把适配器保留为开发候选，但不足以默认启用或声明泛化。

## 决策边界

- 将长度冻结为 30 mm，不围绕现有观察继续扫描。
- 在另行冻结的评估通过前保持默认关闭。
- 35 N 门禁继续独立于适配器和任何学习模型。
- 不使用现有评分器 holdout 为本几何方案背书。
- 每份证据都记录生成 MJCF 与上游来源哈希。

当前仿真保留 stock 手指显式惯性参数，因此只代表轻量适配器，尚未绑定具体打印材料、紧固件、
附加质量或柔顺性。迁移到实体硬件前，还必须完成 CAD、材料/质量辨识、合并惯性、碰撞间隙审查和
真实力标定。
