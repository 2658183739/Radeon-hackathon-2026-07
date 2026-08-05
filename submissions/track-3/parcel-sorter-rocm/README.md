# Parcel Sorter ROCm / ROCm 包裹分拣

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![ROCm 7.2.1](https://img.shields.io/badge/ROCm-7.2.1-red.svg)
![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)

![Local five-second simulation demonstration](docs/assets/hook_5_seconds.gif)

AMD Radeon ROCm simulation for reproducible parcel pick-and-place with Genesis and Franka Panda. This is simulation evidence, not real-robot evidence.

面向 AMD Radeon ROCm 的可复现包裹抓取与分拣仿真，基于 Genesis 与 Franka Panda。本项目提供的是仿真证据，不是现实机器人证据。

**Status / 状态:** deterministic expert/reference development recorded; strict pure VLA is **0/3 and not passed**. The reviewable repository MP4 is public at [blob](https://github.com/2658183739/Radeon-hackathon-2026-07/blob/track3-parcel-sorter-final/submissions/track-3/parcel-sorter-rocm/videos/genesis_panda_8_success_reference_demo.mp4) and [raw](https://raw.githubusercontent.com/2658183739/Radeon-hackathon-2026-07/track3-parcel-sorter-final/submissions/track-3/parcel-sorter-rocm/videos/genesis_panda_8_success_reference_demo.mp4). [PR #119](https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/119) is **Open** against `main`; Bilibili/YouTube is not published.

确定性专家/参考开发已记录；严格纯 VLA 为 **0/3，未通过**。仓库 MP4 可通过 [blob](https://github.com/2658183739/Radeon-hackathon-2026-07/blob/track3-parcel-sorter-final/submissions/track-3/parcel-sorter-rocm/videos/genesis_panda_8_success_reference_demo.mp4) 和 [raw](https://raw.githubusercontent.com/2658183739/Radeon-hackathon-2026-07/track3-parcel-sorter-final/submissions/track-3/parcel-sorter-rocm/videos/genesis_panda_8_success_reference_demo.mp4) 直接审查；[PR #119](https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/119) 为针对 `main` 的 **Open** PR；未发布 Bilibili/YouTube。

**Contents / 目录**

- [1. Project Overview / 项目简介](#overview)
- [2. Development Process / 开发过程](#development)
- [3. Source Attribution / 代码来源说明](#attribution)
- [4. Team Roles / 团队分工](#team)
- [5. Install and Run / 安装与运行](#install)

<a id="overview"></a>
## 1. Project Overview / 项目简介

### English

Parcel Sorter ROCm is a simulation-first Physical AI project for picking a parcel and placing it in a requested left or right bin. It runs one AMD Radeon GPU through ROCm, uses Genesis 1.2.3 rigid-body simulation and a Franka Panda MJCF model, and evaluates deterministic expert/reference control separately from learned-policy experiments.

The working policy contract uses overhead RGB plus a 43-D state, and a 20-D action when primitive progress is enabled. Physics, control, and camera rates are 240 Hz, 30 Hz, and 10 Hz. The verified evidence runtime is AMD Radeon Graphics (`gfx1100`), ROCm 7.2.1, PyTorch 2.9.1 ROCm, Genesis 1.2.3, LeRobot 0.6.1, and Python 3.12. `cuda:0` means the HIP/ROCm device in this repository, not NVIDIA CUDA.

### 中文

Parcel Sorter ROCm 是一个以仿真为先的具身智能项目：抓取包裹并放入指定左/右格口。它在单张 AMD Radeon GPU 上通过 ROCm 运行，使用 Genesis 1.2.3 刚体仿真和 Franka Panda MJCF 模型，并将确定性专家/参考控制与学习策略实验分开评估。

当前策略合约使用俯视 RGB 与 43 维状态；启用 primitive progress 时使用 20 维动作。物理、控制和相机频率分别为 240 Hz、30 Hz 和 10 Hz。已核验证据运行环境为 AMD Radeon Graphics（`gfx1100`）、ROCm 7.2.1、PyTorch 2.9.1 ROCm、Genesis 1.2.3、LeRobot 0.6.1 和 Python 3.12。仓库中的 `cuda:0` 表示 HIP/ROCm 设备，不表示 NVIDIA CUDA。

### Result Boundary / 结果边界

| Evidence track / 证据轨道 | Recorded result / 记录结果 | What it means / 含义 |
| --- | --- | --- |
| Deterministic expert/reference / 确定性专家参考 | **8/10** successful trajectories / 成功轨迹 | Demonstration provenance only; not VLA credit / 仅示范来源，不计入 VLA |
| Offline action ablation / 离线动作消融 | 42 episode-stage samples / 42 个样本 | Action-contract measurement; not task success / 动作合约指标，不是任务成功 |
| Strict pure VLA / 严格纯 VLA | **0/3, not passed / 未通过** | Must not be presented as a VLA success / 不得表述为 VLA 成功 |

The audited primitive dataset contains **7 independent episodes** and **4,557 frames** at 30 fps. It has RGB observations, a 43-D non-privileged state, 20-D actions, and primitive progress. Details: [data contract](data/README.md), [dataset audit](evidence/training/pash-primitive-dataset-v2-audit.json), and [training evidence](docs/TRAINING_EVIDENCE.md).

经审计的 primitive 数据集包含 **7 个独立 episode** 与 **4,557 帧**，采样率为 30 fps；包含 RGB 观测、43 维非特权状态、20 维动作和 primitive progress。详情见 [数据合约](data/README.md)、[数据集审计](evidence/training/pash-primitive-dataset-v2-audit.json) 和 [训练证据](docs/TRAINING_EVIDENCE.md)。

<a id="development"></a>
## 2. Development Process / 开发过程

### English

**Key decisions.** We selected a fixed Panda workcell to isolate manipulation, locked the Radeon runtime and upstream revisions, retained deterministic expert/reference rollouts for data provenance, and made attribution fail closed. Learned actions are checked against finite-value, Cartesian, tool-command, IK, and force boundaries before execution.

**Difficulties and resolutions.** Stock finger geometry could make side/oblique contacts unreliable. The project uses structured XML generation from the locked Panda MJCF to create versioned parcel-adapter variants while preserving the upstream source meshes. A second issue was that raw policy actions exceeded the audited action envelope. The offline ablation shows raw VLA passing 0/42 envelope checks, while safety-clipped VLA and Harness-Lite each pass 42/42. This is a safety-contract finding, not a task-success claim.

**Next steps.** Repeat strict closed-loop VLA evaluation with an auditable protocol, retain failures, and publish only after all attribution gates pass. TensorBoard export, a public dataset URL, Sim-to-Real protocol, and real-robot validation remain **pending**. The repository video and PR links above are publication records only, not pure-VLA or real-robot claims.

### 中文

**关键决策。** 项目选择固定 Panda 工作单元以隔离操作问题，锁定 Radeon 运行环境和上游版本，保留确定性专家/参考 rollout 作为数据来源，并以 fail-closed 方式处理归因。学习策略动作在执行前要通过有限值、笛卡尔步长、工具指令、IK 和力边界检查。

**困难与解决。** 原始手指几何会使侧向/斜向接触不稳定。项目从锁定的 Panda MJCF 使用结构化 XML 生成版本化的包裹适配器变体，同时保留上游源 mesh。另一个问题是原始策略动作超出经审计的动作包络：离线消融中，原始 VLA 为 0/42，安全裁剪 VLA 与 Harness-Lite 均为 42/42。此结论仅说明安全动作合约，不表示任务成功。

**下一步。** 使用可审计协议重复严格闭环 VLA 评测并保留失败样本，只有全部归因门通过后才发布。TensorBoard 导出、公开数据集 URL、Sim-to-Real 协议和真实机器人验证仍为 **pending**。上方仓库视频和 PR 链接仅是发布记录，不构成纯 VLA 或真实机器人主张。

### Offline Ablation / 离线消融

| Treatment / 处理方式 | Mean MAE | Mean MSE | Envelope passes / 包络通过 |
| --- | ---: | ---: | ---: |
| Expert executor / 专家执行器 | 0.00447 | 0.000422 | 42/42 |
| Raw VLA / 原始 VLA | 0.00656 | 0.000972 | 0/42 |
| Safety-clipped VLA / 安全裁剪 VLA | 0.00569 | 0.000434 | 42/42 |
| Harness-Lite | 0.00527 | 0.000427 | 42/42 |

The source is [the ablation JSON](evidence/training/pash-primitive-smolvla-2800step-offline-ablation-v1.json), the [local curve](docs/assets/pash-primitive-smolvla-2800step-training-curve-v1.png), and [training log](evidence/training/pash-primitive-smolvla-rocm-2800step-v1.log). See [ablation notes](docs/ABLATION_RESULTS.md). 证据来源为上述 JSON、本地曲线与训练日志；详见 [消融说明](docs/ABLATION_RESULTS.md)。

<a id="attribution"></a>
## 3. Source Attribution / 代码来源说明

### English

| Component | Source and license | Use and project changes |
| --- | --- | --- |
| Genesis | `Genesis-Embodied-AI/genesis-world`, locked revision `ec0efcc0...`, Apache-2.0 | Rigid-body simulation and asset loading. The project configures the parcel scene, sensing, deterministic control, logging, and validation around it. |
| LeRobot | `huggingface/lerobot`, locked revision `73dbb6f...`, Apache-2.0 | Local dataset and policy-training interfaces. The project uses a locally audited training path and does not claim a hosted dataset. |
| Franka Panda MJCF | Official Franka Panda MJCF as distributed by Genesis 1.2.3, `xml/franka_emika_panda/panda.xml`, Apache-2.0 | The source asset remains traceable to the locked Genesis runtime. Project code can generate versioned parcel-finger adapter or tri-suction derivatives from structured XML; it does not replace the attribution of the upstream asset. |
| Original project work | `src/parcel_sorter/`, `scripts/`, `configs/`, `evidence/` | Parcel task, data audit, deterministic expert/reference controller, safety gates, evidence schema, ROCm scripts, and offline-ablation tooling. |

Exact revisions and license data are recorded in [UPSTREAM_LOCK.json](UPSTREAM_LOCK.json) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). No third-party source is represented as original project work.

### 中文

| 组件 | 来源与许可证 | 使用方式与本项目修改 |
| --- | --- | --- |
| Genesis | `Genesis-Embodied-AI/genesis-world`，锁定版本 `ec0efcc0...`，Apache-2.0 | 用于刚体仿真和资产加载；本项目围绕其配置包裹场景、传感、确定性控制、日志和验证。 |
| LeRobot | `huggingface/lerobot`，锁定版本 `73dbb6f...`，Apache-2.0 | 用于本地数据集与策略训练接口；本项目使用本地审计训练路径，不主张托管数据集。 |
| Franka Panda MJCF | Genesis 1.2.3 分发的官方 Franka Panda MJCF，`xml/franka_emika_panda/panda.xml`，Apache-2.0 | 上游资产可追溯到锁定的 Genesis 运行时。本项目可由结构化 XML 生成版本化的手指适配器或三吸盘派生资产，但不改变上游资产归属。 |
| 项目原创部分 | `src/parcel_sorter/`、`scripts/`、`configs/`、`evidence/` | 包裹任务、数据审计、确定性专家/参考控制器、安全门、证据模式、ROCm 脚本和离线消融工具。 |

精确版本与许可证记录在 [UPSTREAM_LOCK.json](UPSTREAM_LOCK.json) 和 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。不将任何第三方来源表述为项目原创。

<a id="team"></a>
## 4. Team Roles / 团队分工

### English

**2658183739 is the sole submitter.** The submitter is responsible for system design, implementation, experiment execution, evidence review, and the final submission decision. AI tools may assist with drafting, code navigation, and repetitive engineering tasks, but the submitter reviews the resulting code, evidence, claims, and release contents before submission.

### 中文

**2658183739 是唯一提交者。** 提交者负责系统设计、实现、实验执行、证据审核和最终提交决策。AI 工具可辅助文档起草、代码定位和重复性工程工作，但提交前的代码、证据、结论和发布内容均由提交者审核。

<a id="install"></a>
## 5. Install and Run / 安装与运行

### English

The recorded environment is Linux, ROCm 7.2.1, Python 3.12, and one visible Radeon GPU. Local audited data and the audited local backbone are prerequisites; no public dataset or backbone download URL is claimed.

**Docker one-command reproduction.** This builds the pinned container and executes the ROCm authority check. It requires Linux Docker access to `/dev/kfd` and `/dev/dri`.

```bash
docker build -f Dockerfile.rocm --build-arg INSTALL_LEROBOT=1 -t parcel-sorter-rocm . && \
docker run --rm --device=/dev/kfd --device=/dev/dri --group-add video \
  parcel-sorter-rocm bash scripts/preflight_radeon.sh
```

**Native installation and training.** Install a HIP-enabled PyTorch 2.9.1 ROCm 7.2.1 build using the approved Radeon environment before this step. `requirements.txt` deliberately does not install a generic PyPI `torch`, which could select a non-ROCm build.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e . -r requirements.txt
export PYTHONPATH="$PWD/src"
bash scripts/preflight_radeon.sh

MOBILE_SMOLVLA_PROGRESS_CHANNEL=1 MOBILE_SMOLVLA_STEPS=2800 \
  bash scripts/train_mobile_smolvla_rocm.sh \
  /path/to/local/mobile-primitive-dataset-v2 \
  "$PWD/outputs/train/mobile-smolvla-primitive-progress"
```

**Reproduce the expert/reference screen and both camera views.** The first
command records overview and wrist sidecars for all 10 fixed-seed episodes.
The second keeps only the eight episodes whose `success` field is true and
fails closed if a required source or wrist video is missing.

```bash
python3 scripts/run_expert.py \
  --config configs/baseline.toml --backend rocm --episodes 10 \
  --record-video --output outputs/reproduce-expert

python3 videos/build_demo_video.py \
  --source-root outputs/reproduce-expert/expert \
  --font /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc \
  --out outputs/final-video
```

**Verification.** A successful preflight reports one HIP-visible GPU. Inspect data, training, testing, and delivery boundaries through [data/README.md](data/README.md), [docs/TRAINING_EVIDENCE.md](docs/TRAINING_EVIDENCE.md), [docs/TEST_REPORT.md](docs/TEST_REPORT.md), [videos/README.md](videos/README.md), and [docs/SUBMISSION_CHECKLIST.md](docs/SUBMISSION_CHECKLIST.md). The strict VLA result remains 0/3 and not passed.

### 中文

记录的环境为 Linux、ROCm 7.2.1、Python 3.12 和一张可见 Radeon GPU。本地审计数据与审计过的本地骨干模型是前提；本仓库不主张公开数据集或骨干下载 URL。

**Docker 一键复现。** 以下命令构建锁定容器并执行 ROCm 权威检查。Linux Docker 必须可访问 `/dev/kfd` 和 `/dev/dri`。

```bash
docker build -f Dockerfile.rocm --build-arg INSTALL_LEROBOT=1 -t parcel-sorter-rocm . && \
docker run --rm --device=/dev/kfd --device=/dev/dri --group-add video \
  parcel-sorter-rocm bash scripts/preflight_radeon.sh
```

**原生安装与训练。** 在此之前，应通过批准的 Radeon 环境安装支持 HIP 的 PyTorch 2.9.1 ROCm 7.2.1。`requirements.txt` 有意不安装通用 PyPI `torch`，以避免误装非 ROCm 构建。

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e . -r requirements.txt
export PYTHONPATH="$PWD/src"
bash scripts/preflight_radeon.sh
```

**复现专家/参考筛选与双视角。** 第一条命令对 10 个固定种子回合同时录制全景和腕部视频；第二条命令只保留 `success=true` 的 8 个回合，任何必要源视频或腕部视频缺失时都会停止。

```bash
python3 scripts/run_expert.py \
  --config configs/baseline.toml --backend rocm --episodes 10 \
  --record-video --output outputs/reproduce-expert

python3 videos/build_demo_video.py \
  --source-root outputs/reproduce-expert/expert \
  --font /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc \
  --out outputs/final-video
```

**验证。** 成功的 preflight 会报告一张 HIP 可见 GPU。数据、训练、测试和交付边界见 [data/README.md](data/README.md)、[docs/TRAINING_EVIDENCE.md](docs/TRAINING_EVIDENCE.md)、[docs/TEST_REPORT.md](docs/TEST_REPORT.md)、[videos/README.md](videos/README.md) 和 [docs/SUBMISSION_CHECKLIST.md](docs/SUBMISSION_CHECKLIST.md)。严格 VLA 结果仍为 0/3，未通过。
