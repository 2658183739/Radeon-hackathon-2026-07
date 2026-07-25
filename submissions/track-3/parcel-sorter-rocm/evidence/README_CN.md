# Radeon 原始证据索引

本目录保存从单张 Radeon 实测环境复制的小体积原始结果，以及成对记录命令和产物哈希的
证据说明。它们用于审计 README 和技术报告中的数字，不替代完整数据集和模型权重。

| 文件 | 内容 |
| --- | --- |
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
