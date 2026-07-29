# VLA 文献核查与后续实验决策（2026-07-29）

## 当前可声明结果

- 公共基准采用最常用的 LIBERO 四套件 400-unit 协议。冻结 confirmation 中，8-step candidate 为 `386/400 = 96.50%`，本地 10-step PI0.5 control 为 `385/400 = 96.25%`。
- 配对差值仅 `+0.25 pp`，Newcombe 95% CI 为 `[-2.24, 2.76] pp`，单侧 exact McNemar `p=0.5`。只能声明数值略高于本地 control，不能声明统计优越。
- 该结果低于未配对的 OpenPI 公开 `96.85%`，也没有同 checkpoint、同 adapter、同任务和同 seed 的 PI0.6 comparator，因此禁止声称超过公开 PI0.5 或 PI0.6。
- 快递任务尚无通过动作保真门和严格纯 VLA 闭环门的 candidate，当前不能给出快递成功率。

## 文献给出的直接启示

完整检索记录见 `allinone.md`。OpenVLA、Octo、DROID、RT-2、Open X-Embodiment 与 PI0/PI0.5 构成通用 VLA/数据基础；近期最相关的增量集中在：

1. 接触或触觉融合，用于最后几厘米的抓取、保持与释放；
2. action chunk、并行解码和异步控制，用于降低慢 VLA 的闭环延迟；
3. 物理可行性、路径偏差或成功预测，用于拒绝不可靠动作；
4. 环境反馈、自纠正和 world-model 迭代，用于从失败中改进；
5. 小模型、蒸馏和高效 flow policy，用于部署侧加速。

这些方向是相关工作，不自动构成本项目创新。尤其是单独采用 stage weighting、缩短 action chunk 或增加 wrist camera，都已有相邻工作，必须通过严格单因素消融和纯 VLA 完整任务成功证明价值。

## 面向本项目的可辩护贡献组合

优先组合为“阶段归因的动作学习 + 验证式纯 VLA 改进 + Radeon 成功约束优化”。其中每一层都必须先单独成立：

### C1：阶段归一化的绝对动作 flow loss

B3-SW 只改变连续 flow loss 的阶段权重，保持 base、数据、seed、LoRA、mode head、state token、动作合同和 12k 预算不变。它能成为方法贡献的最低条件是：

- 相对 B2 在冻结配对动作保真单元上通过预注册门；
- 严格 `3/3` 纯 VLA 快递 smoke 成功；
- 冻结 development 上的完整成功和接触阶段指标均改善；
- 失败不能仅从一个最优 seed 中删除。

若 B3-SW 只改善离线误差而闭环不改善，则它只能作为负结果或训练诊断，不能作为论文主贡献。

### C2：验证式接触恢复，而非伪“自主进化”

仅在 B3-SW 失败分类表明抓取、保持或释放是主要瓶颈时启用 B4。保持三个不可变池：纯 VLA 成功、失败遥测、待验证纠正。专家或搜索生成的纠正必须独立 replay 成功后才能进入行为克隆；失败动作本身不得伪装成正标签。

更有研究价值的 B4 单因素是“未来接触保持/密封结果辅助目标或 advantage-filtered verified replay”，而不是直接混入大量专家轨迹。辅助标签必须来自部署时可观察的力、密封和后续保持结果，不能读取 privileged object pose。论文名称应使用 verified replay、gated self-improvement 或 DAgger，除非模型自己生成并验证纠正。

### C3：阶段条件的执行窗口与 AMD 运行时

在同一个成功 checkpoint 上，比较固定执行窗口与阶段条件执行窗口：自由空间/运输允许较长 prefix，接触/放置使用短 prefix。调度器只能改变何时重新查询同一 VLA，不能生成目标、替换动作或调用专家；它是 runtime treatment，不得冒充策略能力。

Radeon 比较必须使用配对 ABBA 或等价抗热漂移设计，并同时报告：冷启动、暖态 P50/P95/P99、端到端 observation-to-actuation P95、allocated/reserved 显存、能耗、每个纯 VLA 成功的能耗、junction 温度、采样错误和成功率。只要成功、能耗或稳定性任一强制门回退，即拒绝该优化，即使吞吐更高。

## 冻结执行顺序

1. 完成 B3-SW `3k/6k/9k/12k` checkpoint，不重启或改写当前 `v3`。
2. 对四个 checkpoint 运行相同六观察动作保真 screen，按预注册规则选最早通过者。
3. 只有通过离线门的单个 checkpoint 才运行严格纯 VLA `3/3` smoke。
4. smoke 通过后进入冻结 parcel development；按对象、姿态、质量、接触模式、目标位置和扰动分层诊断。
5. development 配置冻结且达到工程门后，仅打开一次 parcel confirmation；禁止用 confirmation 继续选模型。
6. 只有 parcel 成功不回退后才开展 eager/优化 runtime 配对与 endurance。
7. 若 B3-SW 失败，只依据 development 的首个因果故障选择 B4 或 R14 单因素，不并行混合架构、数据、传感器和 runtime 改动。

## 评测集选择

- **公共主基准：LIBERO。** 已完成一次性 400-unit confirmation，不重跑。它适合与公开 VLA 文献对齐，但不能代替快递搬运结果。
- **任务主基准：冻结 parcel 105-rollout confirmation。** 主终点是完整纯 VLA 成功，必须包含抓取、保持、运输、正确投放、释放和安全门；最低工程门为 `95/105`，论文中若声称总体成功率超过 90%，需至少 `100/105` 并通过预注册单侧精确二项检验。
- **可选外部泛化：SimplerEnv 或 RoboCasa/VLABench。** 只有现有 LIBERO、parcel 与 Radeon 结果已经形成核心贡献后再考虑；新基准必须先冻结 adapter、任务和 seed，不能为排行榜反复试探。
- **DROID、BridgeData V2 与 Open X-Embodiment。** 它们主要是训练/迁移数据资源，不应把数据集训练 loss 写成 benchmark success。当前 PI0.5 DROID checkpoint 保持为固定初始化。

## 论文启动门

开始写 ICLR 正文前至少需要：

- LIBERO 证据边界保持诚实且可复现；
- 一个通过严格纯 VLA 归因的 parcel candidate，并在冻结任务上有足够成功率；
- 至少一个因果清晰的 matched ablation，不能只有最终模型；
- Radeon eager 与优化运行时的配对成功/时延/能耗证据；
- 所有最终 checkpoint、processor、合同、数据 manifest、代码 revision 和原始结果都有 SHA-256。

若这些门没有同时成立，先继续工程和实验，不开始填充论文结果表。
