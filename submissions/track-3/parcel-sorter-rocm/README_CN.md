# Parcel Sorter ROCm 中文说明

这是一个面向 AMD Physical AI 赛道的小快递抓取与分拣项目。系统在单张
AMD Radeon GPU 和 ROCm 上完成 Genesis 物理仿真、Franka Panda 机械臂控制、
RGB-D 数据采集、ACT 训练、闭环推理、离屏录像和性能测试。

英文 [README.md](README.md) 是评审复现的主入口；中文正式报告见
[TECHNICAL_REPORT_CN.md](TECHNICAL_REPORT_CN.md)。优化顺序见
[优化路线图](docs/OPTIMIZATION_ROADMAP_CN.md)，完整工程决策和代码学习记录见
[工程决策日志](docs/ENGINEERING_DECISION_LOG_CN.md)，逐次实验见
[开发日志](docs/DEVELOPMENT_JOURNAL_CN.md)，模型比较见
[模型选型](docs/MODEL_SELECTION_CN.md)。本轮逐步优化、代码能力与决策原因见
[2026-07-25 证据驱动优化记录](docs/OPTIMIZATION_SESSION_2026-07-25_CN.md)。

## 系统组成

- Genesis 刚体物理环境、Franka Panda、Box/Cylinder 快递和左右分拣格口
- catalog v1 的 7 类带权训练包裹，以及 catalog v2 的 12 类均衡训练分层；另有 4 类仅评测行业尺寸和稳定的分层 episode 调度
- 顶视 RGB-D 相机、关节位置、末端位姿、目标位置和夹爪接触力
- IK 专家、机械臂 PD 控制、夹爪力斜坡和末端步长限制
- 检测、接近、抓取、接触验证、抬升、搬运、释放、重试和安全中止闭环
- JSONL 全量审计轨迹和 LeRobotDataset 成功专家回合
- 52M 参数 ACT 基线，以及 Diffusion/SmolVLA 的 Radeon 训练与通用闭环评测入口
- 单张 Radeon 上的并行仿真和训练吞吐 benchmark

学习模型不会直接输出关节力矩。策略输出 8 维末端动作，再经过数值检查、四元数
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
| 目录烟雾回归 | 7 类中 4 类单回合完成；仅用于回归，不是成功率 |
| 轻量 Diffusion 单步烟雾 | 76.6M 参数，Radeon 单步约 23.6 秒；不是成功率 |
| 当前测试套件 | 56 项通过 |

正式专家 120 回合结果是当前机器人能力主指标。固定 10 种子结果只用于回归基线。
ACT 已经证明数据、训练、保存、重载、ROCm 推理和 Genesis 闭环全部跑通，但成功率
仍明显低于专家，不能写成已经收敛的正式策略。相同 episode 10-19 上，第 4,000 步
优于第 5,000 步，说明模型选择不能只看离线 loss。

120 回合中的 24 次失败有 22 次触发接触力安全中止，2 次在抬升阶段丢失抓取。
同一组 120 个 episode 的固定 0.01 m 最终接近步长实验已被拒绝：成功率从 80.0%
降到 75.0%，力中止从 22 次增加到 25 次，吞吐只保留 73.6%。因此默认值恢复为
0.04 m，独立参数只用于实验复现。下一步应比较距离/接触力联合速度整形、困难样本、
关闭强图像增强和深度融合，而不是提高安全阈值或假设“越慢一定越安全”。

当前 `catalog_v1.toml` 中的 0.01 m 只用于水平对齐后的锁定下降，并与独立 XY 容差、
几何自适应预抓取窗口和三段式搬运共同使用；它不等于上面被拒绝的“只改一个固定步长”
候选。单回合目录烟雾中，`small_carton`、`flat_box`、`long_box` 和
`near_limit_box` 完成；`micro_box` 与两类圆筒仍是困难样本。

## 包裹目录回归

```bash
python scripts/evaluate_catalog.py \
  --backend rocm \
  --episodes-per-profile 1 \
  --output outputs/catalog-v1-smoke
```

可重复使用 `--profile small_carton` 只评测指定类别。加入
`--include-evaluation-only` 会运行超出当前平行夹爪能力的行业尺寸边界，只用于展示限制，
不能混入训练成功率。

catalog v2 把训练目录扩展为 12 类、每 20 回合精确分配的均衡组合。训练范围都明确标注为
适配 Panda 80 mm 夹爪的工程分层；USPS 精确尺寸带官方来源 URL，若超出夹爪能力则只评测。

定向补采微型盒与圆筒困难样本：

```bash
python scripts/run_expert.py \
  --config configs/catalog_v2.toml \
  --backend rocm \
  --episodes 20 \
  --start-episode 1000 \
  --profile micro_box \
  --profile upright_canister \
  --record-sensors --lerobot \
  --output outputs/catalog-v2-hard-shard
```

