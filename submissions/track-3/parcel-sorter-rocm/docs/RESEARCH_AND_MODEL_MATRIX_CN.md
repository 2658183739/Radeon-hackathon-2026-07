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
