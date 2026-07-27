# Parcel Sorter ROCm 中文说明

这是一个面向 AMD Physical AI 赛道的小快递抓取与分拣项目。系统在单张
AMD Radeon GPU 和 ROCm 上完成 Genesis 物理仿真、Franka Panda 机械臂控制、
RGB-D 数据采集、ACT 训练、闭环推理、离屏录像和性能测试。

最新的接触/目标纠错版移除了吸盘机械臂上“关闭碰撞但仍显示”的 Panda 旧手指，
把接触目标从 3.0 mm 穿入降为 0.5 mm，并要求连续 12 个真实接触物理步后才能锁存。
快递与指定目标台现在使用同色高可见标记，43 维状态中的目标坐标也修正为底盘世界坐标。
新候选使用 2723 帧审计通过的 RGB-D 数据训练 SmolVLA 2800 步；四类开发门为 4/4，
运输方向错误 0 次、运输阶段专家回退 0 次、VLA 到站确认全部通过、35 N 越界 0，
放置误差 0.60--0.92 cm。该结果是经过开发集选择的小样本机理门，不是冻结成功率，
也不代表已经完成开放世界多目标站分类。
哈希和精简指标见
[`evidence/mobile_bimanual/goal_marker_vla_v1/result.json`](evidence/mobile_bimanual/goal_marker_vla_v1/result.json)。

移动扩展的最新结果见[Harness-Lite 与失败驱动自我改进](docs/MOBILE_HARNESS_SELF_IMPROVEMENT_2026-07-27_CN.md)：
SmolVLA v2在六个成功专家回合上训练2400步，完成36样本动作包络消融，并在抓取接近与30 cm
运输阶段实际控制有界底盘残差。早期五回合门禁得到4/5；后续独立 100 回合基线达到 96/100，
并由下面的自我改进周期完成统计晋级审计。广泛未见几何体泛化仍未验证。
新的[自动自我改进周期](docs/MOBILE_SELF_IMPROVEMENT_CYCLE_CN.md)把失败课程、Radeon 再训练、
配对 100 回合冻结评估和隔离晋级串成一条可恢复命令；候选未过 80%/安全/ROCm 门时不会替换权重。
该周期已实际跑完：v2 基线为 96/100，桥接训练后的 v3 为 91/100；v3 放置误差更低但未通过
Wilson 不劣性门，因此自动隔离且未替换 v2。
新的[配对 RGB-D 消融](docs/MOBILE_RGBD_ABLATION_CN.md)已验证 ROCm 双图 SmolVLA 训练和在线控制。
RGB-D 完成一个开发任务，但 Harness 配对 MAE 回归 1.35%、离线延迟增加 9.65%，因此门禁保留 RGB，
不启动 100 回合 campaign。
新的[左臂残差配对消融](docs/MOBILE_ARM_RESIDUAL_ABLATION_CN.md)让 SmolVLA 在运输阶段真实控制
有界左臂位置残差。新冻结集上基线和候选均为 94/100、零力越界，候选 2306 次 IK 全接受，
但平均放置误差从 1.40 cm 增至 2.45 cm，超过预注册精度容差，因此未晋级，v2 继续只执行底盘残差。
新的[三吸盘/V 型托架协同消融](docs/MOBILE_COOPERATIVE_CRADLE_ABLATION_CN.md)已在单张 Radeon 上
完成 1.44 m 超长纸箱的双臂抬升、30 cm 运输、放置和释放。SmolVLA v2 实际参与 647 个物理步，
负载感知 Harness 在时间容量不足时单向交还专家；最终误差 2.16 cm、峰值托架力 30.65 N。
该结果是单案例机理证据，不替换 96/100 正式基线，也不宣称未见几何泛化。
当前方法卡见 [PASH-VLA：负载感知安全 Harness VLA](docs/PASH_VLA_METHOD_CN.md)：它把
SmolVLA、接触力短时记忆、Harness-Lite、三吸盘/V 型托架和失败驱动隔离晋级组合起来。力记忆
分支目前是显式开发候选，尚未在匹配 Radeon 评测通过前替换冻结 v2 权重。
对应的[论文蓝图](docs/PASH_VLA_PAPER_BLUEPRINT_CN.md)固定了研究问题、公式、消融表、图表规划、
证据边界和投稿诚信检查，英文版见 [Paper Blueprint](docs/PASH_VLA_PAPER_BLUEPRINT.md)。
新的[PASH 自适应重试与技能获取](docs/PASH_ADAPTIVE_RETRY_CN.md)加入 primitive 缺口诊断、
任务/全局双层策略记忆、最多三次独立审计尝试和隔离的技能写回。v2 在一个冻结 100 回合中
已知的抬升失败参数上，首试失败后自动选择 `pash_base@gentle_lift`，第二次成功并保存 673 帧
通过审计的 RGB-D/状态/动作数据；这是配对机理证据，不是总体恢复率。
新的[PASH Primitive 学习扩展](docs/PASH_PRIMITIVE_LEARNING_CN.md)把审计示范转换为六种 primitive
指令和一个进度通道。4,557 帧数据审计、2,800 步 Radeon 训练、42 样本离线 Harness 消融和
冻结 100 回合评估均已完成。候选为 94/100、零力越界，并通过与 96/100 基线配对的不劣性门；
`configs/active_mobile_smolvla.json` 现在以模型和晋升证据双哈希激活该 checkpoint。后续改进周期会
精确比较基线/候选的有序物理参数，并原子更新该指针；被拒绝的候选无法覆盖已部署 checkpoint。

