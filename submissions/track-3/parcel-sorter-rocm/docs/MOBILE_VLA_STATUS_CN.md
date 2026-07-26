# 移动双臂 VLA 状态（2026-07-26）

## 本轮完成

- 固定 43 维非特权状态：底盘位姿/速度、18 个关节、双末端位姿、双侧接触力和目标位姿。
- 固定 19 维动作：底盘 `vx/vy/vyaw`，左右臂各 `XYZ + 四元数 + 夹爪`。
- 在单张 `gfx1100` Radeon 上采集 30 帧 224x224 RGB-D 成功双臂预抓取轨迹。
- 将 LeRobot SmolVLA 的 `max_state_dim` 从默认 32 显式扩展到 48，并完成 43 到 19 维的一步
  前向、反向、优化器更新、checkpoint 保存、重载和推理。
- 新增移动三吸盘接触验证与有界弹簧阻尼吸附控制器。
- v40 在单张 Radeon 上形成两个吸盘密封，锁定 0.4 kg 包裹并物理抬升 0.0811 m；吸附力
  峰值 10.10 N，物理杯面接触峰值 2.37 N，均低于 35 N。

## 证据边界

VLA 结果仍只是接口 smoke，不是有效微调，不能报告泛化成功率。v40 已证明移动吸盘抓取和抬升，
但尚未完成底盘携物运输、分类放置和释放，因此不能宣称完整移动分拣成功。早期 v5 失败继续保留为
负结果，用于解释碰撞几何、接近目标和连续 IK 的修正过程。

下一步先完成底盘携物运输与分类释放，再记录多包裹、多质量、多摩擦轨迹，启动正式 SmolVLA
微调与 Harness/失败回放消融。

## 可复现入口

```bash
python scripts/smoke_mobile_bimanual_arms_rocm.py --backend rocm --steps 240 \
  --hybrid-tools --record-dataset outputs/mobile-bimanual-dataset-v1/lerobot_dataset \
  --output outputs/mobile-bimanual-record-v1

MOBILE_SMOLVLA_STEPS=1 bash scripts/train_mobile_smolvla_rocm.sh \
  outputs/mobile-bimanual-dataset-v1/lerobot_dataset \
  outputs/train/mobile-smolvla-19d-smoke-v2
```
