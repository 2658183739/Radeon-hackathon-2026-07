# 模型与平台选型

## 1. 结论

本项目采用一条分层路线，而不是把所有能力压在一个大模型上：

1. **Genesis + Franka Panda**负责物理仿真、相机、接触与动作执行；
2. **确定性监督器 + IK/PD**负责阶段管理、运动边界、重试与力安全；
3. **ACT**作为已经在 Radeon/ROCm 上跑通的低成本学习基线；
4. **Diffusion Policy**作为第二条常规模仿学习对照；
5. **SmolVLA**作为轻量语言条件 VLA 微调路线；
6. Pi0、Pi0.5、OpenVLA、RDT 等模型只作为兼容性实验，不进入当前可复现承诺。

这样做的原因是比赛首先按任务完成效果评分。大模型不能替代稳定的接触控制、数据质量、
闭环评估和 Radeon 证据。

## 2. 硬约束

| 约束 | 工程处理 |
| --- | --- |
| 单张 AMD Radeon GPU | `HIP_VISIBLE_DEVICES=0`，预检要求只看到一张设备 |
| ROCm 开源栈 | PyTorch ROCm、Genesis `gs.amdgpu`、`torch.version.hip` 证据 |
| 开源仿真与模型 | Genesis、LeRobot、PyTorch，版本由 `UPSTREAM_LOCK.json` 固定 |
| 云端可复现 | 裸机启动脚本、固定配置、单元测试、Dockerfile 和逐步 README |
| 不泄漏仿真真值 | 7 维包裹位姿只进审计数据，不进入策略输入 |
| 闭环安全 | 所有学习策略共用末端步长、IK、PD、夹爪和 35 N 力边界 |

PyTorch ROCm 沿用 `torch.cuda` Python 接口，所以代码中的 `cuda` 表示 HIP 设备，并不
表示使用 NVIDIA CUDA。预检会拒绝 `torch.version.hip` 为空的环境。

## 3. 候选模型比较

| 模型 | 作用 | 优点 | 主要风险 | 当前状态 |
| --- | --- | --- | --- | --- |
| 几何专家 | 数据与能力上限基线 | 可解释、可重放、无需训练 | 泛化依赖规则覆盖 | 已实现、已实测 |
| ACT | 第一学习基线 | 小、快、动作分块成熟 | 数据少时容易过拟合 | 已训练、已闭环评测 |
| Diffusion Policy | 强常规对照 | 多峰动作建模好 | 迭代去噪增加延迟 | 训练入口就绪，未宣称结果 |
| SmolVLA | 语言条件轻量 VLA | 约 500M 级 VLM，单卡可微调 | 下载、ROCm 算子和视觉微调需实测 | 微调入口就绪，未宣称结果 |
| Pi0/Pi0.5 | 前沿 VLA 对照 | 公开实现、能力上限高 | 依赖和显存更重 | 兼容性门控 |
| OpenVLA/RDT | 研究扩展 | 社区资料多 | 不属于当前固定 LeRobot 主路径 | 不承诺交付 |

## 4. 输入、输出与模型职责

当前学习输入为：

- `observation.images.overhead_rgb`：`3 x 224 x 224`；
- `observation.state`：20 维，包括 9 维关节、7 维末端位姿、3 维目标和 1 维接触力；
- `task`：自然语言任务，SmolVLA 使用，ACT/Diffusion 可忽略；
- 深度：以米保存，当前不接入 RGB 模型，用于受控 RGB-D 融合实验。

模型输出 8 维笛卡尔动作：位置、四元数和夹爪命令。模型不直接输出关节力矩。动作仍要
经过有限值检查、四元数归一化、位移限幅、IK、PD、夹爪阶段约束和接触力中止。

## 5. 推荐执行顺序

### 阶段 A：保持 ACT 基线可复现

用相同数据重新训练 ACT，并在互不重叠的 episode 上选择检查点。验收依据是闭环成功率，
而不是只看训练 loss。

