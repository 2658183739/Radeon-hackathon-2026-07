# 2026 前沿方法路线图：多形状快递分拣、VLA、世界模型与 ROS 2

## 1. 本文档回答什么

本文档把当前项目与 2024--2026 年开源机器人方法对齐，并明确哪些方案应当
立刻做、满足门槛后再做、或只作为外部对照。目标不是堆模型名称，而是在单张
AMD Radeon、ROCm、Genesis 和现有 Panda 闭环上形成可归因、可复现、能写进
论文的正向方法。

当前主方法仍然是：

```text
包裹几何/状态
  -> 多候选抓取位姿
  -> IK、FK、碰撞与可操作度过滤
  -> 控制器保真动态安全探针
  -> 35 N 安全门控
  -> 闭环搬运与放置
```

VLA 适合放在高层任务解析或候选提议层，不适合在当前证据下直接替换低层关节
控制器。

## 2. 近期文献与开源实现给出的结论

| 方向 | 代表工作/实现 | 对本项目的价值 | 当前决策 |
| --- | --- | --- | --- |
| 统一 VLA 评测 | `allenai/vla-evaluation-harness` v0.4.0，Apache-2.0 | 将模型服务器与仿真 benchmark 解耦，支持 LeRobot、OpenVLA、PI 系列、VLA-JEPA 等 | 后续接入为外部评测适配层；它不是训练模型 |
| 力记忆 VLA | FM-VLA, arXiv:2607.18231 | 用紧凑力历史 token 处理视觉不可辨识的接触事件，论文报告 80% 以上成功且开销小 | 与 V4 动态探针最相关；先做解释性安全门，再考虑小型力 VAE/LoRA |
| 场景简化 | LENS, arXiv:2607.19633 | 闭环裁剪或合并杂乱场景实体，可改善经典规划、MPC 和 VLA | 当前单包裹场景收益有限；扩展多包裹/杂乱传送带后再做 |
| 物理世界模型 | PhysCoRe, arXiv:2607.20653 | 解析物理 + 学习残差 + 不确定性，适合可变形物体 | 当前刚性包裹不需要 MPM；可作为软袋/邮件袋远期路线 |
| Real2Sim | Agentic Real2Sim, arXiv:2607.19190 | 从视频恢复几何、物理参数和可运行数字孪生 | 有真实录像或机械臂后用于 sim-to-real；当前不替代正式控制实验 |
| 数据引擎 | AXIS, arXiv:2607.21588 | 50K+ 轨迹、自动质检、扰动和 held-out 协议；数据规模带来稳定增益 | 借鉴数据卡、质量过滤和任务快照，不复制其规模 |
| 零售人形 VLA | DEED, arXiv:2607.20345 | 单 GPU、频率对齐、数据筛选、减少 VLA 依赖比盲目微调更重要 | 支持当前“系统集成优先于换大模型”的判断 |
| 经典抓取/规划 | MoveIt 2、GPD、Dex-Net、GraspNet baseline | 提供运动规划、点云抓取、鲁棒抓取评分和通用基线 | MoveIt 2 可做 ROS 2 接口；其余多有 CUDA/旧依赖，不作为 AMD 主实现 |

检索时还发现 `vla-evaluation-harness` 的 LeRobot 桥在固定 v0.6.0 下正式复现
了 PI0.5、GR00T N1.7、MolmoAct2 和 VLA-JEPA 的 LIBERO 结果，但 SmolVLA 只有
加载与单步 smoke，FastWAM 在上游同版本也出现 0/20，说明“仓库支持”不能等价
于“结果可复现”。该经验应直接写进本项目的复现准则。

## 3. 方法优先级

### P0：完成当前 V5 独立确认

V5 使用 80 个全新组、8 个 profile、最多 480 条候选 rollout，只确认
`veto-static`。通过条件包括零成功损失、零安全/掉落回归、至少 6 次且分布在
至少 2 个 profile 的力中止减少，以及单侧精确检验不大于 0.05。

V5 完成前不修改被冻结的 `genesis_env.py`、`grasp_planning.py` 和提取器。

