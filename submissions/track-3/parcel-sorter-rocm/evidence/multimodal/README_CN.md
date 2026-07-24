# 多模态证据

这些文件把历史深度尺度错误和修正后的 RGB-D 链路明确分开。

| 文件 | 含义 |
| --- | --- |
| `old-dataset-rgb-audit.json` | 旧 96 回合数据仍可用于 RGB，但有深度告警 |
| `old-dataset-rgbd-audit.json` | 旧数据按 RGB-D 请求时按预期硬拒绝 |
| `corrected-dataset-audit.json` | 修正后一回合数据通过 RGB-D metadata 审计 |
| `corrected-expert-summary.json` | Radeon 传感器采集链路烟雾 |
| `act-rgbd-smoke-config.json` | 保存的 ACT 检查点声明 RGB 与深度视图输入 |
| `act-rgbd-closed-loop-summary.json` | 单步检查点加载/闭环推理烟雾，不是能力结果 |

修正数据有 152 帧，原始深度范围 0.737-3.535 m，中位数 1.164 m。ACT 烟雾模型为
51,577,736 参数并完成一次优化。它的单回合闭环失败符合预期；该证据只证明输入与运行链。

文件 SHA-256 与英文 [README](README.md) 一致；任何重新生成都应同时更新证据文件和哈希。
