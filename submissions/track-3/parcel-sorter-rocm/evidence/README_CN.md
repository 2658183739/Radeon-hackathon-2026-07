# Radeon 原始证据索引

本目录保存从单张 Radeon 实测环境复制的小体积原始结果，以及成对记录命令和产物哈希的
证据说明。它们用于审计 README 和技术报告中的数字，不替代完整数据集和模型权重。

| 文件 | 内容 |
| --- | --- |
| `mobile_bimanual/mobile-suction-lift-v40-success.json` | 单张 Radeon 双杯密封与 8.11 cm 物理抬升原始结果 |
| `mobile_bimanual/mobile-suction-lift-v40-success.log` | 成功抬升的 Genesis/ROCm 运行日志 |
| `mobile_bimanual/mobile-suction-transport-v41-success.json` | 抓取、30 cm 运输、放置和释放的完整回合 |
| `mobile_bimanual/mobile-suction-transport-v41-success.log` | 完整移动回合的 Genesis/ROCm 运行日志 |
| `expert/randomized-120-summary.json` | 正式 120 回合随机专家结果 |
| `expert/fixed-10-summary.json` | 固定种子专家回归基线 |
| `expert/final-approach-001-120-summary.json` | 被拒绝的 0.01 m 候选，同组 120 回合 |
| `expert/final-approach-001-comparison.json` | 基线/候选逐回合比较与验收决策 |
| `expert/radeon-dataset-400-v2-failure-analysis.json` | Radeon 400 次专家尝试的轨迹级失败归因 |
| `act/checkpoint-4000-episodes-10-19.json` | ACT 4000 步闭环评估 |
| `act/checkpoint-5000-episodes-10-19.json` | ACT 5000 步同种子评估 |
| `training/act-5000-amp-b32.log` | 正式 5000 步训练日志 |
| `training/act-model-sweep-smoke-5k-v2.json` | 六单元 ACT RGB/RGB-D 5000 步集成 smoke 清单和 checkpoint 哈希 |
| `training/act-model-sweep-smoke-5k-v2-status.csv` | 六单元机器可读状态表，所有 status 均为 0 |
| `expert/radeon-reset-ab-v1-comparison.json` | 匹配 Radeon reset A/B；候选 C 未通过任务/安全门禁 |
| `expert/radeon-reset-ab-v1-baseline-summary.json` | 20 回合基线 compact summary；原始 trace 保留在云端 |
| `expert/radeon-reset-ab-v1-candidate-c-summary.json` | 20 回合候选 C compact summary；原始 trace 保留在云端 |
| `expert/radeon-reset-ab-v1-run.log` | Radeon 预检、Genesis 运行日志和 summary 后退出诊断 |
| `expert/radeon-reset-ab-v1-SHA256SUMS` | reset A/B 证据哈希清单 |
| `expert/radeon-size-aware-ab-v1-comparison.json` | 匹配 Radeon 尺寸感知横移 A/B；20 mm 裕量候选被拒绝 | `c21b9f33b584e882a133d68f09dfaebd42671c3d60ce54ceddc20e8222cda12f` |
| `expert/radeon-size-aware-ab-v1-baseline-summary.json` | 尺寸感知对照实验的 20 回合基线 compact summary | `82cce9c23f755fc95c998810f40e53ea9fb2c337d12304f92307f06db2db17e6` |
| `expert/radeon-size-aware-ab-v1-candidate-size-aware-summary.json` | 被拒绝的尺寸感知候选 compact summary；原始 trace 保留在云端 | `e9711e6225df1207a427c792d8ba6d47fd1f929b0ab1d5ca7663a5a6e2f8c26f` |
| `expert/radeon-size-aware-ab-v1-baseline-failure-analysis.json` | 匹配 20 回合基线的轨迹级失败归因 | `7f478ea03a6ba0e6859afb5496aba5eed4614be7cc087b4bdb66ff19e9e8daa4` |
| `expert/radeon-size-aware-ab-v1-candidate-failure-analysis.json` | 候选失败归因和重试回归证据 | `03e133f66884a776616d694b66899522529a3b7d9d1c06e811cc8d34b927ae7f` |
| `expert/radeon-size-aware-ab-v1-candidate.log` | 候选 Radeon Genesis 日志、最终 summary 和运行警告 | `2e9a5a57dd66af12020dae7f083e6be21ecfb5804fda24594cb5c1cccf1ad8ac` |
| `expert/radeon-size-aware-ab-v1-SHA256SUMS` | 尺寸感知负对照证据哈希清单 | N/A |
| `expert/radeon-retry-retreat-ab-v1-comparison.json` | 匹配 Radeon 恢复感知重试 A/B；方向有改善但未通过绝对安全/任务门禁 | `47cfd58a09e344db8c60751167e5504285d82f27276249e00d26dd07df9efec2` |
| `expert/radeon-retry-retreat-ab-v1-baseline-summary.json` | 恢复重试对照实验的 20 回合基线 compact summary | `ae38f67d6665a18b1bad46cc38f1244b5189ed55011343077f9f16f6b76c9d1b` |
| `expert/radeon-retry-retreat-ab-v1-candidate-summary.json` | 恢复感知重试候选 compact summary；尚未设为默认 | `cd4103caf414687eee3c44e44933b9a4c164f46edc7ab05e730197164cecfeb3` |
| `expert/radeon-retry-retreat-ab-v1-baseline-failure-analysis.json` | 基线轨迹级失败归因 | `b468064bdbd200e5b021cddda98856e9124c01a5033ae8c807850a5d5fcd99e6` |
| `expert/radeon-retry-retreat-ab-v1-candidate-failure-analysis.json` | 候选重试和力指标轨迹归因 | `36a826c40de6d3743f0fdc4e50eb9302478a9068ac8194d33b0b3ed9b0dcf10f` |
| `expert/radeon-retry-retreat-ab-v1-SHA256SUMS` | 恢复感知重试实验哈希清单 | N/A |
| `expert/radeon-approach-step-ab-v1-baseline-summary.json` | 40 mm 接近步长基线的压缩 summary | `40274f8e6149a8aeb26129933c47aba2e43c84679e30be3f75dafd5c85125d89` |
| `expert/radeon-approach-step-ab-v1-candidate-summary.json` | 被拒绝的 20 mm 接近步长压缩 summary | `ed7f367eac7e16def48d4198088179836a6e60323b16e2aa30033b63f6a3e489` |
| `expert/radeon-approach-step-ab-v1-comparison.json` | 匹配 A/B 比较和验收门禁 | `1e7a66633d4b4b1bb2ebae3eb33753bd634c25b361acb631342ccd29b299e52b` |
| `expert/radeon-approach-step-ab-v1-baseline-failure-analysis.json` | 基线轨迹级失败归因 | `d9b237a79e0c3adcb0c799481df6bac9a74b0bef04935f4cde0d7b1b95b3a568` |
| `expert/radeon-approach-step-ab-v1-candidate-failure-analysis.json` | 候选轨迹级失败归因 | `2fa7f0a7a4a674855199e152b5f6de2e06e1e16d588a5f4ce4806d7015622c34` |
| `expert/radeon-approach-step-ab-v1-SHA256SUMS` | 本地压缩产物哈希清单 | N/A |
| `expert/radeon-approach-step-ab-v1-remote-SHA256SUMS` | Radeon 远端完整 summary 与运行产物哈希清单 | `9651fd81e8e65609d6e3fc222a6fb94101cf4dd7d407b35f381f6084648c7b39` |
| `benchmarks/parallel-radeon.json` | 1/16/64/128 环境仿真扫描 |
| `benchmarks/act-training-*.log` | FP32/AMP 与 batch 吞吐测试 |
| `catalog/catalog-v1-submit-smoke.json` | 最终 20 秒、7 类 profile 目录回归烟雾 |
| `catalog/catalog-v2-baseline.json` | 12 类确定性基线烟雾 |
| `catalog/catalog-v2-rolling-scoped.json` | 限定滚动摩擦作用域后的完整目录回归 |
| `catalog/README_CN.md` | catalog v2 候选矩阵、哈希与保留/拒绝结论 |
| `training/diffusion-1-step-rocm.md` | Diffusion 单步 Radeon 训练链路记录 |
| `training/diffusion-compact-1step-rocm.md` | 轻量 76.6M 参数 Diffusion 单步与检查点哈希 |
| `multimodal/README_CN.md` | 历史深度拒绝、修正传感器审计和 RGB-D ACT 烟雾 |