英文 [README.md](README.md) 是评审复现的主入口；中文正式报告见
[TECHNICAL_REPORT_CN.md](TECHNICAL_REPORT_CN.md)。优化顺序见
[优化路线图](docs/OPTIMIZATION_ROADMAP_CN.md)，完整工程决策和代码学习记录见
[工程决策日志](docs/ENGINEERING_DECISION_LOG_CN.md)，逐次实验见
[开发日志](docs/DEVELOPMENT_JOURNAL_CN.md)，模型比较见
[模型选型](docs/MODEL_SELECTION_CN.md)。本轮逐步优化、代码能力与决策原因见
[2026-07-25 证据驱动优化记录](docs/OPTIMIZATION_SESSION_2026-07-25_CN.md)。
新增的[前沿研究与开源模型矩阵](docs/RESEARCH_AND_MODEL_MATRIX_CN.md)和
[RGB-D 多模态优化记录](docs/MULTIMODAL_OPTIMIZATION_2026-07-25_CN.md)分别说明模型取舍、
许可证边界和本轮逐步实现/失败/验证过程。
末端执行器的已实现范围与扩展门禁见[能力契约](docs/END_EFFECTOR_CAPABILITY_CN.md)，当前只对平行夹爪闭环结果做正式声明。

如果你要按规范学习“需求 -> 契约 -> 代码 -> 实验 -> 验收 -> 发布”的完整流程，请先读
[工程流程与学习手册](docs/ENGINEERING_PLAYBOOK_CN.md)；英文版见
[Engineering Playbook](docs/ENGINEERING_PLAYBOOK.md)。

本轮新增的采集规划、逐层代码能力、优化优先级、可执行 Radeon 流程和决策依据集中在
[实施与优化学习记录](docs/IMPLEMENTATION_AND_OPTIMIZATION_RECORD_CN.md)；英文配套版本见
[Implementation and Optimization Record](docs/IMPLEMENTATION_AND_OPTIMIZATION_RECORD.md)。

