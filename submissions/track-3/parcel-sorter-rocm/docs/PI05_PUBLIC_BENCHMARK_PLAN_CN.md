# π0.5 VLA 公开数据集与基准实验计划

更新日期：2026-07-28

## 使用边界

公开数据集实验只在快递抓取的冻结 105 回合达到至少 95/105、全部回合由 π0.5 路由和执行、专家回退为零且安全违规不增加之后启动。在此之前，主要资源继续用于修复真实 VLA 闭环。公开数据集的离线动作误差不能替代机器人成功率；没有交互环境的数据集只报告离线泛化指标，不写成“任务成功”。

## 数据集选择

Open X-Embodiment 是跨本体迁移的首选上游数据来源。其公开论文汇集 22 种机器人、21 个机构的数据并覆盖 527 种技能，展示了跨机器人正迁移。它适合验证本文的 LoRA、模式无关语言和验证式回放是否能迁移到不同本体，但完整训练成本很高，因此先使用与抓取、搬运、放置相关的标准化子集，不把全量下载作为第一步。

DROID 是真实场景泛化的首选离线数据集。论文报告 76,000 条示范、350 小时交互、564 个场景、84 个任务和 50 名采集者，能够检验视觉表示是否依赖单一仿真背景。DROID 本身不是可直接复现每条轨迹成功率的交互模拟器，因此计划报告 held-out scene 的动作预测误差、末端位姿误差、语言到动作检索和少样本适配效率，并明确这些指标不是闭环成功率。

BridgeData V2 是样本效率消融的首选数据集。论文报告 60,096 条轨迹、24 个环境和公开低成本机器人平台，并包含自然语言与目标图像条件。实验按完整 episode 而不是帧划分训练、验证和测试集，使用 1%、5%、10% 和 100% 数据比例比较固定 π0.5 base、普通 LoRA、阶段平衡回放 LoRA 和模式/动作加权版本。重复采样帧只作为训练权重，不增加独立样本数。

LIBERO 和 CALVIN 用于补充可交互的语言条件长程操作结果。LIBERO 适合知识迁移和持续学习消融；CALVIN 适合多步语言条件任务。两者的动作空间、相机和机器人本体与本项目不同，因此使用独立输出头并保持同一视觉语言主干。结果报告官方 success、长程链长度和三随机种子均值及置信区间，不把公共基准 adapter 与快递机器人 adapter 混为同一个模型。

## 预注册比较

公开实验的最小比较为固定 π0.5 base、普通 rank-16 LoRA、无模式语言泄漏 LoRA、failure-localized stage-balanced verified replay，以及加入验证式失败恢复回放的完整方法。每个训练比例使用三个固定随机种子。数据划分以 episode、场景或任务为独立单位，禁止把同一 episode 的帧分到训练和测试两侧。超参数只在验证集选择，公共测试集在最终配置冻结后运行一次。

主要离线指标包括归一化动作 MSE、末端接触点欧氏误差、离散模式宏平均准确率、每类召回率、负对数似然或校准误差，以及达到给定误差所需的成功示范数。交互基准报告成功率、Wilson 95% 区间、平均连续任务长度、专家回退率和安全拒绝率。配对任务使用 exact McNemar 检验；多随机种子结果同时报告均值、标准差和原始种子值。

## 与论文贡献的关系

内部快递基准证明方法能否在有吸盘密封、双臂承重和接触力约束的真实闭环中工作。BridgeData V2 检验样本效率，DROID 检验场景泛化，Open X-Embodiment 检验跨本体迁移，LIBERO/CALVIN 检验公开交互任务上的可复现性。四类证据回答不同问题，不能用某一个离线数据集的低误差替代 95/105 的真实抓取目标。

## 检索证据与复现信息

文献检索日期为 2026-07-28。π0.5 原论文通过 arXiv API `id_list=2504.16054` 核验；DROID、BridgeData V2 和 Open X-Embodiment 分别通过 `id_list=2403.12945`、`2308.12952` 和 `2310.08864` 核验。OpenAlex 使用 `/works` 搜索题名，并返回 Open X-Embodiment 的 ICRA 2024 DOI `10.1109/ICRA57147.2024.10611477`、DROID 的 RSS 2024 DOI `10.15607/rss.2024.xx.120`、LIBERO 的 arXiv DOI `10.48550/arXiv.2306.03310` 和 CALVIN 的 arXiv DOI `10.48550/arXiv.2112.03227`。检索只用于确定公开基准和可复核引用；正式稿仍需逐篇核对最终出版版本、作者顺序和 BibTeX。

## 核心参考文献

Physical Intelligence et al. “π0.5: a Vision-Language-Action Model with Open-World Generalization.” arXiv:2504.16054, 2025.

Open X-Embodiment Collaboration et al. “Open X-Embodiment: Robotic Learning Datasets and RT-X Models.” ICRA, 2024. DOI: 10.1109/ICRA57147.2024.10611477.

Khazatsky et al. “DROID: A Large-Scale In-The-Wild Robot Manipulation Dataset.” RSS, 2024. DOI: 10.15607/rss.2024.xx.120.

Walke et al. “BridgeData V2: A Dataset for Robot Learning at Scale.” arXiv:2308.12952, 2023.

Liu et al. “LIBERO: Benchmarking Knowledge Transfer for Lifelong Robot Learning.” arXiv:2306.03310, 2023.

Mees et al. “CALVIN: A Benchmark for Language-Conditioned Policy Learning for Long-Horizon Robot Manipulation Tasks.” arXiv:2112.03227, 2021.
