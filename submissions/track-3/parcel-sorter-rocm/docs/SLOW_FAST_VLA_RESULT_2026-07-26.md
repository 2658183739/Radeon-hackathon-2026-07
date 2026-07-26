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

## 五类扩展与失败分析 / Five-Profile Expansion and Failure Analysis

### 第一轮五类筛选 / First five-profile screen

原始 10k SmolVLA 在 local episode `1` 的五类结果为 `1/5`，最大接触力 50.89 N。加入慢速 VLA、快速安全控制、碰撞检查复位和形状感知抓取规划后，同一组样本达到 `3/5`，最大力降至 11.36 N：`small_carton`、`medium_carton` 和 `upright_canister` 成功；`flat_mailer` 抓取验证失败；`mailing_tube` 零接触停在接近阶段。

The raw 10k SmolVLA scored `1/5` on local episode `1`, with 50.89 N maximum force. The complete slow-fast stack scored `3/5` on the same samples and reduced maximum force to 11.36 N. Small carton, medium carton, and upright canister succeeded; the flat mailer failed grasp verification and the mailing tube remained in approach.

### 两项因果修复 / Two causal fixes

1. **横放邮筒路径迟滞。** VLA 残差先被投影到碰撞验证过的专家运动方向，随后给“升高 -> 原地对腕 -> 平移下降”加入状态迟滞。对腕开始后，即使 IK 产生几毫米位置漂移，也不会退回升高阶段。开发样本 `9000001` 从零接触超时变为首次尝试成功：9.60 s，峰值 10.98 N。
2. **扁平件夹持。** 新开发样本 `2000002` 在默认 20 N 指令下已经抓起，但搬运时升至 37.90 N 并触发安全门。只把 `flat_mailer` 设置为摩擦系数 2.0 的软指面和每指 12 N 力限后，同一样本 4.30 s 完成，峰值 3.68 N。全局 35 N 中止保持不变。

1. **Horizontal-tube path hysteresis.** The VLA residual is projected onto the collision-validated expert motion axis. The raise-align-translate sequence then latches the safe wrist-alignment pose, so millimetre-scale IK drift cannot return it to the raise phase. Development episode `9000001` changed from a zero-contact timeout to first-attempt success in 9.60 s at 10.98 N.
2. **Flat-mailer grip.** New development episode `2000002` was lifted under the default 20 N command but reached the 37.90 N safety abort during transport. A profile-specific friction-2.0 soft fingertip and 12 N per-finger limit changed the matched episode to success in 4.30 s at 3.68 N. The global 35 N abort was not changed.

### 不重叠确认 / Disjoint confirmation

修复冻结后，local episode `3` 的五类不重叠确认得到 `2/5`：小纸箱和扁平件成功；中纸箱与直立罐体零接触超时；邮筒在 64.67 N 中止。因此开发样本上的 4/5 不能作为泛化结论。确认集不再用于调参，原始失败轨迹保留在 `evidence/vla/smolvla-10k-slow-fast-five-profile-confirmation-v1-summary.json`。

After freezing the fixes, the disjoint local episode `3` confirmation scored `2/5`: small carton and flat mailer succeeded, medium carton and upright canister timed out without contact, and the mailing tube aborted at 64.67 N. The development-set 4/5 result therefore does not establish generalization. The confirmation set is closed to further tuning and its raw failure traces are retained.

### 下一实验 / Next experiment

轨迹进一步证明 VLA 的反向残差有时会完全抵消约 1 cm 的专家推进。候选现在要求每帧至少保留 50% 专家进度；新开发样本中 `medium_carton` 成功，但 `upright_canister` 仍在 36.37 N 中止。下一轮必须使用新的开发 episode 建立按形状分层的路径/接触数据，至少每类 10 个开发样本；冻结后再用完全不重叠样本确认。论文级声明至少需要多 seed、置信区间以及原始 VLA、纯专家、无投影残差、无迟滞、无薄件力限的配对消融。

The VLA residual could also cancel the expert's roughly 1 cm progress. The candidate now preserves at least 50% of expert progress per frame. A new medium-carton development episode succeeded, while an upright canister still aborted at 36.37 N. The next phase needs shape-stratified path/contact data on at least ten new development episodes per profile, followed by a fully disjoint confirmation. A paper-level claim also requires multiple seeds, confidence intervals, and paired ablations against raw VLA, pure expert, unprojected residuals, no wrist hysteresis, and no flat-mailer force profile.
