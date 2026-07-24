# Radeon 原始证据索引

本目录保存从单张 Radeon 实测环境复制的小体积原始结果。它们用于审计 README 和技术
报告中的数字，不替代完整数据集和模型权重。

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
| `training/diffusion-1-step-rocm.md` | Diffusion 单步 Radeon 训练链路记录 |

SHA-256 见英文 [README.md](README.md)。JSON 包含配置、运行版本、episode 随机参数、
终止结果和指标。大型 RGB-D 数据、206 MB 模型权重、优化器状态和 MP4 不进入普通 Git，
最终提交时应通过 release 或对象存储提供，并公布 SHA-256。

失败候选也被保留，因为可复现性不仅覆盖成功结果；comparison 明确记录了为什么不能
把它设为默认值。

目录烟雾同样只是小体积回归证据：4 个盒类完成，3 个困难 profile 失败，不构成正式成功率。
其 SHA-256 记录在 `evidence/catalog/README_CN.md`。
