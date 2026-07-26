# Slow-Fast SmolVLA Result / 快慢速 SmolVLA 结果

## 中文

### 决策

采用“慢速 VLA + 快速安全控制”结构，而不是继续增加 SmolVLA 训练步数。SmolVLA 每 3 个控制帧读取 RGB、机器人状态和任务文本，输出笛卡尔位置建议；30 Hz 专家控制器每帧执行，将 VLA 修正限制在 0.01 m 内，并继续负责腕姿态、夹爪、接触反馈、重试和 35 N 安全中止。

选择该结构的原因是：原始 10k SmolVLA 已证明能够完成一个未见小纸箱回合，但五类固定筛选仅为 1/5；继续训练到 12k/14k 反而退化。VLA 适合提供低频视觉语言修正，确定性控制器更适合处理高速接触与安全约束。

### Radeon 验证结果

固定样本为 `small_carton` episode `1000001`，候选与原始 10k SmolVLA 使用同一检查点和环境。

| 指标 | 原始 10k SmolVLA | 快慢速候选 |
|---|---:|---:|
| 成功 | 1/1 | 1/1 |
| 完成时间 | 5.37 s | 5.67 s |
| 峰值接触力 | 12.87 N | 9.21 N |
| 平均策略延迟 | 55.49 ms | 18.50 ms |
| P95 策略延迟 | 405.98 ms | 201.46 ms |
| VLA / 快速控制更新 | 每帧调用适配器 | 57 / 171 |

运行环境为单张 AMD Radeon `gfx1100`（51,522,830,336 bytes VRAM）、ROCm 7.2、PyTorch 2.9.1 ROCm 和 Genesis 1.2.3。VLA 最大应用残差达到 0.01 m，证明模型实际参与动作生成，而非仅作为旁路展示。

该结果是架构方向验证，不是五类包裹的正式泛化结论。下一步只需在冻结的五类未见回合上做匹配评估；若某类失败，保留失败证据，不再根据留出结果调参。

### 复现

```bash
PYTHONPATH=src /workspace/rdna/bin/python scripts/evaluate_act.py \
  --checkpoint outputs/train/smolvla-strict-open-20k-seed11-v1/checkpoints/010000/pretrained_model \
  --config configs/catalog_v2.toml --backend rocm \
  --episodes 1 --start-episode 1 --profile small_carton \
  --output outputs/eval-smolvla-10k-slow-fast-small-carton-v1 \
  --slow-fast-vla --vla-refresh-steps 3 --vla-residual-limit-m 0.01
```

## English

### Decision

Use a slow VLA inside a fast safety controller instead of adding more SmolVLA training steps. SmolVLA consumes RGB, robot state, and task text every three control frames. The 30 Hz expert runs every frame, limits the VLA Cartesian correction to 0.01 m, and retains wrist, gripper, contact, retry, and 35 N abort authority.

This follows the evidence: the original 10k SmolVLA completed one unseen small-carton episode, but scored only 1/5 in the fixed five-profile screen; 12k and 14k regressed. A VLA is useful for slow visual-language correction, while deterministic control is better suited to fast contact and safety constraints.

### Radeon result

The matched `small_carton` episode `1000001` succeeded in 5.67 s with 9.21 N peak force, versus 5.37 s and 12.87 N for the raw 10k SmolVLA. Mean policy latency fell from 55.49 ms to 18.50 ms and P95 from 405.98 ms to 201.46 ms. The candidate performed 57 VLA updates and 171 fast control steps. Its applied residual reached the configured 0.01 m limit, so the VLA materially participated in action generation.

The run used one AMD Radeon `gfx1100`, ROCm 7.2, ROCm PyTorch 2.9.1, and Genesis 1.2.3. This is an architecture-direction result, not a five-profile generalization claim. The next valid step is one matched evaluation on each frozen unseen profile without tuning on holdout outcomes.
