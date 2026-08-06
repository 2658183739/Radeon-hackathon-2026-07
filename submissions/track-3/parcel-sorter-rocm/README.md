# Parcel Sorter ROCm

Parcel Sorter ROCm runs a Genesis parcel-sorting workcell on one AMD Radeon GPU
with ROCm 7.2.1. The included 45.6-second video joins eight successful fixed-seed
episodes controlled by `ScriptedPickPlaceExpert + ClosedLoopSupervisor`.
Those are scripted expert/reference trajectories, not VLA or real-robot runs.

Parcel Sorter ROCm 在一张 AMD Radeon GPU 上通过 ROCm 7.2.1 运行 Genesis 包裹分拣工位。随仓库提供的 45.6 秒视频按原顺序拼接 8 个固定种子成功 episode，控制器是 `ScriptedPickPlaceExpert + ClosedLoopSupervisor`。这些是脚本专家/参考轨迹，不是 VLA 或真实机器人运行。

[Watch the local demo](videos/genesis_panda_8_success_reference_demo.mp4) · [Results](docs/RESULTS.md) · [Architecture](docs/ARCHITECTURE.md) · [Dataset status](data/README.md) · [Submission materials](submission_materials/README.md)

## 1. Project Overview / 项目简介

The task is small on purpose: pick a randomized parcel, carry it across a
fixed Panda workcell, and release it in the requested bin. Genesis runs the
physics; the project supplies the scene randomization, controller, safety
checks, records, and Radeon execution path.

任务被刻意控制在一个明确范围：抓取随机包裹，在固定 Panda 工位内搬运，再放入指定格口。Genesis 负责物理仿真；本项目实现随机化场景、控制器、安全检查、记录和 Radeon 运行路径。

The video is a useful starting point because every shown episode has a matching
result record. The controller reads privileged simulator state and advances
through approach, grasp, lift, transport, and release. This makes it a reliable
way to inspect the workcell, but it does not make the learned policy successful.

视频中的每个 episode 都有对应结果记录。控制器读取仿真特权状态，依次完成接近、抓取、抬升、搬运和释放。它适合审查工位和脚本控制，但不能据此说明学习策略已经成功。

## 2. Development Process / 开发过程

The first hard problem was not training loss. Raw learned actions often looked
close to the expert action yet exceeded an execution limit. We kept those
failures, added Cartesian, force, IK, and tool-command checks, and measured the
effect without folding it into the scripted result.

最先暴露的问题不是 loss，而是原始学习动作看起来接近专家动作，却经常越过执行边界。我们保留这些失败，加入笛卡尔、力、IK 和工具指令检查，并把它们与脚本结果分开统计。

The learned route has two distinct records. In the 42-sample offline action
test, raw VLA passes 0/42 checks; safety-clipped VLA and Harness-Lite pass
42/42. This answers whether an action fits the execution contract, not whether
it finishes the parcel task. The strict pure-VLA run owns all declared actions
and scores 0/3.

学习路线有两类独立记录：42 个离线动作样本中，原始 VLA 通过 0/42，安全裁剪 VLA 和 Harness-Lite 通过 42/42。这回答的是动作是否符合执行合约，不是是否完成分拣任务。严格纯 VLA 由学习策略负责全部声明动作，结果为 0/3。

The next engineering step is more diverse successful demonstrations and another
strict paired run, not a larger headline. GPT-5.6 Luna/Codex Runtime may assist
development and review work; it is not a runtime controller.

下一步是收集更多样化的成功示范并重新进行严格配对评测，而不是扩大标题数字。GPT-5.6 Luna/Codex Runtime 只用于开发和审阅，不参与运行时控制。

## 3. Source Attribution / 代码来源说明

| Component | Source | Project work |
| --- | --- | --- |
| Genesis 1.2.3 | `Genesis-Embodied-AI/genesis-world` | Parcel scene, sensors, Radeon scripts, records and tests |
| LeRobot 0.6.1 | `huggingface/lerobot` | Local SmolVLA/PI0.5 adapters and training contracts |
| Franka Panda MJCF | Genesis-distributed Panda asset | Versioned parcel-tool variants; upstream meshes remain attributed |
| This repository | `src/parcel_sorter/`, `scripts/`, `configs/` | Scripted controller, task logic, safety gates, data audits and reports |

Genesis、LeRobot 和 Panda 资产的锁定版本与许可证记录在 `UPSTREAM_LOCK.json` 和 `THIRD_PARTY_NOTICES.md`。本项目不把上游资产或代码表述为原创。

## 4. Team Roles / 团队分工

`2658183739` is the sole submitter and reviewed the system design, experiments,
evidence, and final release. GPT-5.6 Luna/Codex Runtime was used as a development
tool for bounded implementation and review tasks. It does not receive robot
observations or send robot actions.

`2658183739` 是唯一提交者，负责审核系统设计、实验、证据和最终发布。GPT-5.6 Luna/Codex Runtime 是用于限定开发与审阅工作的工具，不接收机器人观测，也不发送机器人动作。

## 5. Install and Run / 安装与运行

The recorded runtime is Linux, one `gfx1100` Radeon GPU, ROCm 7.2.1, PyTorch
2.9.1 ROCm, Genesis 1.2.3, LeRobot 0.6.1, and Python 3.12. `cuda:0` means the
HIP device here. Docker applies `requirements-lock.txt`, captured from that
completed Radeon runtime, as an exact package constraint set.

记录运行环境为 Linux、单张 `gfx1100` Radeon GPU、ROCm 7.2.1、PyTorch 2.9.1 ROCm、Genesis 1.2.3、LeRobot 0.6.1 和 Python 3.12。本项目中的 `cuda:0` 指 HIP 设备。Docker 会把该 Radeon 已完成运行环境导出的 `requirements-lock.txt` 作为精确依赖约束。

```bash
docker build -f Dockerfile.rocm -t parcel-sorter-rocm .
docker run --rm --device=/dev/kfd --device=/dev/dri --group-add video \
  -v "$PWD/outputs:/workspace/parcel-sorter-rocm/outputs" parcel-sorter-rocm
```

The image runs `scripts/run_demo.sh`: one fixed-seed, checkpoint-free scripted
episode with video recording and a fail-on-unsuccessful exit code. For a native
environment:

镜像执行 `scripts/run_demo.sh`：运行一个固定种子、无需 checkpoint 的脚本 episode，保存视频，并在失败时返回非零退出码。原生环境可运行：

```bash
source scripts/activate_radeon_env.sh
bash scripts/preflight_radeon.sh
bash scripts/run_demo.sh
```

The submitted SmolVLA checkpoint records a 7-episode, 4,557-frame training
dataset, but that original binary payload is no longer present locally or on
the Radeon workspace. A separate 7-episode success-trajectory release is
included with the local delivery; it is not attributed to this checkpoint.

提交的 SmolVLA checkpoint 记录使用 7 个 episode、4,557 帧训练，但该原始二进制
payload 已不在本地或 Radeon 工作区。最终本地交付另带一套 7 episode 成功轨迹
数据集，但不把它归因到该 checkpoint。