SHA-256 见英文 [README.md](README.md)。JSON 包含配置、运行版本、episode 随机参数、
终止结果和指标。历史 96 回合数据的深度尺度无效，只能用于 RGB/状态；大型数据、206 MB
模型权重、优化器状态和 MP4 不进入普通 Git，
最终提交时应通过 release 或对象存储提供，并公布 SHA-256。

失败候选也被保留，因为可复现性不仅覆盖成功结果；comparison 明确记录了为什么不能
把它设为默认值。

400 次尝试的失败分析由远端带完整轨迹的 summary 派生；产物内部记录了源路径、字节数和
SHA-256。为控制仓库体积，它保留逐失败回合归因与聚合统计，不复制每一帧原始轨迹。
其中各因素对比只是描述性证据，不能解释为因果效应。该文件自身 SHA-256 为
`12aae22a747759f96edb3a742e17cc6ba54c90480448198bd93f4153eecd7993`。

目录烟雾同样只是小体积回归证据：4 个盒类完成，3 个困难 profile 失败，不构成正式成功率。
其 SHA-256 记录在 `evidence/catalog/README_CN.md`。

Catalog v2 同样只记录每类一个确定性回合以及同 episode 的物理/控制候选，不能合并为
正式成功率。准确结果和哈希见 `catalog/README_CN.md`。

