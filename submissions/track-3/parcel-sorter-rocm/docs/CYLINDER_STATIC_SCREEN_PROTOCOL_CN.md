# 圆柱静态 IK/FK/碰撞筛查 V1 协议

## 目的

解析审计只证明候选存在。本协议检验这些候选在真实 Genesis Panda 模型上是否满足：

- IK 位置和旋转误差门；
- FK 位置复核；
- 机器人与包裹/桌面/自身的网格碰撞门；
- 每次临时设置关节状态后的精确恢复；
- 现有三组 IK seed 下的可行覆盖与计算时间。

筛查不执行控制动作、不推进物理、不闭合夹爪，也不读取成功、受力、掉落或放置结果。

## 冻结总体

来源是已冻结且通过的 128 样本解析总体。两个 profile 各取 12 个固定偏移：

```text
0, 5, 11, 17, 23, 29, 35, 41, 47, 53, 59, 63
```

因此共 24 个样本；选择键必须是源证据中的子集。立式命名空间从 `10100000` 开始，卧式从
`10200000` 开始。选择不读取 IK、碰撞或任务结果。

## 执行路径

每个样本构建一个启用 ROCm 的 Genesis 场景，但设置 `defer_initialization_settle=true`，不执行
初始化物理步。场景使用实际包裹位姿、专家按形状返回的手掌间隙和 `2 * open_width_m` 总夹爪
开口。圆柱生成器产生候选后，复用现有 `_evaluate_grasp_pose_candidate` 诊断接口执行完全相同的
IK、FK、碰撞、可操作度和状态恢复检查。

协议要求恰好一张可见 GPU 且 PyTorch HIP 版本非空。每个样本记录 PyTorch/HIP 版本、可见设备数、
Radeon 名称、GCN 架构和总显存；CPU 调用或断点续跑期间设备变化都会在汇总前被拒绝。

这里使用下划线接口是有意的诊断适配，不改变共享 `genesis_env.py`。协议绑定该文件哈希，任何
正式运行前的变化都会使入口拒绝执行。

## 预注册门禁

- 24 个样本全部完成；
- 两个 profile 各自至少 75% 样本有一个静态可行候选；
- 所有评估为有限数；
- 最大关节状态恢复误差不超过 `1e-7`；
- 不含场景构建的每样本候选筛查 P95 不超过 5,000 ms。

门禁故意不要求 100% 可行，因为这是候选开发屏幕，不是最终论文总体。若某 profile 低于 75%，
当前候选族不能进入物理执行，应在新的开发命名空间修改几何。若通过，只授权另行冻结少量物理
rollout，不直接接入运行时。

## 计时与输出

分别记录：

- `scene_build_ms`：Genesis 场景和资产构建；
- `screen_compute_ms`：候选生成、全部 seed 的 IK/FK/碰撞和排序；
- 每候选 `compute_ms`；
- profile 分层 P50/P95、最小/中位可行候选数和状态恢复误差。

每个样本独立落盘，manifest 在每个样本后原子更新。`--resume` 只接受同时匹配协议 SHA-256、
profile、episode、完成状态和重新计算样本 SHA-256 的文件。

## 运行顺序

V5 箱体独立确认结束前不启动，避免两个 Genesis 进程竞争同一张 Radeon。V5 结束后：

```bash
cd /workspace/parcel-sorter-opt-v1
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/run_cylinder_static_screen.py \
  --protocol configs/cylinder_static_screen_v1.toml \
  --output-dir outputs/cylinder-static-screen-v1 \
  --backend rocm \
  --resume
```

结果必须按冻结门解释；不能在看到可行率后修改 75%、误差或延迟阈值。

当前有效冻结协议 SHA-256：

```text
31f1b73df7df3b752c8c2b4266cfa249be4048123a4ecc41cf2d9146e21dbfc4
```

较早的执行前指纹 `a0497368...b6f728` 和 `e2777ccb...adcfeb` 都在任何筛查场景构建前被替代。
前者没有绑定 backend/HIP 证据；后者没有绑定配置解析器、随机化器、专家抓取间隙和能力门，也没有
把选中样本投影与无结果标签源审计逐项比较。当前 runner 会在构建场景前，对 24 个键的尺寸、质量、
摩擦、滚动摩擦、位置、yaw、姿态类别和初始位姿全部进行核对。两次重新冻结都没有观察可行性结果。

当前协议还绑定源审计 module 与 runner，并要求其哈希与源证据内部记录的实现指纹一致。