传入 profile 时，`--episodes` 表示每类回合数。每类使用独立 episode 命名空间，审计写入器
会拒绝覆盖已有文件；每次补采应使用新的输出 shard。
专家与学习策略的 summary 都会写出 `profile_summaries`，可直接对比每类成功、接触力、
掉落、延迟和吞吐，不必再手工拆分 JSON。

## Radeon Cloud 首次运行

```bash
cd /workspace/parcel-sorter-rocm
bash scripts/preflight_radeon.sh
ROCM_PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
INSTALL_LEROBOT=1 bash scripts/bootstrap_radeon.sh
source scripts/activate_radeon_env.sh
python -m unittest discover -s tests -q
```

一键执行专家、鲁棒性测试、并行 benchmark 和报告草稿：

```bash
bash scripts/run_pipeline_radeon.sh outputs/radeon-run
```

控制优化后，应使用完全相同的 episode 做对比：

```bash
python scripts/compare_expert_runs.py \
  --baseline evidence/expert/randomized-120-summary.json \
  --candidate outputs/expert-candidate/expert/summary.json \
  --output outputs/expert-candidate/comparison.json
```

该工具会拒绝样本集合不一致的比较，并列出旧失败恢复、旧成功退化、力中止与吞吐变化。

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
ACT_IMAGE_TRANSFORMS=false \
bash scripts/train_act_rocm.sh \
  outputs/radeon-dataset-120/expert/lerobot_dataset \
  outputs/train/act-radeon-5000
```

合成操作任务依赖精确图像几何，因此通用图像增强默认关闭。只应在其他数据、随机种子和
检查点完全一致的情况下设置 `ACT_IMAGE_TRANSFORMS=true` 做对照实验。仓库中的 5000
步原始证据产生于本次修改之前，当时增强已开启；目前不能把旧结果归因于新默认值。

比较 FP32、AMP 和 batch 大小时运行：

```bash
bash scripts/benchmark_act_training_rocm.sh \
  outputs/radeon-dataset-120/expert/lerobot_dataset \
  outputs/benchmarks/act-training
```

## 分段评估学习策略检查点

```bash
python scripts/evaluate_policy.py \
  --backend rocm \
  --checkpoint outputs/train/act-radeon-5000/checkpoints/004000/pretrained_model \
  --episodes 10 \
  --start-episode 10 \
  --record-video \
  --output outputs/eval-act-4000-e10
```

`--start-episode` 用于选择确定且互不重叠的随机区间。结果文件会记录本次评估的开始
episode、结束 episode 和回合数，避免所有检查点只在 episode 0 上比较。

多个检查点评估完成后运行：

```bash
python scripts/summarize_act_evaluations.py \
  outputs/eval-act-sweep \
  --output outputs/act-checkpoint-ranking.json
```

该工具会拒绝重复 episode，并优先按闭环成功率选择模型。

## Diffusion 与 SmolVLA

```bash
bash scripts/train_diffusion_rocm.sh <lerobot_dataset> outputs/train/diffusion-radeon

# 轻量配置的正式消融入口
DIFFUSION_DOWN_DIMS=256,512,1024 DIFFUSION_HORIZON=32 \
DIFFUSION_N_ACTION_STEPS=8 DIFFUSION_INFERENCE_STEPS=10 \
bash scripts/train_diffusion_rocm.sh <lerobot_dataset> outputs/train/diffusion-compact

SMOLVLA_STEPS=4000 SMOLVLA_BATCH_SIZE=4 \
SMOLVLA_POLICY_PATH=/workspace/models/smolvla_base \
bash scripts/train_smolvla_rocm.sh \
  <lerobot_dataset> outputs/train/smolvla-radeon
```

Diffusion 和 SmolVLA 是已经准备好的训练入口，不是已经取得的比赛结果。轻量 Diffusion
已经在 Radeon 上完成 1 步前向、反向、优化器更新和保存：76,597,288 参数，训练进度
约 23.6 秒；这只证明入口和缩小模型可行，仍需完整训练与分层闭环评测。SmolVLA 要求
显式指定已下载的开源检查点；若云实例可访问 Hugging Face，也可把路径设为
`lerobot/smolvla_base`。首轮冻结视觉编码器并只训练动作专家相关部分；视觉解冻必须作为
独立匹配实验。训练后的 ACT、Diffusion 和 SmolVLA 都通过 `evaluate_policy.py` 进入相同
Genesis 闭环和 35 N 安全边界。

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
完整流程。具体见 [SUBMISSION_CHECKLIST_CN.md](SUBMISSION_CHECKLIST_CN.md)。
