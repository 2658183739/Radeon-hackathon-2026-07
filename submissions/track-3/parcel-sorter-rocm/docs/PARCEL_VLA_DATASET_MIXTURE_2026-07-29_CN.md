# 快递 VLA 成功数据集规模与混合协议

日期：2026-07-29。本文只规定数据采集、验收、切分和训练采样；失败轨迹不作为行为克隆正标签。

## 1. 论文证据

| 工作 | 通用预训练规模 | 下游/实体微调规模 | 与本项目直接相关的做法 |
|---|---:|---:|---|
| OpenVLA, arXiv:2406.09246v3 | 97 万条机器人轨迹 | 每个目标任务 10--150 条示范 | 目标域微调只用机器人数据；清理全零动作；DROID 曾以 10% 权重加入，但因学习慢在最后三分之一移除 |
| OpenVLA-OFT, arXiv:2502.19645v2 | 继承 OpenVLA | LIBERO 每套 500 条/10 任务，即 50 条/任务；实体任务分别为 20、30、45、300 条 | 过滤失败示范；连续动作、action chunk、腕部图像和 proprio 对高成功率很重要 |
| Octo, arXiv:2405.12213v2 | 80 万条轨迹、25 个数据集 | 每个新域约 100 条轨迹 | 多样数据集加权 2 倍，重复数据降权；每条长轨迹最多随机取 100 步，避免长回合支配训练 |
| SmolVLA, arXiv:2506.01844v1 | 481 个社区数据集、2.29 万回合、1060 万帧 | 实体任务每个数据集 50 条，5 个起点各 10 条 | 起点分层，任务内多样性优先；LIBERO/MetaWorld 也采用每任务约 50 条 |
| pi0.5, arXiv:2504.16054v1 | 第一阶段 97.6% 样本来自非移动操作、其他机器人或网页；移动操作约 400 小时 | 第二阶段聚焦移动操作 | 后训练动作数据只保留成功且低于固定长度阈值的回合；异构数据用于预训练，不等于可直接拼接动作空间 |

结论不是照搬某一篇的绝对数量。常见目标域微调集中在每任务约 50--100 条，复杂实体任务上限可到 300 条；通用预训练则从 2.29 万到 97 万条。快递任务包含三种不同接触模式、24 个设计单元和长时双臂搬运，因此采用 1500 条独立成功回合，处在“小型目标微调”和“通用预训练”之间，并给每个训练设计单元 50 条成功回合。

## 2. 冻结目标

- 完整验收成功：1500 条，不是 1500 次尝试。
- `top_suction`、`side_suction`、`cooperative_cradle` 各 500 条。
- 每种模式 8 个设计单元，共 24 个单元；每单元验收 62 或 63 条，总和严格为 1500。
- 按独立物理回合切分为 1200 train、150 development、150 untouched confirmation。
- 相邻帧、重复渲染、动作 chunk 和增强图像都不增加独立回合数。

批量计划预生成每模式 960 次候选，即每个设计单元 120 次、共 2880 次储备尝试。计划测试要求 2880 个候选的物理参数签名全部唯一，不能只靠不同 episode ID 冒充独立数据。该储备是为了在先导成功率刚好 70% 时仍能高概率收满全部 24 个单元；采集器按设计单元收满 62/63 条成功配额后立即跳过该单元的剩余候选，因此不会把储备数误当成数据集规模，也不会多收成功轨迹。若仍有单元不足，再只补缺失单元，不复制已有轨迹。

## 3. 先导门与成功包络

先运行 30 次先导：三种模式交错，每种最多 10 次。只有每种模式都达到至少 7/10，才允许启动批量采集；如果某模式即使后续全成功也已不可能达到 7/10，立即按 `yield_gate_failed` 停止，不再消耗剩余候选。否则在每种模式达到 10 次后，任一模式低于 70% 时自动停止。

参数范围来自已完成成功证据。v2 先导在数学上已不可能过门时提前结束，共完成 14 次、保存 7 条成功数据：side suction 为 5/5，top suction 为 1/5，cooperative cradle 为 1/4。失败分析表明 v2 虽然每个字段都落在历史边界内，却把尺寸、质量、摩擦、姿态和起点独立重组，破坏了历史成功样本中的联合相关性。v3 改为相邻成功锚点的联合路径插值，完成 10 次后因 top suction 已不可达而停止：side suction 3/3、cooperative cradle 3/3、top suction 0/4。由此可见 cradle 路径有效，但 top 的接触动力学并非凸集，两个成功端点的中间点仍可能失败。v4 保持 side 和 cradle 完全不变，只把 top 改为从真实成功锚点出发的单因素小扰动。

