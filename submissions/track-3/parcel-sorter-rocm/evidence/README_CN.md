# Radeon 原始证据索引

本目录保存从单张 Radeon 实测环境复制的小体积原始结果，以及成对记录命令和产物哈希的
证据说明。它们用于审计 README 和技术报告中的数字，不替代完整数据集和模型权重。

| 文件 | 内容 |
| --- | --- |
| `expert/randomized-120-summary.json` | 正式 120 回合随机专家结果 |
| `expert/fixed-10-summary.json` | 固定种子专家回归基线 |
| `expert/final-approach-001-120-summary.json` | 被拒绝的 0.01 m 候选，同组 120 回合 |
| `expert/final-approach-001-comparison.json` | 基线/候选逐回合比较与验收决策 |
| `act/checkpoint-4000-episodes-10-19.json` | ACT 4000 步闭环评估 |
| `act/checkpoint-5000-episodes-10-19.json` | ACT 5000 步同种子评估 |
| `training/act-5000-amp-b32.log` | 正式 5000 步训练日志 |
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

目录烟雾同样只是小体积回归证据：4 个盒类完成，3 个困难 profile 失败，不构成正式成功率。
其 SHA-256 记录在 `evidence/catalog/README_CN.md`。

Catalog v2 同样只记录每类一个确定性回合以及同 episode 的物理/控制候选，不能合并为
正式成功率。准确结果和哈希见 `catalog/README_CN.md`。
