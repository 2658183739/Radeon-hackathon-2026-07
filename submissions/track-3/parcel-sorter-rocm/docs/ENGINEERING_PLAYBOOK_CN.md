# 工程流程与学习手册

本文把本项目的开发过程整理成一套可复现、可审计、适合学习的工作流。它记录可观察的证据、代码能力、决策和验证方式，不输出隐藏的逐字思维链。每次新增实验都应遵循同样的格式，并在英文文档中同步更新。

## 1. 先固定目标和边界

本项目的目标是：在单张 AMD Radeon GPU 上，用 ROCm 完成仿真、传感、策略推理和闭环动作执行，完成快递包裹抓取、搬运和二分拣。当前主线是 Franka Panda + Genesis + RGB/RGB-D + ACT，确定性安全控制器始终位于学习策略之后。

不能把以下内容写成已经完成的能力：没有通过固定留出集的学习策略、只完成单步训练的 Diffusion、尚未通过许可证与 ROCm 审计的 VLA、没有对应末端执行器的吸盘或 cradle 场景，以及尚未实现的 ROS 2 桥接。

每项能力都用三种状态标记：

| 状态 | 含义 | 允许写法 |
| --- | --- | --- |
| 已验证 | 在锁定环境和明确 episode 上重复通过 | “已在 Radeon 上验证” |
| 链路烟雾 | 接口、训练或加载能运行，但任务能力未证明 | “完成链路烟雾” |
| 计划/边界 | 尚未实现或未达到验收门槛 | “计划中/当前不支持” |

## 2. 每次改动的标准步骤

### 步骤 A：提出一个可测问题

从失败轨迹或性能数据开始，例如“邮筒接近时发生碰撞”“RGB-D 深度单位不一致”“ACT P95 延迟过高”。不要从模型名称开始，也不要同时修改物理、数据和模型三个层面。

### 步骤 B：建立可重放基线

先固定 `git` 提交、配置文件、环境版本、单卡设备、随机种子、episode 清单、安全阈值和输出目录。基线至少保存原始 JSON、日志、配置副本和 SHA-256。

### 步骤 C：写契约和测试

在改实现前，先把输入、输出、单位、形状、允许范围、错误码和安全条件写成代码契约。优先添加单元测试，再做单 episode 烟雾，最后才进行多回合实验。

### 步骤 D：一次只改变一个主要变量

例如只改 `final_approach_step_m`，或者只改 `ACT_USE_DEPTH`。数据拆分、seed、预算和评测 episode 不变。若必须同时改多个变量，必须拆成独立实验并说明原因。

### 步骤 E：按四类指标验收

每个候选同时记录：

1. 任务：总成功、首次成功、重试恢复、掉落，以及按 profile 分层结果；
2. 安全：峰值接触力、35 N 中止次数、越界后是否继续执行；
3. 性能：平均/P95 推理延迟、训练吞吐、峰值显存、GPU 利用率；
4. 可复现性：命令、环境、seed、数据清单哈希、检查点哈希和日志路径。

吞吐提高但任务或安全退化时，候选必须拒绝。小样本结果同时报告分子、分母和 Wilson 95% 区间，不能只展示百分比。

### 步骤 F：记录保留、拒绝或待定

实验结束后立即更新双语日志：保留说明、拒绝原因、失败证据和下一步。失败结果不能删除或覆盖；应放入 `evidence/` 作为负对照。

## 3. 当前代码能力地图