### P1：单 Radeon 在线并行短探针

若 V5 通过，当前最大的工程与学术增量不是换 VLA，而是把离线反事实探针变成
真正可部署的在线算法：

1. 在一个初始状态上生成 4--6 个候选。
2. 克隆同一确定性状态到多个 Genesis 环境。
3. 在单张 Radeon 上并行执行 approach、grasp、verify、micro-lift。
4. 在第一个 `place` 边界统一停止。
5. 根据固定资格门选出候选或安全放弃。
6. 只在主环境执行完整 transport/place。

必须分别报告：场景构建、状态克隆、内核编译、批量探针、主轨迹和选择器耗时。
当前顺序采集仅使用约 2% VRAM，GPU 忙碌度约 28%，说明并行化空间很大。

### P1：圆柱与快递筒抓取规划

当前箱体候选生成器不能用于圆柱。圆柱扩展应独立实现，不能把“没有候选”伪装
成控制失败。

建议候选族：

- 立式圆柱：四个绕轴等价侧抓取 yaw、两个高度偏移、对称腕部；
- 卧式圆柱：沿筒轴方向的纵向偏移、绕筒轴的接触角、对称腕部；
- 圆柱碰撞包络：用解析圆柱或保守胶囊体检查手掌、指尖与桌面间隙；
- 稳定性排序：夹爪闭合轴与圆柱径向对齐、重心臂、滚动方向风险、可操作度；
- 卧式筒体额外门：滚动摩擦不足时禁止单次侧抓，转为托举/挡轨能力边界。

正式比较应包含箱体规划器、圆柱规划器和错误地使用箱体近似的负对照。

### P1：ROCm 原生 RGB-D 几何感知

比直接接大 VLA 更适合当前任务的视觉增强是轻量 RGB-D 几何前端：

```text
深度图 -> PyTorch/ROCm 反投影 -> 桌面分割 -> 包裹点云
       -> PCA/有向包围盒 -> shape、尺寸、中心、yaw、置信度
       -> 几何候选规划与安全探针
```

该方法可在 Radeon 上训练一个小型置信度/残差头，也可先完全解析实现。评测要
同时包含真值状态、加噪真值和 RGB-D 估计三档，避免把仿真真值误称为视觉感知。

### P2：SmolVLA/ACT 高层候选提议

只有以下条件满足后才进入正式微调：

- 几何与圆柱规划主方法已有稳定正结果；
- 至少 500 条通过质量审计的 RGB-D/状态/动作轨迹；
- train/development/holdout 按物理 episode 和 profile 分组；
- 先冻结动作频率、图像键、状态维度、归一化和 action chunk；
- 模型不得绕过 35 N 安全监督器。

首选顺序：

1. 已有 ACT RGB-D 作为小模型基线；
2. SmolVLA LoRA 或只微调 action expert，输出高层抓取候选/目标，而非关节力；
3. FM-VLA 风格的力历史 token 消融；
4. 再考虑 PI0.5、VLA-JEPA 或更大世界模型。

每个模型都要与“参数量相近但无视觉/无力历史”的对照比较，并记录 ROCm 峰值
显存、训练吞吐、推理 P50/P95、首次编译和稳态延迟。

### P2：ROS 2 与 MoveIt 2 部署适配

ROS 2 不是比赛硬性条件，也不提高当前仿真成功率，因此放在算法结果之后。
推荐最小架构：

```text
/camera/rgb + /camera/depth + /joint_states
        -> parcel_perception_node
        -> grasp_candidate_node
        -> safety_probe_node
        -> FollowJointTrajectory / gripper command
        -> safety_monitor_node (35 N, drop, timeout)
```

使用 rosbag2 固定输入和回放闭环，MoveIt 2 仅负责现实机器人运动规划接口；论文
主结果仍来自同一冻结算法，而不是把 MoveIt 默认行为当成本文贡献。

## 4. 不应采用的捷径

