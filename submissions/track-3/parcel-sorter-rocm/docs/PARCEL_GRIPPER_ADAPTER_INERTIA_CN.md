# 包裹夹爪适配器质量与惯量

## 问题与边界

第一轮 30 mm 适配器实验保留了 stock Panda 手指惯量。本轮追问：加入有限适配器质量、质心偏移和
完整惯量张量后，同一几何是否仍然有效。这是物理真实性门禁，不是密度或几何搜索。

适配器继续默认关闭。延长量冻结为 30 mm，有效密度固定为 1240 kg/m3，实测力中止线保持 35 N。
实验只使用已经观察过的 `4120001 medium_carton` 机理对照，不打开评分器 holdout、新 episode 或
`7130001` 扩大组。

## 实现

每个生成适配器盒体尺寸为 `20 x 8 x 30 mm`，体积为 `4.8e-6 m3`；按固定有效密度计算，每根
手指增加 `5.952 g`，手指总质量由 `15.000 g` 变为 `20.952 g`。

`combine_rigid_body_with_box_inertia` 先计算均匀盒体绕自身质心的惯量，再用平行轴定理把 stock
手指与适配器共同换算到合并质心。MJCF 生成器把 stock `diaginertia` 替换为显式六分量
`fullinertia`：

```text
质量 = 0.020952 kg
质心 = (0, 0.00156242840779, 0.0193172966781) m
完整惯量 =
  2.26856869553e-05  2.27234426117e-05  1.10904434364e-06
  0                   0                  -1.59367697595e-06 kg m2
```

生成文件名同时包含两个冻结物理参数：
`panda_parcel_adapter_30p0mm_1240kgm3.xml`。配置会验证 100--2500 kg/m3 的有效密度范围，但本轮
没有扫描密度。正式执行、诊断与几何探针 CLI 都可以显式传入该值；遥测区分
`stock_explicit_inertia` 与 `combined_rigid_body`，并记录每指附加质量。

## Radeon 验证

Genesis 1.2.3 在线场景通过 ROCm 7.2 在单张 Radeon `gfx1100` 上接受了完整惯量张量。几何契约
不变：每指碰撞 geom 从 6 个增至 7 个，AABB 长轴从约 56 mm 增至 85 mm，生成 XML 包含 4 个
适配器 geom。生成 MJCF 的 SHA-256 为
`c1785752199e90c2631c3bff46eb6733545d35f707819686dec590c236e95e32`。
同步后的源码编译通过，远端全量 259 项测试全部通过。

预先规定的淘汰顺序是先跑已知失败的 `+40 mm` 机理抓取，再跑已知成功的 `+45 mm` 哨兵：

| 候选 | 轻量近似适配器 | 质量感知适配器 | 门禁 |
|---|---:|---:|---|
| `+40 mm` 机理抓取 | 完成，24.07 N | 完成，13.14 N | 通过 |
| `+45 mm` 成功哨兵 | 完成，12.55 N | 中止，38.34 N | 失败 |

哨兵回归精确复现：两次质量感知运行都在第 204 帧超过 35 N，峰值均为 38.3364 N。第 202 帧
实测力仍为 5.06 N；第 203 帧接触点由 8 个突增至 19 个，双侧支撑丢失，接触诊断报告 38.34 N
峰值。这是在当前仿真器中可复现的接触动力学分支变化，不能解释为“增加的质量直接产生了 38 N”。

## 决策

质量/惯量实现作为可复现、默认关闭的物理建模能力保留，但质量感知适配器不能晋级：它保留了原
恢复机理，却把成功哨兵回归成安全中止。停止规则取消计划中的 `7130001` 扩大组和任何新配对实验。
本轮不能写成鲁棒性或成功率实验。

下一项允许开展的工作是独立定义的接触模型调查，例如核查第 202--204 帧的手指执行器动力学与
碰撞对身份；不得围绕这个已观察哨兵调节延长量或密度。柔顺性、紧固件和实体力标定仍未建模。

## 复现

在赛事 Radeon 实例的项目根目录执行：

```bash
export PYTHONPATH="$PWD/src"
python scripts/probe_gripper_adapter_geometry.py \
  --backend rocm \
  --profile large_narrow_carton \
  --episode 4120001 \
  --extension-m 0.030 \
  --density-kg-m3 1240 \
  --output outputs/gripper-adapter-inertia-development-v2/geometry-probe.json

python scripts/diagnose_counterfactual_grasp_candidates.py \
  --config configs/catalog_v2.toml \
  --profile medium_carton \
  --episode 4120001 \
  --backend rocm \
  --candidate-id canonical-long-+0.000-up-0.045 \
  --contact-wrench-telemetry \
  --contact-wrench-backend cpu \
  --parcel-gripper-adapter \
  --parcel-gripper-extension-m 0.030 \
  --parcel-gripper-density-kg-m3 1240 \
  --output outputs/gripper-adapter-inertia-development-v2/4120001-canonical-45-adapter-mass-aware.json
```

其中 CPU 只用于微小的只读诊断评分；Genesis 仿真、接触求解和闭环任务仍通过 ROCm 在单张
Radeon 上执行。