当前能力、未实现边界和推荐复现顺序见[项目状态与复现协议](docs/PROJECT_STATUS_CN.md)，
英文评审入口为 [PROJECT_STATUS.md](docs/PROJECT_STATUS.md)。
最新 Radeon 几何规划方法、顺序探针、正式 20+20 结果和剩余边界见
[几何感知抓取规划](docs/GEOMETRY_AWARE_GRASP_PLANNING_CN.md)；英文版见
[Geometry-Aware Grasp Planning](docs/GEOMETRY_AWARE_GRASP_PLANNING.md)。
开源指尖承托几何、Radeon 配对证据与实体迁移边界见
[包裹夹爪适配器](docs/PARCEL_GRIPPER_ADAPTER_CN.md)；英文版见
[Open-Source Parcel Gripper Adapter](docs/PARCEL_GRIPPER_ADAPTER.md)。

## 系统组成

- Genesis 刚体物理环境、Franka Panda、Box/Cylinder 快递和左右分拣格口
- catalog v1 的 7 类带权训练包裹，以及 catalog v2 的 12 类均衡训练分层；另有 9 类仅评测行业尺寸边界（原有 4 类加本轮新增 5 类）和稳定的分层 episode 调度
- 顶视 RGB-D 相机、关节位置、末端位姿、目标位置和夹爪接触力
- IK 专家、机械臂 PD 控制、夹爪力斜坡和末端步长限制
- 检测、接近、抓取、接触验证、抬升、搬运、释放、重试和安全中止闭环
- JSONL 全量审计轨迹和 LeRobotDataset 成功专家回合
- 52M 参数 ACT 基线、Diffusion 的 Radeon 训练入口和通用闭环评测适配器
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
| 历史 RGB/状态数据 | 96 回合，11,753 帧；深度不可用于 RGB-D |
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
| 大纸箱几何规划困难集 | 基线 5/20，候选 15/20；实验能力，未通过发布门禁 |
| 移动 SmolVLA v2 冻结集 | 96/100，0 次 35 N 力越界 |
| 自我改进 SmolVLA v3 | 91/100，Wilson 非劣性失败，未晋级 |
| Primitive-progress SmolVLA | 94/100，0 次力越界，通过配对不劣性门并激活 |
| 已知失败自适应恢复 | 首试抬升失败，第二次成功；673 帧恢复数据审计通过 |
| 超长箱双臂协同开发案例 | 抬升 8.53 cm、运输 30 cm、误差 2.16 cm、0 断吸 |
| 移动主线定向测试 | Radeon 上 48 项通过 |
| 真实接触目标条件 VLA 开发门 | 4/4；0.5 mm 接触、12 步密封、VLA 到站确认、0 次力越界 |

移动 SmolVLA v2 的 96/100 是保留基线，primitive-progress 模型以 94/100 通过预注册不劣性门并
成为活动 checkpoint；正式专家 120 回合和 ACT 作为历史受控基线保留。超长箱结果只证明双臂协同
机理可运行，不是统计泛化。ACT 已证明数据、训练、保存、
重载、ROCm 推理和 Genesis 闭环全部跑通，但成功率明显低于专家。相同 episode 10-19 上，
第 4,000 步优于第 5,000 步，也说明模型选择不能只看离线 loss。

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

做 reset 姿态诊断时，保持基线配置不变，只通过九个关节参数覆盖 home 姿态。覆盖值会写入
`summary.json`，因此运行仍可审计。候选姿态必须在 Radeon 上经过匹配的任务、安全和吞吐门禁后，
才能接收为默认值：

```bash
python scripts/run_expert.py \\
  --config configs/catalog_v2.toml --backend rocm \\
  --episodes 20 --start-episode 0 --profile large_narrow_carton \\
  --reset-qpos -1.0124 1.0 1.4 -1.6878 -1.5799 1.7757 1.4602 0.04 0.04 \\
  --output outputs/diagnostics/large-narrow-home-c
```

固定的 20 episode Radeon 验收协议也已封装为一条命令。脚本会拒绝复用已有输出目录，以相同 profile 和
随机样本依次运行基线与候选 C，比较两份 summary，并写出 `SHA256SUMS`：

