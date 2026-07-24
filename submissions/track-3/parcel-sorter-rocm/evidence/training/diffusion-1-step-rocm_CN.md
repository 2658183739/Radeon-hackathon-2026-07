# Diffusion 单步 Radeon 烟雾

这是训练链路烟雾，不是策略能力结果。

| 项目 | 值 |
| --- | --- |
| 命令 | `DIFFUSION_STEPS=1 DIFFUSION_BATCH_SIZE=2 DIFFUSION_NUM_WORKERS=0 bash scripts/train_diffusion_rocm.sh <dataset> outputs/train/diffusion-script-smoke-v2` |
| 数据切分 | 86 个训练回合 / 10 个评估回合 |
| 模型 | LeRobot Diffusion，263,762,728 参数 |
| 设备 | AMD Radeon Graphics，HIP 兼容设备 `cuda:0` |
| ROCm | PyTorch 2.9.1 ROCm 7.2.1 |
| 结果 | 模型、优化器创建成功，完成 1 次前向/反向并保存检查点 |
| 耗时 | 含启动约 53 秒 |

第一次尝试因没有安装 `diffusers` 在模型创建前停止；随后 bootstrap 已改为安装
LeRobot 的 `diffusion` 和 `smolvla` extras，第二次完成。单步结果不能推出成功率、
loss 趋势或比赛结论。
