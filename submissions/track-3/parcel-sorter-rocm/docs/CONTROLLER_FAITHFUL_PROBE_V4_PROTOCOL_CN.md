# 控制器保真探针 V4：Train-only 可行性协议

## 目的与边界

V2 MLP 与 V3 保守记忆排序器以不同形式暴露了同一限制：28 个静态几何/状态特征不能可靠预测
后续接触动力学。V4 检验真实控制器微抬升中已经出现的动态信息，能否比静态几何基线更好地选择
候选。

这是 train-only 可行性研究。它只允许读取冻结的 32 个 V2 train 物理组和 192 条完整候选轨迹，
但特征必须在首次运输/放置动作前截止。V2 development 与 holdout 禁止输入。即使 V4 有策略通过，
也固定输出 `new_physics_authorized=false`；在线探针与新物理总体必须另写并冻结协议。

## 因果截断点

每条来源轨迹记录的是“执行当前命令之前”的状态。提取器包含第一次进入 `place` 阶段的那一行，
因为它是前一个 lift 命令产生的终端观测，然后拒绝所有后续行；提前 `abort` 也可作为边界。因此
探针只看到 approach、grasp、verify、lift 和抬升后边界状态，看不到运输、释放、最终成功或后续
受力事件。

测试强制两条防泄漏边界：

1. 修改边界后的力、相对位姿、接触或滑移字段，不得改变任何探针特征。
2. 交换候选的最终标签，不得改变策略选择的候选。

## 冻结特征契约

27 个特征都是物理摘要，不是学习嵌入：

- 完成、探针力中止、接触获得、终端接触和终端已抬升标志；
- 探针/verify/lift 帧数与接触获得延迟；
- approach、verify、lift、终端和整体受力统计；
- 包裹与末端抬升位移；
- 终端相对位姿漂移、最大相对步长与最大向下相对步长；
- 受载阶段接触保持比例。

排名键不包含最终成功、最终安全中止标签、完整时域峰值力、耗时、最终阶段或边界后轨迹。

## 硬资格与固定策略

候选只有同时满足微抬升完成、探针未超过未修改的 35 N、获得并保持接触、边界时包裹已抬起，
才有资格被执行。若全部不合格，规划器安全放弃，不会把静态首选作为隐藏回退继续执行。

比较四种固定、无拟合参数的顺序：

| 策略 | 通过硬资格后的顺序 |
| --- | --- |
| `veto-static` | 保持静态几何顺序 |
| `force-first` | 探针峰值力、向下运动、漂移、静态顺序 |
| `stability-first` | 向下步长、总相对步长、漂移、力、接触支持、静态顺序 |
| `support-first` | 接触保持、包裹抬升、漂移、力、静态顺序 |

这些方案分别表达“只做否决”和三种物理优先级，不根据已观察结果拟合阈值。

## 固定评测与门禁

32 个 train 组被确定性分为四个 profile 均衡折，每折每个 profile 恰好 2 组。策略本身不在折内
训练；分折用于暴露局部回归，避免总体改善掩盖集中失败。

策略必须覆盖完整物理组，任何 profile 和任何折都不得发生安全或成功回归，总体成功数不得下降，
且至少增加一次成功或减少一次安全中止，六候选选择器 P95 还必须低于 5 ms。安全放弃按任务失败
计数，因此不能通过全部拒绝来制造安全改善。

合格策略依次按安全中止少、成功多、放弃少、选中候选受力低、延迟低和固定名称排序。即使通过，
仍不授权 development 或 holdout。

## 复现顺序

协议提交存在后先运行审计：

```bash
cd /workspace/parcel-sorter-opt-v1
PYTHONPATH=src /opt/venv/bin/python \
  scripts/audit_controller_faithful_probe_protocol.py \
  --protocol configs/controller_faithful_probe_v4.toml \
  --output outputs/controller-probe-v4/protocol-audit.json
```

只有得到 `protocol_valid` 后才允许执行 train-only 评测：

```bash
PYTHONPATH=src /opt/venv/bin/python \
  scripts/evaluate_controller_faithful_probe.py \
  --manifest /workspace/parcel-sorter-opt-v1/outputs/grasp-scorer-v2/candidates/train/manifest.json \
  --protocol configs/controller_faithful_probe_v4.toml \
  --dataset-output outputs/controller-probe-v4/train-probe-dataset.json \
  --output outputs/controller-probe-v4/train-only-result.json
```

协议 SHA-256 为
`ca941366101c0a0d730a2628c442573347113e539c541778b617ba0619be4ff3`。