```bash
bash scripts/run_reset_pose_ab_rocm.sh \
  configs/catalog_v2.toml outputs/radeon-reset-ab-v1
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
审计，不输入模型。历史 `radeon-dataset-120-v1` 的深度曾被错误乘以 `0.001`，因此它只可
复现已有 RGB ACT，不可用于 RGB-D。修复后新采数据同时包含米制原始深度和三通道深度视图。

训练前先做门禁：

```bash
python scripts/audit_dataset.py --dataset-root <lerobot_dataset>
python scripts/audit_dataset.py --dataset-root <lerobot_dataset> --require-depth-rgb
```

采集完成后，训练前先冻结 train/validation/held-out 拆分，不能在不同模型之间重新随机拆分：

```bash
python scripts/build_dataset_split.py \
  --audit-root outputs/radeon-dataset-400-v2/expert/audit_dataset \
  --dataset-root outputs/radeon-dataset-400-v2/expert/lerobot_dataset \
  --output outputs/radeon-dataset-400-v2/dataset-split.json \
  --seed 20260725
```

清单按包裹 profile 分层，并记录原始确定性 episode ID 与 LeRobot 紧凑 episode 索引，
held-out 回合完全排除出训练。所有匹配实验使用同一清单：

```bash
DATASET_SPLIT_MANIFEST=outputs/radeon-dataset-400-v2/dataset-split.json \
ACT_SEED=11 ACT_STEPS=30000 ACT_USE_AMP=true \
bash scripts/train_act_rocm.sh \
  outputs/radeon-dataset-400-v2/expert/lerobot_dataset \
  outputs/train/act-rgb-seed11
```

Diffusion 入口也使用同一个 `DATASET_SPLIT_MANIFEST`。不同 seed、RGB 和 RGB-D 对照之间都不能重新生成清单。

## 可复现模型矩阵

先在单张 GPU 上顺序运行 ACT：

    MODEL_SWEEP_MODELS=act MODEL_SWEEP_SEEDS=11,22,33 \
    bash scripts/run_model_sweep_rocm.sh \
      outputs/radeon-dataset-400-v2/expert/lerobot_dataset \
      outputs/radeon-dataset-400-v2/dataset-split.json \
      outputs/model-sweep/act

ACT 门禁通过后，再把 MODEL_SWEEP_MODELS=act,diffusion 加入轻量 Diffusion 的 RGB/RGB-D
对照。矩阵会为每个模型/模态/seed 保存一行 CSV 和一份日志；失败运行会保留，不会静默改变后续实验条件。

在云端可以把等待采集完成、生成清单和启动矩阵连成一个可审计任务：

    nohup bash scripts/watch_and_train_rocm.sh outputs/radeon-dataset-400-v2 \
      > outputs/radeon-dataset-400-v2/watch-and-train.log 2>&1 &

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

使用修正后的新数据做匹配 RGB-D 实验时添加 `ACT_USE_DEPTH=true`。检查点会声明 RGB 与
深度视图两个输入，通用评测器会自动读取，不再依赖手工推理开关。RGB 对照必须保持数据
拆分、种子、训练步数和检查点计划一致，只把该变量设为 `false`。

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

## Diffusion 与 VLA 研究路线

```bash
bash scripts/train_diffusion_rocm.sh <lerobot_dataset> outputs/train/diffusion-radeon

