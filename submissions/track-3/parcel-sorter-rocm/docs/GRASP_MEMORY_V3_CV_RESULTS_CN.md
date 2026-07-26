# 保守抓取记忆 V3：Train-only CV 结果

## 结论边界

这是一次负面的 train-only 折外可行性结果。它没有读取 V2 development 或任何 holdout 数据，
不是独立泛化成绩，也不授权新的物理执行。冻结协议见
`GRASP_MEMORY_V3_CV_PROTOCOL_CN.md`。

## 执行与完整性

冻结的 V2 train 数据包含 32 个物理组，四个包裹 profile 各 8 组，每组 6 个候选，共 192 次
已记录 rollout。四个确定性折保持物理组完整，并在每折放入每个 profile 的 2 组。协议审计返回
`protocol_valid`，同时验证 development 与 holdout 输入均被禁止。

交叉验证使用单张 `gfx1100` AMD Radeon、PyTorch 2.9.1 和 HIP 7.2。PyTorch 把 ROCm 兼容设备
报告为 `cuda`，但运行记录中的实际硬件是 `AMD Radeon Graphics`。

| 产物 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `grasp-memory-v3-train-only-cv.json` | 998,070 | `3ec39a321f88ac775340a40a57f74c2d6f17ffc51ee70450916d9ec15f168d68` |
| `grasp-memory-v3-cv-protocol-audit.json` | 2,553 | `c8058dfb7bdebbd2e210eeeb65e83837d8b4014d846447fff135951f88eeae8b` |

协议 SHA-256 为
`80911bf25a2642fe0b099ab27d22fbd8e04ffdc40bc91434aa465405e4893b02`；来源数据集 SHA-256 为
`71761164467ba3b29866d87639b73474a5d5f2cc1fdb8907d62957a6c73703d5`。

## 结果

折外静态基线为 7/32 成功、17/32 安全中止。六个预注册记忆式配置全部未通过。

| 候选 | 成功 | 安全中止 | 改选次数 | Warm P95 | 门禁结论 |
| --- | ---: | ---: | ---: | ---: | --- |
| `knn-k3-r3-q90` | 7 | 17 | 0 | 0.534 ms | 无任务或安全改善 |
| `knn-k5-r3-q90` | 7 | 17 | 1 | 0.540 ms | 无任务或安全改善 |
| `knn-k5-r6-q90` | 7 | 17 | 2 | 0.552 ms | 某折安全回归，且无净改善 |
| `knn-k5-r6-q95` | 7 | 17 | 2 | 0.542 ms | 某折安全回归，且无净改善 |
| `knn-k9-r6-q95` | 7 | 17 | 0 | 0.555 ms | 无任务或安全改善 |
| `knn-k9-r15-q95` | 7 | 18 | 1 | 0.552 ms | profile/折安全回归，且无净改善 |

全部延迟都远低于冻结的 5 ms 上限，因此失败原因不是 Radeon 推理延迟。保守拒绝大多复现静态
基线，少数改选也没有带来任务或安全净收益。

## 决策

固定选择器输出：

```text
status=no_cv_candidate
selected=null
new_physics_authorized=false
```

不为这条静态特征记忆排序路线采集 V3 学习总体，不打开 holdout，运行时继续使用静态几何基线。
不得复用已有 V2 development 去修改这些阈值或再选另一种静态 28 特征模型。

下一条允许研究的路线必须增加静态候选描述中没有的信息，例如另行预注册的短时预抓取或微抬升
物理探针，并加入接触/滑移状态。把多个短时域 rollout 在 Radeon 上批量并行是合理的 ROCm 优化
目标，但在新的总体、安全停止、比较方法与 holdout 边界冻结前，它仍只是提案。

紧凑机器可读决策见 `evidence/training/grasp-memory-v3-cv-evidence.json`。
