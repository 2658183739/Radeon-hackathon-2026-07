# Competition Submission Materials / 比赛提交材料

This folder is the local, reproducible hand-off for the Parcel Sorter ROCm
project. It contains the bilingual description, the exact V20 mode-only
calibration/evaluation evidence, three raw MP4 episode recordings, and the
public-fork link record.

本目录是 Parcel Sorter ROCm 项目的本地可复核交付材料，包含中英双语项目说明、
V20 mode-only 校准与评测的原始证据、三段原始 MP4，以及公开 fork 链接记录。

## Result boundary / 结果边界

The strict V20 PI0.5 campaign completed all three episodes, but the audited
pure-VLA result is **0/3**, with zero force violations and zero expert
fallback/reference calls. Therefore this is an auditable **not-passed
competition candidate**, not a claimed MVP pass. The package deliberately
does not contain a forged `RESULTS.json` or a fake passing delivery manifest.

V20 PI0.5 严格评测完整运行了 3 个 episode，但审计后的纯 VLA 结果为 **0/3**；
force violation、expert fallback 和 expert reference 均为 0。因此本目录是可审查的
**未通过比赛候选包**，不是宣称通过的 MVP。目录不会伪造 `RESULTS.json` 或通过版清单。

## Reproduction / 复现

Use the exact command and fixed contract recorded in
`evidence/v20/exact-command.sh`. The contract keeps training seed `11`, runtime
seed `2026080206`, inference seeds `20260727/20260728/20260729`, the frozen
12-observation panel, and the registered thresholds unchanged.

使用 `evidence/v20/exact-command.sh` 中记录的精确命令和固定契约复现。训练 seed、
运行 seed、推理 seeds、冻结 12-observation panel 以及阈值均保持不变。

## Video / 视频

`videos/v20/` contains the three raw strict-evaluation recordings. The side
suction episode is 2.8 seconds and is suitable as a short local demo clip;
the two top-suction recordings are short fail-closed clips. The training
observation clips under `videos/training/` are included as visual context and
are explicitly labelled as training/demo footage, not pure-VLA success.

`videos/v20/` 包含严格评测的三段原始视频。side suction 片段时长 2.8 秒，可作为本地
短演示；两个 top suction 片段是 fail-closed 短片段。`videos/training/` 中的训练观测
视频只用于展示动态场景，已明确标注为训练/演示素材，不计为纯 VLA 成功。

External YouTube/Bilibili publication is not performed by this package. The
only valid public URL currently recorded is the verified GitHub fork in
`../submission_links.json`; video URL fields remain null until the account
owner publishes and opens the link successfully.

本包未代替账号发布 YouTube/Bilibili。当前只记录已验证的 GitHub fork；视频 URL 在账号
所有者真实发布并打开验证前保持为空。
