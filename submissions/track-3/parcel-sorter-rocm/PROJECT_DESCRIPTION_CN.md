# 项目说明

Parcel Sorter ROCm 在单张 AMD Radeon GPU 上通过 ROCm 运行 Genesis 包裹抓取与分拣仿真。Franka Panda 抓取随机包裹、跨工作区搬运，并放入指定左/右目标区。

三条执行路径严格分开。成功视频来自确定性控制器 `ScriptedPickPlaceExpert + ClosedLoopSupervisor`：它读取 Genesis 特权状态、执行有限状态监督，在 10 个开发回合中成功 8 个。它不是 GPT-5.6 Luna，也不是纯 VLA。

混合 VLA 路径中，SmolVLA 或 PI0.5 提出受限动作或残差，Harness-Lite 检查笛卡尔进度、接触力、IK 和工具指令边界。42 个离线动作包络结果只属于混合 VLA 的离线证据，不是闭环任务成功。严格纯 VLA 路径由学习策略负责全部声明任务动作，不允许专家完成或回退；结果为 0/3，未通过。

学习策略输入为俯视 RGB、语言与 43 维非特权状态；启用 primitive progress 后输出为 20 维动作。审计数据集包含 7 个独立 episode、4,557 帧；本地 SmolVLA checkpoint 训练 2,800 step。

**GPT-5.6 Luna 是研发/编排 Agent。** 它通过 Codex 运行时的 Responses 风格文件、终端、Git 和浏览器工具调用，辅助代码实现、实验编排、证据核验和交付审核。GPT-5.6 Luna 不接收机器人观测、不调用 `ActionPolicy.predict`、不向机器人发送动作，因此不是机器人推理或控制模型。

工程贡献是可审计边界：统一的 `ActionPolicy` API、可复现脚本控制器、版本化 Panda 工具适配器、受限的混合 VLA 动作选择，以及把每项结果绑定到控制器和 checkpoint 的证据台账。

记录的运行环境为 Genesis 1.2.3、ROCm 7.2.1、PyTorch 2.9.1 ROCm、LeRobot 0.6.1 和 Python 3.12。本次提交仅提供仿真结果；不主张 Sim-to-Real、真实机器人视频或成功的纯 VLA 闭环结果。
