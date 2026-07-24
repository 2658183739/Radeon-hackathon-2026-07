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

## 2026-07-25 中心抓取证据

以下序列延续限定滚动物理的对照。每个单邮筒文件只包含同一个固定诊断回合，不是成功率
估计；两份回归文件各包含 12 个 profile 的固定单回合。

| 产物 | 决策 / 观察结果 | SHA-256 |
| --- | --- | --- |
| `catalog-v2-tube-geometry-fix.json` | 规范化圆筒几何；72.92 N 中止 | `72bbfb7c134cee44eeef844c7eceef501fe68f567d306cae4d8ed817b732e13d` |
| `catalog-v2-tube-geometry-xy005.json` | 拒绝 5 mm XY 门槛；0 N 但接近超时 | `b33c729900b7c75c93bcd6cb18003c610768c9219c446341889f0e9a73732907` |
| `catalog-v2-tube-geometry-xy010.json` | 拒绝仅 10 mm XY 候选；63.77 N | `2040561aee1cc71a148235d1b9f68191ab194e3472d79c39e6500f91d121c20c` |
| `catalog-v2-tube-geometry-xy010-step0025.json` | 拒绝组合候选；143.33 N | `032649742823ada893a1e4d88484e284c53ad9748e198270ed7ece1dfd61af9d` |
| `catalog-v2-tube-rails-prototype.json` | 拒绝双导轨原型；无改善，72.92 N | `47973f22b4ccedc3e35887e385b89307a1329f2f6d41059752475f46b916efd8` |
| `catalog-v2-tube-axis-aligned.json` | 保留轴向夹爪；改善到 43.54 N | `23009ac98a15447059756857c8035f4c095b3cfd67ae0d1c8e74a905c7031459` |
| `catalog-v2-tube-axis-step005.json` | 保留 5 mm 最终接近；34.26 N 后抬升丢抓 | `07671138052ed0760d11de62c0cafd83c4cad1a14e49b9d80053f52ad454be16` |
| `catalog-v2-tube-stable-contact.json` | 三帧稳定后进入抬升；恢复以 48.05 N 中止 | `f0c10d4f919f4c3219e15c8299c4648c8bdd9e09bc24f2cdd6620c36b3a6d969` |
| `catalog-v2-tube-lift-step010.json` | 保留 10 mm 抬升请求；接触更久，恢复为 35.12 N | `87cb904706bbaa8d2c4f9719689b3755efb503352cb89955fab64470da64b979` |
| `catalog-v2-tube-pad-friction200.json` | 保留摩擦指垫；峰值 15.62 N，三次进入抬升 | `17f31300b072fe34577d32a7bc94b8522f509450c6096273f850ffd774824de0` |
| `catalog-v2-tube-centered-grasp.json` | 保留 10 mm 闭合容差；首次真正抬到中心高度 66.4 mm | `d406edbaf642b355874e3d3bbb01838dcbd4d0e2526512db8e5677122444a462` |
| `catalog-v2-tube-force025.json` | 拒绝 25 N 夹持力；69.2 mm，36.46 N 安全违规 | `808ce89fec19993756ee1aa33a23ac81bcebc70b3d1d365c674d76165dcb8a8c` |
| `catalog-v2-tube-force035.json` | 拒绝 35 N 夹持力；69.9 mm，35.19 N 安全违规 | `7ec0738ccc77369f656127d8ec175abe243fafd499bddb0aa76e79d01486d96f` |
| `catalog-v2-centered-regression.json` | 拒绝全局三帧稳定；目录退化到 5/12 | `73a33b088c2e8ea524700f1076afa1985c1255645c1b40e8a0a60ccd7f0bea00` |
| `catalog-v2-tube-scoped-regression.json` | 保留 profile 限定稳定；完全恢复基线 8/12 | `1e99926b5a9d481349d84758d463902158ee5d264c53cba79245a1154dd83605` |

最终保留实现修复了圆筒构造和邮筒轴向抓取，并为邮筒限定接近、抬升、闭合容差、稳定
帧数和高摩擦指垫。它不代表邮筒任务成功：最佳保留诊断把物体抬离台面，但没有完成搬运
和投放。下一项可接受改动必须是结构化夹爪/夹具候选，并经过重复保留集评测。