## 接近接触制动负对照

`expert/radeon-contact-brake-ab-v1-*` 保存 20 回合匹配 Radeon A/B 的 compact summary、失败
归因、日志、comparison 和两级哈希清单。候选只改变 20 N 接触制动阈值；结果与基线同为
1/20 成功、12/20 力中止、0 次掉落，峰值力从 111.28 N 增至 467.31 N，因此默认关闭。
核心本地哈希为：baseline summary `e79de0fd...3ce30`、candidate summary
`b35298cf...4e11d`、comparison `5b8ead9a...40290`。完整值见
`expert/radeon-contact-brake-ab-v1-SHA256SUMS`，远端原始 summary 哈希见
`expert/radeon-contact-brake-ab-v1-remote-SHA256SUMS`。

## 碰撞前 AABB 过滤器负对照

`expert/radeon-approach-aabb-ab-v1-*` 保存匹配 20 回合 Radeon A/B 的 compact summary、
失败归因、两侧日志、comparison 和本地/远端哈希清单。唯一配置变化是
`control.precontact_aabb_guard_distance_m=0.040`。候选在 6,003 个接近采样中触发 65 次，
AABB 同步测量平均 1.625 ms，但结果为 0/20 成功、12/20 力中止；基线为 1/20、12/20。
候选使 `7000005` 回归、增加 1 次接近超时且吞吐为 0，因此继续关闭。

本地 compact 核心哈希为 baseline summary `cc8e2967...d1ef6d`、candidate summary
`0d5ead5f...654f7c`、comparison `5554bd40...de136`。完整值见
`expert/radeon-approach-aabb-ab-v1-SHA256SUMS`；远端清单记录带完整轨迹的源 summary、
comparison、分析和日志。compact episode 会保留 AABB 安全聚合，并明确标注省略逐帧轨迹。

## 竖直屏障恢复负对照

