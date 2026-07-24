# 轻量 Diffusion 单步 Radeon 烟雾

这是经过参数优化的训练链路烟雾，不是闭环策略能力结果。

| 项目 | 值 |
| --- | --- |
| 实验 | `diffusion-compact-smoke-v1` |
| 仓库状态 | `8dea503` 之后的本地变更集 |
| 命令 | `DIFFUSION_STEPS=1 DIFFUSION_BATCH_SIZE=2 DIFFUSION_NUM_WORKERS=0 DIFFUSION_DOWN_DIMS=256,512,1024 DIFFUSION_HORIZON=32 DIFFUSION_N_ACTION_STEPS=8 DIFFUSION_INFERENCE_STEPS=10 DIFFUSION_USE_AMP=true bash scripts/train_diffusion_rocm.sh <dataset> outputs/train/diffusion-compact-smoke-v1` |
| 数据切分 | 86 个训练回合 / 10 个评估回合 |
| 模型 | LeRobot Diffusion，76,597,288 参数 |
| 设备 | AMD Radeon Graphics，HIP 兼容设备 `cuda:0`，仅 1 张可见 GPU |
| ROCm | PyTorch 2.9.1 ROCm 7.2.1 |
| 结果 | 完成 1 次前向、反向和优化器更新，保存检查点 |
| 单步耗时 | 训练进度约 23.60 秒；含启动的包装器约 41.10 秒 |
| 模型 SHA-256 | `de1241d77d41517d68e7e3ec114b5b37f3d1595b2b847eb13abc2d391a2e54f5` |
| 模型配置 SHA-256 | `c86a3f0b81a546611f91a122317da2d68318dfdc781927d541a8af7d53c89643` |
| 训练配置 SHA-256 | `e0767a9580e7a98b610d66093ed45cff8df5e83b34c0f05592dc43aca283dd79` |

上一份单步烟雾使用 `[512,1024,2048]`，263,762,728 参数，含启动约 53 秒。本次参数量
约减少 71%，观测到的单步包装器耗时约减少 55%。由于启动和缓存状态没有按正式基准完全
锁定，这只是方向性比较。下一步必须固定随机种子、预热方式和闭环 episode，才能决定是否
保留轻量模型。

第一次重试在模型创建前失败，因为当前动态 LeRobot CLI 要求 `down_dims` 作为一个列表值，
脚本却传成了三个独立参数。现在脚本输出 `"[256,512,1024]"`，并在启动前检查 horizon 与
UNet 下采样倍数的兼容性。这个失败属于命令集成问题，不属于模型失败。