| 能力 | 代码位置 | 当前验证 | 下一项增强 |
| --- | --- | --- | --- |
| 配置与范围校验 | `src/parcel_sorter/config.py` | TOML、冻结配置、非法范围单测 | 增加配置版本和迁移检查 |
| 随机化与 episode 调度 | `src/parcel_sorter/randomization.py`, `episode_plan.py` | 稳定 seed、profile 分层单测 | 记录每个随机变量的分布摘要 |
| Genesis 物理环境 | `genesis_env.py`, `runner.py` | Box/Cylinder、Franka、两格分拣 | V 型 cradle、定位槽和更真实材质 |
| 感知数据 | `dataset.py`, `data_quality.py` | RGB、米制深度、状态、接触力 | RGB-D 对齐检查、点云缓存和遮挡标记 |
| 专家控制 | `expert.py`, `state_machine.py` | IK/PD、接触确认、重试、释放检查 | 失败恢复策略和末端执行器切换 |
| 安全监督 | `policy.py`, `contracts.py` | 有限值、四元数、步长、35 N 中止 | 速度/加速度/碰撞能量联合门控 |
| 数据拆分 | `dataset_split.py`, `build_dataset_split.py` | 固定 seed、按 profile、held-out 隔离 | 生成机器可读的清单摘要和签名 |
| ACT | `train_act_rocm.sh`, `evaluate_act.py` | Radeon 训练/保存/加载/闭环接口 | 三 seed RGB 与 RGB-D 固定留出比较 |
| Diffusion | `train_diffusion_rocm.sh` | 轻量配置单步烟雾 | 5/10/20 去噪步数匹配评测 |
| ROCm 性能 | `preflight_radeon.sh`, `benchmark_*` | HIP 设备门禁、AMP、并行仿真 | 分阶段 profile 和编译/eager 对照 |
| VLA | `train_smolvla_rocm.sh` | 仅保留兼容性入口 | 递归许可证、算子和离线权重双门禁 |
| ROS 2 | 预留接口 | 尚未实现 | 仿真契约稳定后做可选桥接 |

## 4. 优化顺序和原因

1. **数据质量优先。** 先完成至少 300 个按 profile 均衡的成功 RGB-D 回合；否则模型比较反映的是采样偏差。
2. **ACT 先于 Diffusion/VLA。** ACT 参数量和推理延迟较低，适合建立可重复主线；Diffusion 作为动作多峰对照，VLA 只负责高层语义路由候选。
3. **安全控制器不交给大模型。** 模型只输出 8 维笛卡尔动作，IK、PD、夹爪阶段和力门限仍由确定性监督器执行，避免模型直接产生危险力矩。
4. **RGB-D 采用匹配消融。** 相同清单、seed、训练步数和闭环 episode 下比较 RGB 与 RGB-D，只有成功率提升且安全、延迟不退化时才保留深度。
5. **物理问题先于控制调参。** 采样尺寸、半径、摩擦和 solver 作用域必须先正确；不能用控制器参数掩盖模型几何错误。
6. **先测量再做 ROCm 优化。** 分开仿真步进、渲染、主机到设备传输和网络推理的耗时，再选择 AMP、batch、编译或缓存优化。
7. **最后扩展 VLA、点云和 ROS 2。** 这些会增加依赖、许可证和部署风险，必须在主线达到任务和安全门槛后加入。

## 5. 实验记录模板

每个实验至少包含以下字段：

```text
ID / 日期：
问题与失败证据：
基线提交、配置、环境和数据清单：
候选方案：
只改变的主要变量：
任务、安全、性能指标：
命令与输出路径：
结果：保留 / 拒绝 / 待定：
决策原因：
复盘条件与下一步：
```

建议把结构化结果保存为 JSON/CSV，把解释写入 `DEVELOPMENT_JOURNAL_CN.md` 和对应英文日志。这样既能人工学习，也能让脚本自动生成报告。

## 6. 复现与发布门禁

发布前依次执行：

```bash
bash scripts/preflight_radeon.sh
python -m unittest discover -s tests -q
python -m compileall -q src scripts
python scripts/audit_dataset.py --dataset-root <dataset> --require-depth-rgb
python scripts/build_dataset_split.py --audit-root <audit> --dataset-root <dataset> \
  --output <split.json> --seed 20260725
MODEL_SWEEP_MODELS=act MODEL_SWEEP_SEEDS=11,22,33 \
  bash scripts/run_model_sweep_rocm.sh <dataset> <split.json> <output>
```

最终提交必须包含源码、配置、Dockerfile、锁定版本、双语 README、技术报告、数据集卡、模型卡、实验日志和可复现命令。数据集和权重过大时不直接提交 Git，而是提交下载说明、哈希和许可证明。

## 7. 学习重点

先阅读 `PROJECT_STATUS_CN.md` 了解当前边界，再阅读 `DEVELOPMENT_JOURNAL_CN.md` 观察失败如何驱动代码改动，最后阅读 `ENGINEERING_DECISION_LOG_CN.md` 对照具体决策。每次学习一个模块，都回答三件事：输入契约是什么、失败如何被观测、结果如何被复现。

