# 前沿研究与开源模型决策矩阵

访问日期：2026-07-25。范围：面向单张 Radeon、全部可审计开源组件的快递分拣方案做
定向检索。源码许可证不等于模型和数据许可证；任何检查点进入最终复现包前，都必须继续
审计上游模型、依赖和数据条款。

## 结论

实施顺序确定为：

1. 先采集修正单位、类别均衡的 RGB-D 数据，ACT 保持为受控基线；
2. 在完全相同的数据拆分上训练轻量 Diffusion Policy；
3. 对 ACT 和 Diffusion 都做 RGB 对 RGB-D 的同条件闭环消融；
4. 对 0.5B VLA-Adapter 做 ROCm 兼容性试验；
5. 只有 RGB-D 已证明有收益、二维深度编码成为限制时，才投入原生点云策略。

这样先优化评分最高的机器人能力和 AMD 证据，再增加模型规模。当前 96 个成功回合不足以
支撑“通用 VLA 泛化”结论。

## 方法矩阵

| 方法 | 开源材料 | 对本项目的价值 | Radeon 状态 | 决策 |
| --- | --- | --- | --- | --- |
| ACT | MIT 参考实现；Apache-2.0 LeRobot 实现 | 低数据动作分块基线，已完成集成 | 已完成 5,000 步训练和闭环推理 | P0；用修正数据、3 个种子重训 |
| Diffusion Policy | MIT 参考实现；LeRobot 实现 | 能表达多峰动作，但迭代去噪增加延迟 | 76.6M 轻量版已完成单步训练 | P0 对照；比较 5/10/20 步去噪 |
| 3D Diffusion Policy（DP3） | MIT 源码；RSS 2024 论文 | 点云可能比深度图更直接利用几何 | 本仓库无 ROCm 实测 | RGB-D 消融和算子审计后进入 P1 |
| Consistency Policy | 公开论文与实现生态 | 可蒸馏 Diffusion、降低推理延迟 | 未集成 | Diffusion 有效果但延迟不达标时做 P2 |
| VLA-Adapter 0.5B | MIT 仓库；公开 MIT 标注基座/检查点 | 语言条件、0.5B、覆盖 10-48 GB 训练配置 | 官方安装仍以 CUDA 为主，ROCm 未验证 | 首选 VLA 兼容性试验 |
| SmolVLA | Apache-2.0 LeRobot 源码；公开检查点 | LeRobot 原生且较小 | 入口已写，Radeon 主机拿不到权重 | 暂缓：检查点元数据未声明许可证 |
| OpenVLA / OFT | MIT 源码和公开权重 | 强 VLA 研究基线，OFT 提高动作吞吐 | 官方示例依赖 CUDA/FlashAttention，7B 对单指令过重 | 仅研究；权重继承 Llama 2 条款 |
| Octo | MIT 源码；80 万轨迹通用策略 | 可作开放通用策略参考 | JAX 增加 ROCm 适配风险 | 仅研究 |
| RDT-1B | MIT 源码和 MIT 标注权重 | 开放 1B diffusion 基础策略 | 双臂 embodiment 与当前接口不匹配 | 兼容性备选，不是第一 VLA |
| openpi（pi0/pi0.5） | Apache-2.0 源码和公开权重 | 前沿能力参考 | 官方 README 明确要求 NVIDIA，完整微调超过本卡 | 排除出比赛实现主线 |
| NVIDIA GR00T | Apache-2.0 源码；NVIDIA 模型许可证 | embodiment 覆盖广 | NVIDIA/CUDA 路线，模型条款与源码不同 | 排除出严格开源 Radeon 路线 |

表中的“开源”只描述已引用材料，不代表自动批准。VLA-Adapter 仍需递归审计 Qwen2.5、
DINOv2/SigLIP、安装 wheel 和每个权重文件。

## 六类能力优化方案

| 能力 | 下一实验 | 必须固定 | 验收证据 |
| --- | --- | --- | --- |
| 仿真 | 物理与相机分别 profile；滚动摩擦继续限定作用域 | catalog、种子、35 N | steps/s、渲染频率、任务回归 |
| 学习 | 300 个 catalog-v2 成功回合；ACT 与轻量 Diffusion 各 3 种子 | 数据拆分、动作接口、训练预算 | 留出集闭环均值和范围 |
| 鲁棒性 | 课程随机化、失败邻域补采、nominal/in-domain/unseen | episode 清单和安全边界 | 分类成功、掉落和恢复 |
| 闭环 | 接触感知速度整形，学习动作外加残差纠偏 | 状态机与力中止 | 首次成功/恢复提升且力不退化 |
| GPU 优化 | AMP/batch 扫描、同步计时、复制/渲染 profile，再尝试 compile | 模型、种子、数据 | samples/s、P95、峰值显存、成功率 |
| 多模态 | RGB 对 RGB+深度视图；之后才是点云 | 相同回合和检查点计划 | 未见类别收益及延迟代价 |