v4 暴露了此前漏检的合同漂移：top 的 15 条“5/5 成功锚点”来自 7 月 27 日旧评测代码，原摘要全部为 `frames=0`，没有经过当前非空 wrist RGB-D 数据落盘门；当前评测器又新增了物理杯位与准静态接触逻辑，旧成功不能直接当作当前协议成功。v4 的前三条 top 均完成抓取和运输，但放置循环只允许 cooperative cradle 在进入投放容差后提前停止，top 继续下压并出现 42--68 N 接触峰值。v5 不改候选参数，只把 24 帧稳定投放门应用到所有抓取模式，并在任一接触通道达到 35 N 时立即停止继续下压。

v5b 在补齐远端缺失的 `mobile_vla_service.py` 后完成了 4 条 top 单因素探针。结果不是零进展：`micro_box` 完成完整抓取、抬升、运输、投放和释放，保存 594 帧非空 RGB-D，投放误差 0.0134 m，峰值接触力 19.52 N；另外三条为当前协议真实失败，峰值 36.79--39.12 N。随后两个更大 `micro_box` 锚点分别达到 40.20 N 和 102.72 N；将 flat-mailer 接触压入从 0.50 mm 降到 0.25 mm 后仍为 39.33 N，否证了“仅由压入量造成”的假设。v6 因此删除所有没有通过当前合同的 top 锚点，只保留 v5b 的完整成功点；cradle 也删除 lift contact ratio 为 0.4917 的边界失败点，只保留当前协议下比 0.50 门槛有明确余量的两条成功点。

- top suction：唯一锚点为 v5b 当前协议成功的 `micro_box`：尺寸 `(0.0637339768, 0.0375, 0.0285) m`、质量 `0.08 kg`、摩擦 `0.355`、零起点偏移和零 yaw。每条候选只扰动 `size_x/size_y/size_z/mass/friction/offset_x/offset_y/yaw` 中的一个因素，尺寸幅度 0.2%、质量/摩擦 0.5%、起点 0.25 mm、yaw 0.0025 rad；其余字段保持成功锚点原值。普通示范不得注入 recovery 接触偏移。该范围必须先通过 8 个设计单元探针和完整 10 条先导，不能由单条成功直接外推到 500 条。
- side suction：以 `pi05-side-recovery-v2` 的 8/8 成功范围为中心，只保留已验证的 5.5--6.5 mm 接触偏移、0.25--0.75 mm 压入和 0.60 垂向速度比例。
- cooperative cradle：只在 v4 当前协议成功的 `cooperative_cradle-0000/0001` 两点间，对箱体参数、起点、接触偏移和双臂抬升偏移做联合路径插值。两点的 lift contact ratio 约为 0.5375 和 0.5625，峰值 cradle force 约为 27.99 N 和 31.58 N；失败点 0.4917 不得进入成功包络。

完整成功要求抓取、保持、搬运、正确投放、释放、35 N 力门和传感器完整性全部通过。失败尝试只进入 failure telemetry。

## 4. 训练混合比例

第一版候选采用最常见的“通用 checkpoint 初始化 + 目标域成功示范微调”方式：

- 行为克隆数据源：100% 验证成功的快递目标域回合。
- 三种抓取模式采样概率：各 1/3。
- 模式内部：8 个设计单元等概率。v6 的 top suction 仅覆盖当前已验证的轻小包裹域；upright canister 与 large rectangular carton 分别由 side suction 和 cooperative cradle 覆盖。不得为了表面多样性把未通过 35 N 门的 flat-mailer 或 small-carton 当作正样本。
- 长轨迹：先选模式、设计单元、回合和阶段，再在阶段内采样；每个回合每阶段最多 100 帧，避免 600 帧长回合压过短接触阶段。
- failed episode：0%；未验证 corrective candidate：0%；纯 VLA 成功回放：当前为 0%，以后只能在独立 replay 成功后加入。

不默认混入 DROID/BridgeData/Open X 原始动作。它们的机器人本体、动作维度、坐标系和归一化与当前 23-D 绝对动作合同不同；PI0.5 DROID checkpoint 已承担通用初始化。只有完成独立 action adapter 后，才做一个固定预算消融：前 2/3 训练为 90% 快递 + 10% adapted DROID，最后 1/3 回到 100% 快递。这一消融对应 OpenVLA 的保守 10% DROID 经验，不作为默认高分配方。

## 5. 可执行切分门

