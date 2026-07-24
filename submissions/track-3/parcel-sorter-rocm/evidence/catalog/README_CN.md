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

## Catalog v2 优化证据

以下文件均来自同一张 `gfx1100`、47.98 GiB Radeon，环境为 ROCm 7.2.1、PyTorch
2.9.1 ROCm 和 Genesis 1.2.3。每个候选都是确定性回归烟雾，不是成功率估计。

| 产物 | 用途/结果 | SHA-256 |
| --- | --- | --- |
| `catalog-v2-baseline.json` | 12 类各 1 回合，8 类完成 | `760b09e0a38ed38ebf37dcadb91d59e5d5999d129b943d7f947c3dfe562a810f` |
| `catalog-v2-height-aware.json` | 已拒绝的高包裹高度候选 | `938514705e7b0815b18115bc0a97ebe5068aa80f76dfec09cc3434c11d713704` |
| `catalog-v2-seated-grasp.json` | 已拒绝的闭合后落座候选 | `829415c920c09284f2a1a536dc0c9bb3ed687e89249bc82abfccbcf9fbf92fa0` |
| `catalog-v2-rolling-friction.json` | 滚动摩擦 0.002；漂移 18.3 mm，79.27 N 中止 | `7d17cb091222c7b4411502d5a0f73f96996be48d9340bbd23ac839256a293a8a` |
| `catalog-v2-tube-slow-approach.json` | 拒绝 2.5 mm 接近；36.74 N 中止 | `1ff4140e65925d3acb5108f42b8a696913d9d5b95bb0f2c4764cae6bfd318258` |
| `catalog-v2-tube-step-2mm.json` | 拒绝 2.0 mm 接近；98.83 N 中止 | `51ab8c36fdb7f964b9c6922e1ee107cb58882d2c7d6ed3ce895409ac371898cb` |
| `catalog-v2-tube-tight-xy.json` | 拒绝 5 mm XY 阈值；0 N 但接近超时 | `4644c637e6cb5e3f7c384d39738f42d2d2f8c69ebf28efc30056205122fc7254` |
| `catalog-v2-tube-friction-005.json` | 滚动摩擦 0.005；漂移 3.3 mm，73.99 N 中止 | `37f99b8f1d0fefef7630453909d64fc172821c58b593cee42d4d9962b4027e99` |
| `catalog-v2-rolling-final.json` | 拒绝全局 solver；目录从 8/12 回归到 6/12 | `ae691128f2bc2a66e6e02096757f72d00583691c7c6b062ce74fe94faa31a26a` |
| `catalog-v2-rolling-scoped.json` | 只对易滚邮筒启用 solver；目录恢复到 8/12 | `f0ecdc95781825653ad3395b600e476c19daa28712420808e20bb1cf94b7d9f8` |

保留的代码开启 Genesis 扭转与滚动摩擦，并把 profile 级滚动系数传给包裹材质。未通过
验收的 profile 级控制覆盖已经删除。邮筒仍是明确限制；下一候选是低矮防滚定位槽或适合
圆筒的末端执行器。

两份全目录文件构成回归门槛：全局 solver 配置被拒绝，限定作用域后所有非邮筒 profile
恢复到基线结果。两处 8/12 都不是正式成功率。