模型初选至少需要 30 个未参与选模的闭环回合；最终比较应使用不少于 60 个预先声明的
episode、按 profile 分层、3 个训练种子、固定 35 N 边界和文件哈希。

## 检索来源与复现

OpenAlex 使用 `GET https://api.openalex.org/works`，参数为 `search`、
`filter=from_publication_date:2022-01-01`、`sort=relevance_score:desc`、
`per_page=5/8`。检索主题包括 ACT、Diffusion、DP3、VLA、OpenVLA、RDT-1B、
VQ-BeT 和 Consistency Policy。GitHub 使用
`GET https://api.github.com/repos/{owner}/{repo}` 与 README contents API；模型元数据使用
`GET https://huggingface.co/api/models/{model_id}`。

主要论文：

- ACT：RSS 2023，DOI `10.15607/RSS.2023.XIX.016`。
- Diffusion Policy：RSS 2023，DOI `10.15607/RSS.2023.XIX.026`。
- DP3：RSS 2024，DOI `10.15607/RSS.2024.XX.067`，arXiv `2403.03954`。
- Consistency Policy：RSS 2024，DOI `10.15607/RSS.2024.XX.071`。
- Octo：RSS 2024，DOI `10.15607/RSS.2024.XX.090`。
- OpenVLA：arXiv `2406.09246`；OpenVLA-OFT：RSS 2025，DOI
  `10.15607/RSS.2025.XXI.017`。
- SmolVLA：arXiv `2506.01844`；RDT-1B：arXiv `2410.07864`。
- VLA-Adapter：arXiv `2509.09372`，AAAI 2026 DOI
  `10.1609/aaai.v40i22.38931`。

仓库和模型来源详见英文配对文档中的完整 URL 列表。注意：引用数和仓库活跃度会变化；
GitHub 的 license 字段不覆盖所有模型和依赖。任何方法只有在目标 Radeon 上实际运行并
留存日志后，才可以写成 ROCm 兼容。

## 本轮可复核检索快照

本轮重新执行了定向请求，没有把二手列表当作证据。arXiv export API 返回每个编号的论文
标题和发布日期；GitHub API 返回仓库 license 和默认分支。它们只能支持实验取舍，不能
证明任务性能，也不能代替传递依赖许可证审计。

| 对象 | 检索结果 | 工程影响 |
| --- | --- | --- |
| ACT，arXiv `2304.13705` | *Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware*，2023-04-23 | 保留动作分块低数据基线 |
| Diffusion Policy，arXiv `2303.04137` | *Diffusion Policy: Visuomotor Policy Learning via Action Diffusion*，2023-03-07 | 做匹配的随机动作对照 |
| DP3，arXiv `2403.03954` | *3D Diffusion Policy: Generalizable Visuomotor Policy Learning via Simple 3D Representations*，2024-03-06 | 深度视图消融为正后才投入点云 |
| Consistency Policy，arXiv `2405.07503` | *Consistency Policy: Accelerated Visuomotor Policies via Consistency Distillation*，2024-05-13 | 仅在 Diffusion 延迟不达标时尝试 |
| OpenVLA，arXiv `2406.09246` | *OpenVLA: An Open-Source Vision-Language-Action Model*，2024-06-13 | 研究参考；权重条款和 CUDA 栈需单独审计 |
| Octo，arXiv `2405.12213` | *Octo: An Open-Source Generalist Robot Policy*，2024-05-20 | 研究参考；JAX/ROCm 是额外风险 |
| RDT-1B，arXiv `2410.07864` | *RDT-1B: a Diffusion Foundation Model for Bimanual Manipulation*，2024-10-10 | 兼容性备选，不是单臂第一路线 |
| pi0，arXiv `2410.24164` | *$\\pi_0$: A Vision-Language-Action Flow Model for General Robot Control*，2024-10-31 | 前沿参考；官方 NVIDIA 约束排除出主线 |
| SmolVLA，arXiv `2506.01844` | *SmolVLA: A Vision-Language-Action Model for Affordable and Efficient Robotics*，2025-06-02 | 检查点许可证明确前暂缓 |
| RISE，IROS 2024 | *RISE: 3D Perception Makes Real-World Robot Imitation Simple and Effective* | 稀疏 3D 编码候选；当前许可证门禁未通过 |
| FlowPolicy，AAAI 2025 | *FlowPolicy: Enabling Fast and Robust 3D Flow-Based Policy via Consistency Flow Matching for Robot Manipulation* | RGB-D 先证明收益且延迟预算固定后才进入候选 |
| DROID，RSS 2024 | *DROID: A Large-Scale In-The-Wild Robot Manipulation Dataset* | 支持“数据多样性优先”，但不能直接复用到当前 embodiment |
| AXIS，arXiv `2607.21588` | *AXIS: A Growable Community-Driven Data Engine for Scalable Robot Manipulation* | 很新的数据引擎信号，不能作为当前任务证据 |
| 偏差感知采集，arXiv `2607.21582` | *Scale Up Strategically: Learning Compositional Generalization via Bias-Aware Evaluation and Data Collection for Robotic Manipulation* | 支持在冻结基线后按失败分层补采 |
| `huggingface/lerobot` | GitHub API：Apache-2.0，默认分支 `main` | 使用固定的 LeRobot 数据/策略接口 |
| `OpenHelix-Team/VLA-Adapter` | GitHub API：MIT，默认分支 `main` | 做独立 ROCm 与递归许可证试验 |
| `Physical-Intelligence/openpi` | GitHub API：Apache-2.0，默认分支 `main` | 作为参考；README 的 NVIDIA 要求不满足主线 |
| `Genesis-Embodied-AI/Genesis` | GitHub API：Apache-2.0，默认分支 `main` | 继续 Genesis 物理与渲染路线 |

