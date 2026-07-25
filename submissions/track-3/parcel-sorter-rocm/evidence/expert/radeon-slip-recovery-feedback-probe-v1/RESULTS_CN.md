# 反馈式滑移恢复机理探针

## 证据边界

本轮只使用一个已经观察过的开发回合来检验物理机制，不是独立成功率样本，也没有打开预留确认集。
对照为运输契约调查中采用反馈限速的 `4120001 medium_carton` 轨迹。

两次执行均使用单张 `gfx1100` Radeon、ROCm 7.2、Genesis 1.2.3、stock Panda 平行夹爪和未改变的
35 N 实测力中止线。候选通过关闭有界前瞻恢复实测位姿反馈运输；唯一新增的主动机制是冻结的滑移
检测和夹力响应。

## 冻结机制

- 仅在带载 `raise` 或 `transfer` 阶段检测；
- 单帧相对位移至少 8 mm；
- 纸箱相对夹爪向下移动至少 6 mm；
- 实测接触力至少 1 N，且与目标料箱的水平距离至少 80 mm；
- 夹紧命令从 20 N 提升到 22 N，持续 15 个控制帧；
- 命令目标相对固定 35 N 中止线至少保留 10 N 余量。

命令夹力余量是配置不变量，并不表示刚体动力学下的实测接触力绝不会过冲；最终安全判断仍以物理
探针为准。

## 结果

| 指标 | 反馈基线 | 滑移恢复 |
| --- | ---: | ---: |
| 任务成功 | 否 | 否 |
| 终态 | 一次重试后的接近阶段 | 一次重试后的接近阶段 |
| 时长 | 19.97 s | 19.97 s |
| 实测接触力峰值 | 21.81 N | 22.92 N |
| 首次失去双指接触 | 第 159 帧 | 第 159 帧 |
| 最终失去接触 | 第 260 帧 | 第 261 帧 |
| 恢复触发 | 不适用 | 第 159、261 帧 |
| 增力命令帧数 | 不适用 | 30 |

第一次触发精确复现了冻结的第 159 帧信号：相对位移 12.56 mm、向下分量 10.95 mm、接触力
16.52 N、目标距离 337.90 mm。22 N 命令使下一帧实测峰值达到 22.92 N，并短暂恢复双指接触。

该响应没有稳定负载。纸箱继续下沉，到第 250 帧已不再满足「已抬升」判定，并在第 261 帧失去接触。
此时距离目标仍有 167.93 mm，第二次信号仍满足规则，但双指接触已经消失；纸箱离开夹爪后，单纯
增加闭合力无法重新捕获。相对反馈基线，机制只把最终失去接触推迟一帧，没有改变任务结果或时长。

## 决策

拒绝升级，代码只作为默认关闭的负对照保留。主探针失败，因此按预注册门禁取消两个成功哨兵、阈值
扫描、夹力扫描、重复和新 episode 验证；35 N 中止线保持不变。

只有在机制改变捕获几何或恢复状态时才重新评估，例如使用许可证明确的加长夹指/托架资产、增加
安全放回后重抓状态，或换用能够建立更深抓取的夹具。当前轨迹不支持继续增加夹力。

## 复现

```bash
source scripts/activate_radeon_env.sh
PYTHONPATH=src python scripts/run_expert.py \
  --config configs/catalog_v2.toml \
  --backend rocm \
  --episodes 1 \
  --start-episode 120001 \
  --profile medium_carton \
  --output outputs/radeon-slip-recovery-probe-v2/4120001-feedback \
  --collision-checked-reset \
  --geometry-aware-grasp-planning \
  --grasp-planning-reset-fallback-gate \
  --grasp-planning-transport-contract \
  --grasp-planning-disable-transport-lookahead \
  --grasp-planning-raise-step 0.02 \
  --grasp-planning-transport-step 0.01 \
  --grasp-planning-transfer-settle-steps 2 \
  --transport-slip-recovery
```

紧凑 JSON 保留完整安全汇总，并记录被省略完整轨迹的哈希；`TRACE-COMPARISON.json` 保存固定的
对照数值和源哈希。含逐帧轨迹的完整 summary 继续保存在 Radeon 工作区。
