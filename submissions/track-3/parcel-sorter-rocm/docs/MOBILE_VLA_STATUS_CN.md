# 移动双臂 VLA 状态（2026-07-26）

## 本轮完成

- 固定 43 维非特权状态：底盘位姿/速度、18 个关节、双末端位姿、双侧接触力和目标位姿。
- 固定 19 维动作：底盘 `vx/vy/vyaw`，左右臂各 `XYZ + 四元数 + 夹爪`。
- 在单张 `gfx1100` Radeon 上采集 30 帧 224x224 RGB-D 成功双臂预抓取轨迹。
- 将 LeRobot SmolVLA 的 `max_state_dim` 从默认 32 显式扩展到 48，并完成 43 到 19 维的一步
  前向、反向、优化器更新、checkpoint 保存、重载和推理。
- 新增移动三吸盘接触验证与有界弹簧阻尼吸附控制器。

## 证据边界

VLA 结果只是接口 smoke，不是有效微调。当前只有一个成功 episode，不能报告泛化成功率。三吸盘物理
抬升 v5 失败：动态接近在形成双杯密封前分叉并侧向推动包裹，因此不能宣称移动吸盘抓取成功。

下一步只做两件事：从已经验证的同步预抓取姿态生成稳定的笛卡尔接近；成功吸取、抬升和放置后，
记录多包裹、多质量、多摩擦轨迹，再启动正式 SmolVLA 微调与 Harness/失败回放消融。

## 可复现入口

```bash
python scripts/smoke_mobile_bimanual_arms_rocm.py --backend rocm --steps 240 \
  --hybrid-tools --record-dataset outputs/mobile-bimanual-dataset-v1/lerobot_dataset \
  --output outputs/mobile-bimanual-record-v1

MOBILE_SMOLVLA_STEPS=1 bash scripts/train_mobile_smolvla_rocm.sh \
  outputs/mobile-bimanual-dataset-v1/lerobot_dataset \
  outputs/train/mobile-smolvla-19d-smoke-v2
```