复核命令如下，学习者可以直接重复：

```text
GET https://export.arxiv.org/api/query?id_list=2304.13705,2303.04137,2403.03954,2405.07503,2406.09246,2405.12213,2410.07864,2506.01844,2410.24164
GET https://api.github.com/repos/{owner}/{repo}
```

## 快递几何证据

目录把有实测来源的承运商产品与硬件可行训练分层分开。USPS 产品页提供了当前评测
profile 中的精确箱体尺寸；USPS Notice 123 提供了大圆筒压力范围使用的长度/周长规则。
FedEx 和 UPS 包装页只作为定性包装参考，不把没有来源的数字写成产品尺寸。没有原始尺寸
来源的 profile 不标记为“承运商标准”。

| 几何类别 | 代表来源或规则 | 目录处理 |
| --- | --- | --- |
| 小/中/大型长方体 | USPS Small、Medium、Board Game Flat Rate 产品页 | 精确尺寸只做评测；训练分层覆盖 `small_carton` 到 `large_narrow_carton` |
| 扁平邮袋/信封 | USPS flat-rate 包装系列 | 当前用刚性 flat-mailer proxy；可变形邮袋留到后续 |
| 直立圆柱 | Panda 夹爪开口内的消费品罐/筒几何 | 训练 profile 随机化半径和高度 |
| 横向圆柱 | USPS 非标准圆筒规则和邮筒尺寸 | `mailing_tube` 训练 profile 加 `large_mailing_tube` 边界 profile |
| 超大箱 | USPS board-game 箱和长度/周长规则 | 吸盘或 cradle 末端执行器接入前只做评测 |

来源：

- https://store.usps.com/store/product/priority-mail-flat-rate-small-box-P_SMALL_FRB
- https://store.usps.com/store/product/priority-mail-flat-rate-medium-box-1-P_O_FRB1
- https://store.usps.com/store/product/priority-mail-board-game-large-flat-rate-box-GB_FRB
- https://pe.usps.com/text/dmm300/Notice123.htm
- https://www.fedex.com/en-us/shipping/packaging.html
- https://www.ups.com/us/en/supplychain/resources/glossary-term/ups-packaging-guidelines.page

上面的 2026 年 arXiv 条目只作为前沿信号，不作为稳定基线。它们只用于改进数据采集实验，
不能绕过仓库许可证、ROCm 或固定留出评测门禁。

## 匹配模型选取协议

模型排名现在会拒绝 episode 集、随机样本 SHA-256 指纹或接触力阈值不一致的检查点比较，
同时输出 Wilson 95% 区间和逐 profile 成功率，再按以下顺序排序：

1. 安全违规率为零或最低；
2. profile 成功率宏平均，避免样本更多的盒类掩盖圆柱和大箱失败；
3. 总成功率、掉落率、P95 延迟和峰值接触力。

这只是评测能力改进，不是模型性能结论。新的结果必须等 Radeon 采集、训练和固定留出集闭环
全部完成后才能写入。
