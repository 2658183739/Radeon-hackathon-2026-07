# Parcel Sorter ROCm 中文说明

这是一个面向 AMD Physical AI 赛道的小快递抓取与分拣项目。系统在单张
AMD Radeon GPU 和 ROCm 上完成 Genesis 物理仿真、Franka Panda 机械臂控制、
RGB-D 数据采集、ACT 训练、闭环推理、离屏录像和性能测试。

英文 [README.md](README.md) 是评审复现的主入口；英文
[TECHNICAL_REPORT.md](TECHNICAL_REPORT.md) 是正式技术报告。本文件用于中文操作和
结果说明。

## 系统组成

- Genesis 刚体物理环境、Franka Panda、随机快递和左右分拣格口
- 顶视 RGB-D 相机、关节位置、末端位姿、目标位置和夹爪接触力
- IK 专家、机械臂 PD 控制、夹爪力斜坡和末端步长限制
- 检测、接近、抓取、接触验证、抬升、搬运、释放、重试和安全中止闭环
- JSONL 全量审计轨迹和 LeRobotDataset 成功专家回合
- 52M 参数 ACT 视觉模仿策略、检查点保存、加载和 Genesis 闭环评估
- 单张 Radeon 上的并行仿真和训练吞吐 benchmark

学习模型不会直接输出关节力矩。ACT 输出 8 维末端动作，再经过数值检查、四元数
归一化、单步位移限制、IK、PD、夹爪控制和接触力安全边界。监督状态机始终位于
模型外部，因此专家和学习策略共用同一套执行与安全链路。

## 已验证环境

2026 年 7 月 24 日，完整流程已在以下单卡环境执行：

| 项目 | 实测环境 |
| --- | --- |
| GPU | AMD Radeon Graphics，`gfx1100` |
| 显存 | 47.98 GiB |
| 系统 | Ubuntu 24.04 |
| ROCm | 7.2.1 |
| PyTorch | 2.9.1 ROCm |
| Genesis | 1.2.3 |
| LeRobot | 0.6.1 |
| Python | 3.12 |

PyTorch 的 ROCm 版本沿用 `torch.cuda` 兼容接口，因此配置中的 `cuda:0` 表示第一张
HIP/ROCm 设备，不代表使用了 NVIDIA CUDA。预检脚本会检查 `torch.version.hip`，并在
环境不符合时停止。

## 当前实测结果

| 测试 | 结果 |
| --- | ---: |
| 正式随机专家测试 | 120 回合成功 96 回合，成功率 80.0% |
| 首次成功率 | 77.5% |
| 发生重试回合的恢复成功率 | 37.5% |
| 成功 RGB-D 数据 | 96 回合，11,753 帧 |
| 固定 10 种子专家基线 | 成功率 90%，掉落率 0% |
| 固定种子成功吞吐 | 727 件/小时 |
| ACT 正式训练 | 5,000 步，AMP，batch 32 |
| ACT 第 5,000 步评估 loss | 0.1384 |
| ACT 第 4,000 步，episode 10-19 | 闭环成功率 30% |
| ACT 第 4,000 步推理 | 平均 2.05 ms，P95 8.00 ms |
| ACT 第 5,000 步，episode 10-19 | 闭环成功率 10% |
| 128 并行环境 | 46,582 environment-steps/s |
| 峰值 GPU 利用率 | 83% |
| ACT AMP/batch32 训练吞吐 | 80 samples/s |

正式专家 120 回合结果是当前机器人能力主指标。固定 10 种子结果只用于回归基线。
ACT 已经证明数据、训练、保存、重载、ROCm 推理和 Genesis 闭环全部跑通，但成功率
仍明显低于专家，不能写成已经收敛的正式策略。相同 episode 10-19 上，第 4,000 步
优于第 5,000 步，说明模型选择不能只看离线 loss。

120 回合中的 24 次失败有 22 次触发接触力安全中止，2 次在抬升阶段丢失抓取。
当前优先优化方向是降低最终接近速度、增加困难样本，并比较关闭强图像增强和加入
深度融合后的模型，而不是提高安全阈值。

## Radeon Cloud 首次运行

```bash
cd /workspace/parcel-sorter-rocm
bash scripts/preflight_radeon.sh
INSTALL_LEROBOT=1 bash scripts/bootstrap_radeon.sh
source scripts/activate_radeon_env.sh
python -m unittest discover -s tests -q
```

一键执行专家、鲁棒性测试、并行 benchmark 和报告草稿：

```bash
bash scripts/run_pipeline_radeon.sh outputs/radeon-run
```

## 采集 120 回合 RGB-D 专家数据

```bash
python scripts/run_expert.py \
  --backend rocm \
  --episodes 120 \
  --record-sensors \
  --lerobot \
  --output outputs/radeon-dataset-120
```

成功回合进入 `expert/lerobot_dataset`，所有成功和失败回合进入
`expert/audit_dataset`。ACT 使用顶视 RGB 和 20 维非特权状态；7 维包裹真值位姿只用于
审计，不输入模型。深度以米为单位保存，供后续 RGB-D 融合实验使用。

## 在 Radeon 上训练 ACT

```bash
ACT_STEPS=5000 \
ACT_BATCH_SIZE=32 \
ACT_NUM_WORKERS=4 \
ACT_SAVE_FREQ=1000 \
ACT_USE_AMP=true \
bash scripts/train_act_rocm.sh \
  outputs/radeon-dataset-120/expert/lerobot_dataset \
  outputs/train/act-radeon-5000
```

比较 FP32、AMP 和 batch 大小时运行：

```bash
bash scripts/benchmark_act_training_rocm.sh \
  outputs/radeon-dataset-120/expert/lerobot_dataset \
  outputs/benchmarks/act-training
```

## 分段评估 ACT 检查点

```bash
python scripts/evaluate_act.py \
  --backend rocm \
  --checkpoint outputs/train/act-radeon-5000/checkpoints/004000/pretrained_model \
  --episodes 10 \
  --start-episode 10 \
  --record-video \
  --output outputs/eval-act-4000-e10
```

`--start-episode` 用于选择确定且互不重叠的随机区间。结果文件会记录本次评估的开始
episode、结束 episode 和回合数，避免所有检查点只在 episode 0 上比较。

## Docker

Dockerfile 已固定到 ROCm 7.2.1、Ubuntu 24.04、Python 3.12 和 PyTorch 2.9.1，
并在构建时下载锁定提交的 Genesis 与 LeRobot，不依赖本地未提交的 `third_party`。

```bash
docker build -f Dockerfile.rocm \
  --build-arg INSTALL_LEROBOT=1 \
  -t parcel-sorter-rocm:rocm7.2.1 .
```

比赛云实例已验证的是裸机流程；不要求云容器内部再运行嵌套 Docker。

## NVIDIA 本地开发

RTX 5060 Ti 16 GB 可以用于本地开发和调试：

```bash
bash scripts/preflight_cuda.sh
bash scripts/bootstrap_cuda.sh
bash scripts/run_pipeline_cuda.sh
```

CUDA 结果不能代替最终 AMD Radeon/ROCm 证据。代码中不要引入 TensorRT 或写死的
NVIDIA 专用算子，否则迁回 ROCm 会增加返工。

## 原始证据与剩余提交项

小体积的专家、ACT、训练和 benchmark 原始结果保存在 `evidence/`，数据集和 206 MB
模型权重不直接提交 Git。最终 PR 前仍需填写与 Luma 一致的团队名和法定姓名、上传
带 SHA-256 的正式权重与数据、录制 3-5 分钟演示视频，并从最终 Git 提交重新跑一次
完整流程。具体见 [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md)。