`expert/radeon-approach-barrier-ab-v1-*` 保存 20 回合匹配 Radeon A/B 的压缩 summary、失败归因、日志、comparison 和两级哈希清单。候选只设置 `control.approach_barrier_recovery_step_m=0.120`；它为 0/20 成功、12/20 力中止，基线为 1/20、12/20，候选吞吐为 0，因此默认关闭。核心本地哈希为 baseline summary `5154a5d2...841b3a`、candidate summary `98196889...593c49`、comparison `172236b9...01e886`。完整值见 `expert/radeon-approach-barrier-ab-v1-SHA256SUMS`，远端原始 summary 哈希见 `expert/radeon-approach-barrier-ab-v1-remote-SHA256SUMS`。

## 接近顺应刚度负对照

`expert/radeon-approach-compliance-ab-v1-*` 保存匹配 20 回合、单张 Radeon A/B 的 compact
summary、轨迹派生失败归因、两侧日志、精确 comparison 和本地/远端 SHA-256 清单。唯一配置变化为
`control.approach_stiffness_scale` 从基线 1.0 改为 0.50；机械臂 Kv 使用 `sqrt(scale)`，夹爪增益
保持不变。

两组均为 1/20 成功、0 次掉落和 111.28 N 最大接触力。候选把力中止从 12 次降为 10 次，把逐回合
峰值力 P95 从 98.12 N 降为 71.07 N，但接近超时从 7 次增为 9 次，吞吐只保留 0.751 倍。它没有
恢复任何回合，并且未通过绝对成功率、力中止率和吞吐门禁，因此默认值继续为 1.0。

本地 compact 核心哈希为 baseline summary `e552b842...24805f`、candidate summary
`84f2a585...4749f`、comparison `e47f2573...0be61`。完整值见
`expert/radeon-approach-compliance-ab-v1-SHA256SUMS`；远端清单保留 6.9 MB 与 9.1 MB 完整轨迹
summary 及全部派生产物的来源哈希。

## 操作空间速度控制负对照

`expert/radeon-approach-velocity-ab-v1-*` 保存固定 20 回合、单张 Radeon 的匹配 A/B，唯一
配置差异是 `control.approach_velocity_control_enabled`。候选在 `MOVE_PREGRASP` 使用 Genesis
末端 Jacobian 与有界加权阻尼最小二乘；抓取、抬升和放置仍使用原 IK 位置控制。

基线为 1/20 成功、12/20 力中止、0 掉落；候选为 0/20 成功、13/20 力中止、0 掉落和 0 成功
吞吐，并使 `7000005` 回归。逐回合峰值力 P95 从 98.12 N 降到 67.55 N，但最大力仍为 111.28 N，
因此候选未通过任务、安全和吞吐门禁，继续默认关闭。

候选在 ROCm 上执行 5,727 次速度控制采样，同步控制计算平均 1.983 ms；最大关节命令 1.50 rad/s，
最大位姿误差 0.1817 m。本地 compact 哈希见
`expert/radeon-approach-velocity-ab-v1-SHA256SUMS`，两份远端清单分别保留完整轨迹来源与 compact
产物的哈希来源链。

## 碰撞检查复位诊断与负对照

`expert/radeon-contact-link-diagnostic-v1-*` 保存 link 级、240 Hz 初始化证据。失败回合
`7000001` 在第 0 个物理子步就发生 hand/纸箱碰撞，接触力约 1,270.85 N；成功回合
`7000005` 没有初始化接触，之后只有夹指接触，峰值为 17.12 N。该证据说明：部分随机纸箱在
30 Hz 控制器开始动作前，已经与历史 reset 几何相交。

`expert/radeon-collision-checked-reset-ab-v1-*` 保存据此构造的固定 20 回合、单张 Radeon A/B。
候选在物理积分前调用 Genesis 碰撞查询，仅在机器人/纸箱已经相交时切换到固定后备姿态。
20 个回合全部检查，其中 14 个触发后备姿态；初始共检测到 86 个几何对，每次切换后复查均为
0 个碰撞对。每回合同步复位检查平均耗时 3.707 ms。