### 阶段 B：训练 Diffusion 对照

```bash
DIFFUSION_STEPS=30000 DIFFUSION_BATCH_SIZE=32 \
bash scripts/train_diffusion_rocm.sh \
  outputs/radeon-dataset-120/expert/lerobot_dataset \
  outputs/train/diffusion-radeon
```

默认 horizon 为 32、每次执行 8 步、推理去噪 10 步，在动作连续性与实时延迟之间取平衡。
先比较成功率和 P95 延迟，再决定是否增加去噪步数。

### 阶段 C：微调 SmolVLA

```bash
SMOLVLA_STEPS=4000 SMOLVLA_BATCH_SIZE=4 \
SMOLVLA_POLICY_PATH=/workspace/models/smolvla_base \
bash scripts/train_smolvla_rocm.sh \
  outputs/radeon-dataset-120/expert/lerobot_dataset \
  outputs/train/smolvla-radeon
```

先在可联网机器下载开源 `lerobot/smolvla_base` 并传到云端，再显式提供本地路径。比赛实例
当前无法访问 Hugging Face，因此脚本不会静默依赖下载。首轮冻结视觉编码器，只训练动作
专家相关部分，这是最稳妥的显存和过拟合控制。只有基线闭环稳定后，才设置：

```bash
SMOLVLA_POLICY_PATH=/workspace/models/smolvla_base \
SMOLVLA_FREEZE_VISION_ENCODER=false \
SMOLVLA_TRAIN_EXPERT_ONLY=false \
SMOLVLA_STEPS=2000 \
bash scripts/train_smolvla_rocm.sh <dataset> <new-output>
```

视觉解冻必须使用新的输出目录，并与冻结视觉的同数据、同评测 episode 对照。

## 6. Radeon 优化矩阵

每种模型只改变一个主要变量：

| 实验 | 变量 | 保持不变 | 主要指标 |
| --- | --- | --- | --- |
| 精度 | FP32 / AMP | 数据、seed、步数 | samples/s、显存、成功率 |
| batch | 4/8/16/32 | 精度、数据、步数 | GPU 利用率、吞吐 |
| Diffusion 去噪 | 5/10/20 | 检查点、episode | P95 延迟、成功率 |
| SmolVLA 视觉 | 冻结/解冻 | 数据、评测集 | 未见包裹成功率、过拟合 |
| 编译 | eager/compile | 模型、batch | 首次编译成本、稳态延迟 |

任何优化都必须同时报告任务、安全和性能。吞吐提高但成功率明显下降，或通过提高 35 N
阈值隐藏碰撞，都不接受。

## 7. 当前边界

- ACT 的数据、训练、保存、重载、ROCm 推理和 Genesis 闭环已经验证；
- Diffusion 已完成原始与轻量配置的 1 步 Radeon 训练烟雾；轻量配置把 UNet 从
  `[512,1024,2048]` 改为 `[256,512,1024]`，为 76.6M 参数；这只是资源和链路结果，
  不是任务能力结果；
- SmolVLA 脚本已按 LeRobot 0.6.1 接口准备，但基座权重需先离线传入，尚无正式训练结果；
- 当前 96 个成功回合不足以证明 VLA 泛化，先扩充目录化专家数据；
- 圆柱仍暴露平行夹爪几何和控制边界，不能靠更大模型自动掩盖；
- 深度已采集但未进入模型，RGB-D 融合仍是待做实验。

## 8. 模型验收门槛

模型进入演示前至少满足：

1. 在固定且未参与选模的 20 个闭环 episode 上评测；
2. 报告总体及按包裹 profile 分层成功率；
3. 无超过 35 N 后继续执行的情况；
4. 记录平均/P95 推理延迟、峰值显存与 GPU 利用率；
5. 权重、数据和配置带 SHA-256；
6. 结果能从最终 Git 提交重新产生。