# 轻量配置的正式消融入口
DIFFUSION_DOWN_DIMS=256,512,1024 DIFFUSION_HORIZON=32 \
DIFFUSION_N_ACTION_STEPS=8 DIFFUSION_INFERENCE_STEPS=10 \
bash scripts/train_diffusion_rocm.sh <lerobot_dataset> outputs/train/diffusion-compact
```

Diffusion 是已经准备好的训练入口，不是已经取得的比赛结果。轻量 Diffusion
已经在 Radeon 上完成 1 步前向、反向、优化器更新和保存：76,597,288 参数，训练进度
约 23.6 秒；这只证明入口和缩小模型可行，仍需完整训练与分层闭环评测。VLA-Adapter 0.5B
仍是尚未接入的比较候选。当前 VLA 主线使用 Apache-2.0 的 LeRobot SmolVLA，并以
Apache-2.0 的 `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` 固定 revision
`7b375e1b73b11138ff12fe22c8f2822d8fe03467` 初始化。10k checkpoint 是本项目
在单张 Radeon 上使用自建轨迹训练得到的派生权重。训练器生成的 `license` 字段为空，
因此任何单独分发都必须同时提供基础模型清单和派生 checkpoint 来源说明。评测器仍把它
放在相同的 Genesis 闭环和 35 N 安全边界之后。

## 冻结实验协议与类别汇总

需要快速查看移动 VLA 是否真的能抓取和搬运时，可直接运行四类快递冻结快速集。默认每类
3 次，共 12 回合；脚本自动生成按类别成功率、安全越界数和放置误差的 `REPORT.md`，并为
每类保存一个 640x480 MP4 与 PNG。该评测集明确标记为只评测，结果不会回流训练。

```bash
PYTHONPATH=src:. /workspace/rdna/bin/python scripts/run_mobile_quick_eval_rocm.py \
  --output outputs/mobile-quick-eval-12-v1 \
  --workers 4
```

增加 `--max-episodes 4` 可先做每类 1 次的画面预览。VLA 仍使用冻结的 224x224 RGB
观察；高清视频由独立展示相机生成，因此录像不会改变模型输入或评测条件。

任何远端实验前先校验版本化协议：

```bash
python scripts/validate_campaign.py configs/campaign_v1.toml
```

该协议固定 ROCm、单张 GPU、35 N 安全上限、目录哈希、评测回合、随机种子、
训练预算、开源声明和验收门槛。均衡 RGB-D 数据与拆分完成前，相关哈希明确
保持为 `PENDING`。

对已有专家或策略 summary 按箱体、圆柱和末端执行器处理类别汇总：

```bash
python scripts/summarize_categories.py outputs/.../summary.json
```

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

## 轮式双臂开发基线

当前主形态升级为全向轮式底盘和两条 Franka Panda 机械臂。
`mobile_bimanual.py` 在运行时读取 Genesis 中 Apache-2.0 的 Bi-Franka MJCF，
加入本项目原创的 `x/y/yaw` 平面底盘关节、实体底盘、车轮外观、限速导航命令、
双臂角色分配和快递语义分类路由；上游资产本身不复制进仓库。

在比赛 Radeon 上，生成的 21 自由度机器人已由 Genesis 1.2.3 成功编译，并在
240 个物理步中前移 0.13047 m，仿真报告约 494--516 FPS。闭环绕障随后用 321 个
控制步到达目标，最终误差 4.39 cm。14 个机械臂自由度的同步 IK 烟雾测试中，两侧
预抓取误差均不超过 1.60 cm，无新增碰撞，底盘漂移 1.35 mm，仿真速度 405 FPS。
后续三吸盘移动闭环已完成实体快递抓取、抬升、30 cm 运输、放置与释放；跨参数成功率以
SmolVLA v2 的独立冻结 96/100 为准。

混合末端在左臂安装 3 个实体吸盘碰撞体，在右臂安装两条 V 型托架碰撞轨。最新单案例在
Radeon 上搬运 `1.44 x 0.12 x 0.18 m` 纸箱：抬升 8.53 cm、移动 30 cm、放置误差 2.16 cm，
零断吸且峰值托架力 30.65 N。SmolVLA 在 Harness 下实际参与控制；完整消融见
`docs/MOBILE_COOPERATIVE_CRADLE_ABLATION_CN.md`。尚未完成多尺寸冻结评测，因此不作泛化声明。

`mobile_task.py` 将后续微调动作契约固定为 19 维：3 维限幅底盘速度，以及左右各
8 维笛卡尔位姿/夹爪命令。该模块也提供专家采集器与 SmolVLA 共用的失败闭合状态机，
覆盖导航、双侧接触确认、抬升、搬运、放置、有限重试和接触力中止。

```bash
python scripts/smoke_mobile_bimanual_rocm.py \
  --backend rocm --steps 240 --speed-m-s 0.20 \
  --output outputs/mobile-bimanual-smoke-v3