成功率从 1/20 提升到 5/20，没有成功回合退化；力中止从 12/20 降到 8/20，成功吞吐从每小时
17.80 件升到 97.00 件。但 25% 成功率和 40% 力中止率仍远未达到 90% 与 5% 的发布门禁，
所以功能继续默认关闭，只作为有价值的诊断和负对照，不能称为可部署优化。本地哈希见
`expert/radeon-collision-checked-reset-ab-v1-SHA256SUMS`，两份远端清单保留完整与 compact
产物来源链。

## 表面感知预抓取淘汰探针

`expert/radeon-surface-aware-pregrasp-probes-v1-*` 保存顺序式 Radeon 淘汰实验，不是正式成功率
实验。历史轨迹显示，7 个高纸箱超时回合结束时只比名义抓取中心高 `40--50 mm`，XY 已经对齐。
候选把球形到位窗口替换为默认关闭的接触带：XY 必须在 `15 mm` 内，侧面竖直重叠至少 `20 mm`，
正向高度误差最多 `55 mm`。

v1 对所有非扁平纸箱启用。第一个保留成功探针就把 `7000005` 从完成且峰值 `17.12 N` 退化为
`56.50 N` 力中止，差异只约一个控制帧。v2 把接触带限制到至少 `150 mm` 高的纸箱，准确恢复
`7000005`；但目标超时回合 `7000000` 从低力失败变成两次重试后的 `66.22 N` 力中止。因此按
预注册安全规则取消第三探针和正式 20+20 A/B。

实现与尚未执行的固定 runner 继续默认关闭，作为可复现负对照。证据说明：扩大“完成判定”不能替代
IK 与碰撞均可行的抓取位姿。本地哈希见
`expert/radeon-surface-aware-pregrasp-probes-v1-SHA256SUMS`；远端清单保留三份完整源 summary 与
派生 compact 产物。

## 几何感知抓取规划结果

`expert/radeon-geometry-aware-grasp-planning-ab-v2-tiered-*` 保存固定 20+20 单张 Radeon A/B 的
精简 summary、轨迹失败归因、两份运行日志、精确 comparison 和本地/远端 SHA-256。相对碰撞检查
复位基线，候选只改变 `task.geometry_aware_grasp_planning_enabled`。

成功从 5/20 提升到 15/20，力中止从 8/20 降到 4/20，没有成功回归，掉落保持为 0。成功吞吐从
每小时 98.25 件提升到 359.36 件，最大力从 111.30 N 降到 46.99 N。候选没有达到 90% 成功率与
5% 力中止率门禁，所以仍是实验能力。

`expert/radeon-geometry-aware-grasp-planning-v2-probe-ledger.json` 记录保留、swept 门禁、步长和交叉
哨兵的顺序决策。完整逐帧 summary 保留在 Radeon 工作区，其哈希位于远端清单。

## 复位后备风险门控验证

`expert/radeon-reset-fallback-gate-validation-v1/` 归档冻结的 60+60 配对、多 profile Radeon
验证。碰撞检查复位为 35/60 成功、17/60 力中止；门控规划为 33/60 成功、19/60 力中止，
两组均无掉落。逐回合峰值力均值增加 6.67 N（配对 Bootstrap 95% 区间 -0.53 到 +16.85 N），
成功吞吐降至 0.910 倍。

归因审计发现规划实际启用 5 回合，其中恢复 1 个、回归 2 个；新门控相对原几何规则避免的规划
回合为 0。另有 1 个回归发生在规划次数为 0 的回合，且状态分叉早于决策分叉。该候选被拒绝并
继续默认关闭。完整解释和产物索引见证据目录内的 `RESULTS_CN.md`。

## 复位门控执行重复性

`expert/radeon-reset-gate-repeatability-v1/` 保存对 4 个验证分叉 episode 的固定种子分块研究，每个
episode 与条件各有 5 次嵌套执行。三个规划实际启用的分叉完全重现：恢复 1 个、回归 2 个。规划
未启用的 episode 在两种条件下都成功 2/5，而且四次成功全部发生在区组第二位置，说明存在进程局部
顺序/carry-over 效应，而不是未启用规划器的效果。

