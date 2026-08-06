# Technical Blog and Social Copy / 技术博客与社交媒体文案

## Chinese Blog / 中文博客

### Loss 降了，机器人为什么还是抓不起来？

我们在 AMD Radeon + ROCm 上训练 Parcel Sorter 的 SmolVLA 时，最先遇到的不是训练跑不动，而是一个更麻烦的问题：loss 从 2.164 降到 0.056，机器人闭环却仍然无法完成一次完整抓放。

这迫使我们把“模型学到了什么”和“机器人真的完成了什么”拆开记录。

Parcel Sorter ROCm 在 Genesis 中使用 Franka Panda 完成随机包裹抓取、跨工作区搬运和目标区放置。我们保留了三条互不混淆的执行路径。第一条是 `ScriptedPickPlaceExpert + ClosedLoopSupervisor`，它读取仿真特权状态，用有限状态机完成接近、抓取、抬升、搬运和释放。10 个固定种子回合中有 8 个成功，演示视频中的八段轨迹都来自这里。

第二条是混合 Agent+VLA。SmolVLA 或 PI0.5 给出动作或残差，Harness-Lite 再检查笛卡尔位移、IK、接触力和工具命令。原始 VLA 动作在 42 个离线 episode-stage 样本上是 0/42 合法；加入固定安全裁剪和 Harness-Lite 后都是 42/42。这个结果说明安全监督层有用，但它只是离线动作包络，不是 42 次抓放成功。

第三条是严格纯 VLA：学习策略负责所有声明的任务动作，不允许专家补全。结果是 0/3。我们选择把失败留下，因为它比把三条路径合成一个漂亮成功率更有用。训练 loss、离线 MAE、动作合法性和闭环成功率回答的是四个不同问题。

本次训练使用单张 AMD Radeon GPU、ROCm 7.2.1、PyTorch 2.9.1 ROCm 和 LeRobot 0.6.1。一次完整运行训练 2,800 step，用时 442 秒，平均 6.33 step/s，日志峰值显存 2.32 GB。训练数据为 7 个独立仿真回合、4,557 帧，策略输入是俯视 RGB 和 43 维非特权状态，输出是含 primitive progress 的 20 维动作。

这次项目最重要的产出不是“VLA 已经成功”，而是一套不混淆证据的工作方式：成功视频绑定实际控制器，训练图绑定原始日志，数据集绑定 manifest 和哈希，纯 VLA 失败单独报告。下一步真正值得做的是增加多样化成功示范，再按冻结协议做独立随机回合的闭环比较；真机 Sim-to-Real 也必须等标定、同步视频和安全日志齐全后再报告。

项目地址：<https://github.com/2658183739/Radeon-hackathon-2026-07>

## English Blog

### The loss went down. Why did the robot still fail?

Our first obstacle while training SmolVLA for Parcel Sorter on AMD Radeon and ROCm was not getting training to run. It was the gap between optimization and control: the recorded loss fell from 2.164 to 0.056, yet the learned policy still did not complete a full pick-and-place task in closed loop.

That forced us to separate what the model learned from what the robot actually completed.

Parcel Sorter ROCm uses a Franka Panda in Genesis to pick a randomized parcel, move it across the workcell and place it in a target region. We keep three execution routes separate. The first, `ScriptedPickPlaceExpert + ClosedLoopSupervisor`, reads privileged simulator state and runs a finite-state sequence for approach, grasp, lift, transport and release. It completed 8 of 10 fixed-seed development episodes, and all eight clips in the demo come from this route.

The second route is hybrid Agent+VLA. SmolVLA or PI0.5 proposes an action or residual; Harness-Lite checks Cartesian motion, IK, contact force and tool commands. Raw VLA actions passed 0/42 frozen offline action-envelope samples. Fixed safety clipping and Harness-Lite both passed 42/42. This supports the supervisor design, but it does not mean 42 completed robot tasks.

The third route is strict pure VLA. The learned policy owns every declared task action and receives no expert completion. It scored 0/3. We kept that failure because combining the three routes into one attractive success rate would hide the engineering problem. Training loss, offline MAE, action validity and closed-loop task success answer different questions.

The recorded run used one AMD Radeon GPU, ROCm 7.2.1, PyTorch 2.9.1 ROCm and LeRobot 0.6.1. It trained for 2,800 updates in 442 seconds at 6.33 steps/s, with 2.32 GB reported peak memory. The audited simulation dataset contains seven independent episodes and 4,557 frames. Policy inputs are overhead RGB and a 43-D non-privileged state; outputs use a 20-D action contract with primitive progress.

The main outcome is not a claim that VLA is solved. It is an evidence discipline: each success video names its controller, each training figure traces back to a log, each dataset claim traces back to a manifest and hashes, and pure-VLA failure remains visible. The next step is more diverse successful demonstrations followed by a frozen, independent closed-loop comparison. Sim-to-Real should only be reported after calibration, synchronized video and safety logs exist.

Repository: <https://github.com/2658183739/Radeon-hackathon-2026-07>

## Social Post / 社交媒体短文案

**中文：**

我们在单张 AMD Radeon + ROCm 上完成了 Parcel Sorter ROCm：Genesis 中的 Franka Panda 包裹抓放、2,800-step SmolVLA 训练、可审计数据与三条严格分开的控制路径。脚本 Agent 为 8/10；混合 Agent+VLA 目前只有离线动作包络 42/42；严格纯 VLA 为 0/3。我们保留失败，也让每段视频和每个指标都能追溯到真实控制器。项目：<https://github.com/2658183739/Radeon-hackathon-2026-07>

**English:**

Parcel Sorter ROCm runs Genesis pick-and-place on one AMD Radeon GPU with ROCm, including a 2,800-update SmolVLA run and controller-attributed evidence. Scripted Agent: 8/10. Hybrid Agent+VLA: 42/42 offline action-envelope checks only. Strict pure VLA: 0/3. Every clip and metric stays tied to the controller that produced it. <https://github.com/2658183739/Radeon-hackathon-2026-07>