python scripts/smoke_mobile_bimanual_arms_rocm.py \
  --backend rocm --output outputs/mobile-bimanual-arms-v2
python scripts/smoke_mobile_bimanual_rocm.py --backend rocm --hybrid-tools \
  --output outputs/mobile-bimanual-hybrid-tools-v1
```

原始结果见
`evidence/mobile_bimanual/mobile-bimanual-smoke-v3.json`、
`mobile-navigation-v1.json`、`mobile-bimanual-arms-v2.json`、
`mobile-bimanual-hybrid-tools-v1.json`，以及保留的负结果
`mobile-bimanual-pick-v3-failure.json`。首次成功物理吸盘抬升证据为
`mobile-suction-lift-v40-success.json`。

## 开发过程

项目采用失败闭合的受控实验流程：先冻结 episode ID、安全阈值和评价指标，记录基线，
每轮只改变一个可归因机制，在同一张 Radeon 上执行配对实验，保留被拒绝候选，并且只在
独立留出集通过晋升门槛后替换 checkpoint。当前原创工作包括快递任务状态机、几何抓取
规划、三吸盘物理约束、Harness-Lite 生成器/验证器、失败回放隔离与晋升、自建数据集、
快递分类，以及轮式双臂形态。成功和失败实验都保存在 `docs/` 与 `evidence/`。

## 代码来源说明

`src/parcel_sorter`、`scripts` 和 `tests` 中的项目代码采用 MIT 许可证。运行依赖
按锁定 revision 下载，不把第三方仓库直接复制到提交目录。Genesis World 及其
Bi-Franka 资产、LeRobot/SmolVLA 实现、SmolVLM2 基础 checkpoint 均为
Apache-2.0；具体仓库、revision 和用途见 `THIRD_PARTY_NOTICES.md` 与
`UPSTREAM_LOCK.json`。轮式底盘、Harness-Lite 规则、吸盘约束、分类路由、实验编排
及生成数据是本项目修改，不是未修改的上游 fork。模型权重不提交到本 Git 仓库。

## 原始证据与剩余提交项

小体积的专家、ACT、训练和 benchmark 原始结果保存在 `evidence/`，数据集和 206 MB
模型权重不直接提交 Git。最终 PR 前仍需填写与 Luma 一致的团队名和法定姓名、上传
带 SHA-256 的正式权重与数据、录制 3-5 分钟演示视频，并从最终 Git 提交重新跑一次
完整流程。具体见 [SUBMISSION_CHECKLIST_CN.md](SUBMISSION_CHECKLIST_CN.md)。

## 2026-07-27 双臂几何 Harness 更新

新增 [PASH 双臂几何 Harness](docs/PASH_DUAL_ARM_DEPTH_CN.md)：冻结的 RGB SmolVLA 在运输阶段同时提出左右臂位置，系统先投影为刚体一致的共同运动，再进行双臂联合 IK；米制深度作为确定性风险侧路，接近放置点时学习式权限逐渐降为零。

单张 Radeon 上的固定 1.44 m 超长纸箱案例已通过：左右臂各有 24 次非零更新，双臂残差实际执行 2,356 个物理步，工具间距变化为 0，最终放置误差 3.19 cm，断吸为 0，最大托架接触力 30.68 N，未触发 35 N 安全线。该结果只证明机理闭环，不代表泛化成功率。