40 次执行只是 4 个实验单位的技术重复，不能当作 40 个独立任务样本。证据目录保留精确顺序、
事件记录、位置汇总、源 summary 哈希和中英文解释。

## 规划抓取运输契约机制探针

`expert/radeon-transport-contract-probe-v1/` 保存三个已观察开发回合上的顺序式机制探针，不是
成功率实验，也没有打开保留确认集。所有运行均使用单张 `gfx1100` Radeon、ROCm 7.2、
Genesis 1.2.3 和未修改的 35 N 中止阈值。默认关闭的候选加入
`raise -> raise_settle -> transfer -> transfer_settle -> descend` 单向阶段、20 mm 抬升步长、
10 mm 运输步长、2 帧交接、有界参考前瞻和姿态/相对位置遥测。

阶段锁存修复了 `7120004 large_narrow_carton`（13.88 N），并在完整运输锁存后保留
`5120003 shoe_box_proxy`（29.69 N）。但 `4120001 medium_carton` 在慢运输第 259 帧失去
夹持；10 mm 与 5 mm 前瞻把峰值力分别推到 39.95 N 和 40.95 N，仍未通过安全门禁。
因此候选拒绝并保持默认关闭，不再对同一开发样本扫描步长。下一机制应改变抓取稳定性本身，
例如负载感知候选评分、侧抓姿态或滑移检测与重抓。目录内的中英文结果、运行元数据和三级
SHA-256 清单保留完整证据来源链。

## 反馈式滑移恢复负对照

`expert/radeon-slip-recovery-feedback-probe-v1/` 记录默认关闭的滑移检测和有界夹力响应，使用的是
已经观察过的 `4120001 medium_carton` 机理回合。冻结规则为 8 mm 相对位移、6 mm 向下分量、
1 N 接触和 80 mm 目标距离；夹紧命令从 20 N 提到 22 N，持续 15 帧，不改变 35 N 中止线。

规则在第 159 和 261 帧触发。实测峰值保持在 22.92 N，但最终失去接触只从第 260 帧推迟到
第 261 帧，任务仍在一次重试后失败。预注册停止规则取消了哨兵和参数扫描。目录保存紧凑证据、
轨迹对照、中英文结论、运行元数据、源码哈希和完整 summary 哈希。

## 动态抓取与状态型恢复探针

`expert/radeon-dynamic-stability-setdown-probes-v1/` 归档三份完整的快照隔离动态诊断和两份紧凑闭环
summary。诊断使用 6 个唯一可行候选、2 次重复、30 mm 抬升和 30 mm 运输。恢复误差为零、重复结果
一致，但 `4120001` 中已知失败的首选抓取通过两次短测，因此没有接入在线动态排序。

同一目录还记录默认关闭的安全放回/释放/重试机制，以及独立的失败候选黑名单。放回阶段峰值为
21.81 N，并进入第二次抓取；普通重试复用 `+40 mm` 后以 129.45 N 中止，黑名单强制改选
`+45.1 mm` 后以 129.98 N 中止，两次都发生在第二次运输阶段。中英文解释、精确命令、源码哈希、
紧凑产物和远端完整 summary 哈希共同保留证据来源链。

## 完整时域与正式闭环抓取反事实

`expert/radeon-full-horizon-counterfactual-grasp-v1.json` 是六份 Git 忽略原始 JSON 的紧凑索引，
记录运行时、固定干预、源文件 SHA-256、理想化完整时域淘汰结论、六个正式闭环候选结果、两次复测
和两个回退哨兵。

理想化路径让已知失败候选通过，因此不能作为排序器。正式闭环中，`+40 mm` 未进入目标料箱，
中心 `+45 mm` 则在两次完全一致的复测中以 10.31 N 完成；五个替代中四个完成，一个越过未修改的
安全线。这些是开发标签，不是成功率。评分器仍未实现，必须先获得冻结的多 episode 数据集与未查看
配对留出集。

## 结构化抓取评分器 ROCm smoke

