# 控制器保真探针 V4：Train-only 结果

## 结论边界

这是冻结 V2 train 总体上的正向安全可行性结果，不是独立 development 或 holdout 结果，没有增加
任务成功数，也不授权部署或新物理。它唯一允许的“晋级”是：为选中的机理另写并冻结完全不重叠的
新总体协议。

## 完整性与执行

评测器先核对冻结的 32 组 train manifest 与全部 32 份来源哈希，再提取 192 行候选。每个特征都在
首次 `place` 动作前边界或更早的 abort 截止。协议审计返回 `protocol_valid`，development 与
holdout 均被禁止。

来源 rollout 由单张 AMD Radeon 通过 ROCm 执行 Genesis 控制器保真路径。当前离线可行性选择器
只是主机控制逻辑，不声称 GPU 模型推理；在线 Radeon 并行探针仍属于后续工作。

| 产物 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `controller-probe-v4-protocol-audit.json` | 912 | `5bd01a17c7422592a6dfec4f9fe1b275796cd0f91d3f4f14c2ee9e43f6a7ef6e` |
| `controller-probe-v4-train-dataset.json` | 746,998 | `8b2324a6e86395a59b3997d600631264fd83e078077fce650d81c4e85d1ac72a` |
| `controller-probe-v4-train-result.json` | 1,723,556 | `3df57dafab079204afa5ec0fe5366fd1ae04d0844219c48c967ebb9c4e5bba16` |

协议 SHA-256 为
`ca941366101c0a0d730a2628c442573347113e539c541778b617ba0619be4ff3`。

## 结果

train 静态基线为 7/32 成功、17/32 力中止。

| 策略 | 成功 | 力中止 | 安全放弃 | 改选 | 选择器 P95 | 门禁 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `veto-static` | 7 | 13 | 4 | 5 | 0.006 ms | 通过 |
| `force-first` | 6 | 12 | 4 | 26 | 0.007 ms | 拒绝：总体/profile/折回归 |
| `stability-first` | 5 | 11 | 4 | 16 | 0.008 ms | 拒绝：总体/profile/折成功回归 |
| `support-first` | 7 | 12 | 4 | 31 | 0.008 ms | 拒绝：profile/折成功回归 |

`veto-static` 保留静态基线的全部 7 次成功，并减少 4 次力中止，任一 profile 与任一折都没有安全或
成功回归。四次减少全部来自安全放弃：一个 `medium_carton` 和三个 `near_limit_box` 的静态首选
后来都会力中止。第五次改变发生在一个 `large_narrow_carton`：探针选择唯一合格候选，但它与静态
首选都是安全任务失败。

三个主动重排策略形成了重要负对照：更低探针力、更小漂移或更强早期接触支持，都不能单独预测完整
运输成功；它们在不同组之间频繁交换增益与损失，因此未通过冻结回归门禁。

## 决策

固定选择器输出：

```text
status=probe_candidate_found
selected=veto-static
new_physics_authorized=false
holdout_opened=false
```

选中的机理是动态安全否决器，不是新的成功排序器。当前运行时继续使用静态几何基线。下一步只允许
冻结一个完全不重叠、覆盖更广包裹的新总体，并让 `veto-static` 与静态基线做一次确认评测。V2
development 与 holdout 继续关闭，不能用于这项确认。

紧凑机器可读索引见 `evidence/training/controller-probe-v4-train-evidence.json`。