收满数据后必须运行 `scripts/build_mobile_pi05_success_split.py`，并同时提供最终 `collection-summary.json` 与合并后 LeRobot `meta/info.json`。切分器不是按帧随机切分，而是按独立回合、抓取模式和设计单元分层；它精确生成每模式 400 train、50 development、50 confirmation，即总计 1200/150/150。任一回合缺少非空数据、完整抬升/运输/投放/释放证据、达到 35 N、来源身份重复、配额不完整或合并数据集不是 1500 回合时，切分失败并且不得训练。

confirmation 索引在模型、训练配方和 AMD 运行时配置冻结前不得读取。训练采样器按模式各 1/3，再在模式内按 8 个设计单元各 1/8 采样，避免 62/63 条的轻微数量差异改变梯度比例。

存储格式固定为 LeRobot v3 视频后端：两路 RGB、两路 12-bit metric depth 和两路三通道 depth view 均按视频保存，训练和审计固定使用 `dataset.video_backend=pyav` 与 `dataset.depth_output_unit=m`。单条 594 帧实测由约 161 MB 降至 7.8 MB；PyAV 随机解码三处关键帧通过，depth view 相对重新计算值的平均误差为 0.21--0.26/255，99% 像素误差不超过 2。不得使用当前 ROCm 环境中无法加载的 TorchCodec 默认后端。

collection v7 仅冻结上述视频存储和审计合同，物理参数继续使用已经通过探针的 v6 成功包络。v6 三模式先导用于物理成功率证据；v7 先导必须再次证明直接视频写入、合并、PyAV 解码与相同完整任务成功率，随后 bulk 只允许使用 v7 计划和匹配的 collector 哈希。

### 5.1 训练前的三个冻结产物

收满并合并 1500 条成功回合后，训练不能直接读取全量帧，也不能直接使用全量 `meta/stats.json`。必须依次生成并冻结：

1. `PARCEL_SUCCESS_SPLIT.json`：按独立回合、模式和设计单元生成 1200/150/150 切分。
2. `PARCEL_PI05_SAMPLING_MANIFEST.json`：只索引 1200 条 train 回合，24 个设计单元每轮严格等量，每回合每阶段最多 100 个唯一帧。
3. `meta/train_stats.json` 与 `PARCEL_TRAIN_STATS_MANIFEST.json`：只使用上述等权 train 帧计算 state/action 归一化统计，development 和 confirmation 帧数必须为 0。

训练入口会同时检查 sampling manifest 的内容哈希和文件哈希、train-stats manifest、LeRobot 顶层 `EpisodeAwareSampler` 的实际类绑定，以及训练合同中的有效每轮样本数。任一缺失时 fail closed，避免出现“文档写 1/3，实际仍按原始帧数采样”或 confirmation 通过全量统计泄漏的问题。

```bash
python scripts/build_mobile_pi05_success_split.py \
  --collection-summary RUN/collection-summary.json \
  --dataset-info RUN/lerobot_dataset/meta/info.json \
  --output RUN/lerobot_dataset/PARCEL_SUCCESS_SPLIT.json

python scripts/build_mobile_pi05_sampling_manifest.py \
  --dataset-root RUN/lerobot_dataset \
  --split-manifest RUN/lerobot_dataset/PARCEL_SUCCESS_SPLIT.json \
  --output RUN/lerobot_dataset/PARCEL_PI05_SAMPLING_MANIFEST.json

python scripts/build_mobile_pi05_train_stats.py \
  --dataset-root RUN/lerobot_dataset \
  --split-manifest RUN/lerobot_dataset/PARCEL_SUCCESS_SPLIT.json \
  --sampling-manifest RUN/lerobot_dataset/PARCEL_PI05_SAMPLING_MANIFEST.json \
  --output-stats RUN/lerobot_dataset/meta/train_stats.json \
  --output-manifest RUN/lerobot_dataset/PARCEL_TRAIN_STATS_MANIFEST.json
```

## 6. 复现来源

文献元数据于 2026-07-29 通过 arXiv API 一次定向查询：

`https://export.arxiv.org/api/query?id_list=2406.09246,2502.19645,2405.12213,2504.16054,2506.01844&max_results=5`

正文读取固定版本：`2406.09246v3`、`2502.19645v2`、`2405.12213v2`、`2504.16054v1`、`2506.01844v1`。原始 LaTeX 源文件保存在 `/workspace/persistence/parcel-sorter-opt-v1/literature/vla-data-mixture-20260729`。本地先导计划固定 seed `20260729`，计划文件、采集器和失败分类器均在运行摘要中记录 SHA-256。