`training/grasp-scorer-smoke-rocm-v1.json` 记录冻结协议、28 特征六行 smoke 数据、6,276 参数检查点、
Radeon 1,000 步拟合、独立检查点加载以及冷/预热延迟基准，并用 SHA-256 绑定 Git 忽略的数据集、
训练 summary、评估与检查点。

训练和评估使用同一个已观察组，因此重建选择不是泛化结果；当前控制器没有改变。12 个 train、
6 个 development 和 6 个 holdout episode 继续保持冻结且未观察，跟踪证据已经在采集前写明升级门禁。

## 接触扳手开发诊断

`expert/radeon-contact-wrench-development-v1.json` 用哈希绑定四份被 Git 忽略的原始产物，覆盖
Genesis 接触字段探针、一个已观察机理对照、一个冻结六候选训练组，以及匹配的 CPU/ROCm 调度
对照。评分使用接触位置、法向、受力、摩擦锥余量、质心力臂和有界扰动余量。

成功与失败发生重叠，其中包含一个成功候选的抬升前假阴性和一个后来达到 100.70 N 的失败候选
假阳性，因此该指标只保留为默认关闭遥测，不打开 holdout。逐步小张量 ROCm 路径也比参考实现更慢。
最终遥测在 30 Hz 采样，Genesis 物理和接触求解继续在 Radeon 上执行。

## 开源包裹夹爪适配器

`expert/radeon-parcel-gripper-adapter-development-v1.json` 用 SHA-256 绑定 stock 接触扳手来源、
Radeon 几何探针、两个适配器机理运行和一个六候选冻结训练运行。运行时生成的 30 mm 适配器在
带许可的 Genesis Panda MJCF 每根手指上增加一个碰撞盒和一个视觉盒，仓库不复制第三方 mesh。

8 个配对候选执行嵌套在两个已观察 episode 中：stock 完成 4/8，适配器完成 7/8；stock 的 4 次
成功全部保留，未修改的 35 N 门禁在 36.95 N 中止唯一剩余危险候选。这是开发机理证据，不是
成功率或 holdout 结果。30 mm 已冻结，适配器保持默认关闭，打印件质量与柔顺性尚未建模。

## 包裹适配器质量/惯量安全门

`expert/radeon-parcel-gripper-adapter-inertia-development-v2.json` 用哈希绑定质量感知几何探针和三份
被 Git 忽略的完整轨迹。生成 MJCF 按固定有效密度 1240 kg/m3 为每根手指增加 5.952 g，用平行轴
定理移动合并质心，并写入六分量完整惯量张量。

已知失败的 `+40 mm` 机理抓取仍以 13.14 N 完成；随后已知成功的 `+45 mm` 哨兵在两次完全一致的
运行中均以 38.34 N 中止。预先规定的停止规则取消 `7130001` 扩大组和任何新配对活动。该实现作为
默认关闭的物理建模能力保留，但候选未通过晋级门禁；没有打开 holdout 或新 episode。

## Genesis 双指最小与动态复现

`expert/genesis-finger-reproduction-development-v1.json` 通过哈希绑定两项预注册缩减产生的 7 份
Git 忽略原始产物。静态零速度回放在 64 个对齐子步中没有达到已注册差异阈值；一次完整来源捕获
随后精确重现原来的 162.19 N / 115.55 mm 故障，并增加完整广义状态字段。

配对动态场景以实测零误差恢复 qpos/qvel，并回放相同的 9 维力序列。两者都没有触发独立门禁，
只出现 5.49 N 接触力差。因此证据只把缺失机理缩小到未捕获的闭环或求解器状态，不声称 Genesis
存在全局缺陷。没有打开新 episode、holdout 或参数扫描。

最终同步的 Radeon 源代码树通过全部 268 项测试。

## Genesis 指爪原始控制回放

`expert/genesis-finger-control-replay-development-v1.json` 绑定一次只读来源捕获、
原装与质量感知精确模式回放、比较结果和执行代码。提交 `63ac10b` 在物理执行
前冻结中英文协议与回放实现。