- 不把 `torch.cuda` 字符串当作 NVIDIA 证据；ROCm 的 PyTorch 也使用该命名。
- 不把模型“能加载”写成闭环有效；至少需要固定未见 episode 的任务结果。
- 不在 V5 结果出现后调资格阈值、最小收益或 profile。
- 不把 USPS/FedEx 大箱尺寸直接交给 79 mm 平行夹爪并宣称可抓；超过能力包络
  的 profile 必须标记为 suction/cradle boundary。
- 不在一个实验里同时更换视觉、规划器、控制器和模型，否则无法归因。
- 不用 CUDA-only 自定义算子作为 AMD 主路径；若必须使用，只能作为外部参考。
- 不把世界模型生成的视频质量当成任务成功，需要物理状态和安全闭环验证。

## 5. 论文级实验矩阵

| 实验 | 必须对照 | 主要指标 |
| --- | --- | --- |
| 箱体主方法 | 历史基线、碰撞复位、完整几何规划 | 成功、力中止、掉落、峰值力、耗时、规划延迟 |
| 几何消融 | 无碰撞过滤、无可操作度、无对称腕、无 retry 重规划 | 配对变化与失败类型 |
| 动态安全探针 | 静态首选、V5 否决、在线并行否决 | 成功损失、安全减少、探针代价 |
| 多形状 | 方箱、长箱、扁平件、立式圆柱、卧式筒体 | profile 分层与宏平均 |
| 感知 | 真值、加噪真值、RGB-D 估计 | 位姿/尺寸误差和闭环成功 |
| 学习 | ACT、SmolVLA、高层几何 + 力记忆 | 未见 profile、鲁棒性、显存和延迟 |
| GPU | 顺序场景、并行探针、批量感知 | GPU 利用率、VRAM、吞吐、端到端 P95 |

统计使用配对 McNemar、Wilson 95% 区间、连续指标配对 bootstrap/符号翻转；若
profile 和扰动层级足够多，再补混合效应 logistic 模型。所有方法必须使用同一
episode、同一随机样本和同一 35 N 门。

## 6. 检索来源与复现信息

访问日期：2026-07-26。

- arXiv API：`https://export.arxiv.org/api/query`；查询
  `cat:cs.RO AND (contact-rich manipulation OR vision-language-action OR world model)`，
  按提交日期降序；随后按 ID 读取 2607.18231、2607.19633、2607.20653、
  2607.19190、2607.20345、2607.21588 的题目与摘要。
- OpenAlex API：`https://api.openalex.org/works`；2024-01-01 以后关键词检索
  contact-rich manipulation、VLA/world model、cylindrical grasp planning。
- GitHub API：仓库 metadata、README、tree 与至多三个目标文件；重点检查
  `allenai/vla-evaluation-harness`、`huggingface/lerobot`、`moveit/moveit2`、
  `atenpas/gpd`、`BerkeleyAutomation/dex-net`、`graspnet/graspnet-baseline`、
  `NVlabs/contact_graspnet`。

文献和仓库只证明方法与接口存在；是否能在本项目的 ROCm、gfx1100 和包裹闭环
上工作，必须由本仓库自己的 smoke、冻结协议和正式评测证明。

可核验入口：

- [FM-VLA](https://arxiv.org/abs/2607.18231)
- [LENS](https://arxiv.org/abs/2607.19633)
- [PhysCoRe](https://arxiv.org/abs/2607.20653)
- [Agentic Real2Sim](https://arxiv.org/abs/2607.19190)
- [DEED](https://arxiv.org/abs/2607.20345)
- [AXIS](https://arxiv.org/abs/2607.21588)
- [allenai/vla-evaluation-harness](https://github.com/allenai/vla-evaluation-harness)
- [huggingface/lerobot](https://github.com/huggingface/lerobot)
- [moveit/moveit2](https://github.com/moveit/moveit2)
- [atenpas/gpd](https://github.com/atenpas/gpd)
- [BerkeleyAutomation/dex-net](https://github.com/BerkeleyAutomation/dex-net)
- [graspnet/graspnet-baseline](https://github.com/graspnet/graspnet-baseline)
- [NVlabs/contact_graspnet](https://github.com/NVlabs/contact_graspnet)
