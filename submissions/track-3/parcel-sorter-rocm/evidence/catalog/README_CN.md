# 目录证据

`catalog-v1-submit-smoke.json` 来自最终 20 秒目录烟雾测试。运行前已将本地
`configs/catalog_v1.toml` 同步到经过验证的 Radeon 实例。

| 项目 | 值 |
| --- | --- |
| 命令 | `python scripts/evaluate_catalog.py --backend rocm --episodes-per-profile 1` |
| GPU | AMD Radeon Graphics，`gfx1100` |
| 显存 | 47.98 GiB |
| ROCm | 7.2.1 / HIP |
| Genesis | 1.2.3，`gs.amdgpu` |
| 配置 | `configs/catalog_v1.toml`，20 秒回合 |
| SHA-256 | `7b69a332faea59f6e930acfec653ec118f858c6002cd9d78d20a06bd8f142be0` |

文件包含 7 个训练 profile 各 1 个确定性回合。这是回归烟雾，不是统计意义上的成功率。
4 个盒类完成，微型盒和两个圆筒仍是明确困难样本。