来源使用机械臂七轴位置控制和两指力控制。原始目标回放在新场景中重现质量
感知 `203/4` 故障：162.186 N、115.546 mm。原装跨模型参考更早在 `198/1`
失稳，因此注册结论是 `invalid_reference`，而不是惯量归因。本轮没有打开
参数扫描、新 episode 或 holdout；适配器继续被拒绝并默认关闭。

同步后的 Radeon 树通过 269 项测试和 28 个子测试。

## 抓取评分器 V2 训练冻结

`training/grasp-scorer-v2-train-evidence.json` 记录完整 32 组训练采集、192 个候选 rollout、两份
同容量正式模型和 development 前检查点冻结。配套保存两份训练摘要与冻结 manifest；检查点、
234,048 字节哈希数据集和 226 MiB 完整轨迹留在 Radeon 工作区，由字节数与 SHA-256 引用。

训练集内静态、pointwise 和 groupwise 的重建选择仅用于验证接线，不能解释为泛化结果。冻结记录
明确证明两份检查点在 development manifest 出现前生成，holdout 仍未创建。中英文解释见
`docs/GRASP_SCORER_V2_TRAIN_FREEZE_RESULTS_CN.md`。

## 抓取评分器 V2 development 负结果

`training/grasp-scorer-v2-development-evidence.json` 绑定一次性 16 组 development、两份冻结模型
评测和最终 `no_promotion` 决策。pointwise 与 groupwise 均满足约 0.9 ms 的延迟要求，但分别把
安全中止从静态基线的 4/16 增至 9/16 和 8/16，四个 profile 全部回归，因此均被拒绝。

证据明确记录 `selected=null`、`holdout_opened=false`，并保留事后 oracle 与失准诊断。111 MiB
完整 development 轨迹和组合数据集留在 Radeon 工作区；Git 保存决策、两份评测与紧凑哈希索引。
中英文结论见 `docs/GRASP_SCORER_V2_DEVELOPMENT_RESULTS_CN.md`。

## 保守抓取记忆 V3 train-only CV 负结果

`training/grasp-memory-v3-cv-evidence.json` 是冻结四折 train-only 研究的紧凑决策索引，绑定协议
审计与 998,070 字节完整 CV 结果。六个候选全部通过 Radeon 延迟线，但都没有改善静态基线的
7/32 成功与 17/32 安全中止；最宽信任范围把中止增加到 18 次。

最终状态为 `no_cv_candidate`、`selected=null` 和 `new_physics_authorized=false`。没有打开 V3 学习
总体或 holdout，运行时继续使用静态几何选择器。完整说明见
`docs/GRASP_MEMORY_V3_CV_RESULTS_CN.md`。

## 控制器保真探针 V4 train-only 安全结果

`training/controller-probe-v4-train-evidence.json` 是冻结 32 组、192 候选放置前探针研究的紧凑索引，
绑定协议审计、派生数据集和完整结果。`veto-static` 保留 7/32 成功，并通过四次安全放弃把力中止从
17/32 降到 13/32。

另三个策略会主动重排候选，均未通过已注册的成功或局部安全门。选中机理因此只能解释为安全否决器；
它尚未部署，不授权新物理，V2 holdout 继续关闭。详见
`docs/CONTROLLER_FAITHFUL_PROBE_V4_TRAIN_RESULTS_CN.md`。

## 圆柱候选总体 V1

`planning/cylinder-candidate-audit-v1.json` 是完整的 128 样本无结果标签解析审计。两个 64 样本
命名空间分别覆盖立式罐筒和卧式快递筒。所有样本均通过能力门并生成 16 或 18 个唯一候选；卧式
最大轴对齐误差为 `4.44e-16`，观察到的最小开口余量为 10.29 mm。

文件 SHA-256 为 `1c19e5a0...adf2c`。它只证明确定性候选覆盖；选择契约明确没有构建场景、推进
物理、执行动作或读取结果。静态 IK/碰撞筛查仍待执行。详见
`docs/CYLINDER_CANDIDATE_AUDIT_RESULTS_CN.md`。
