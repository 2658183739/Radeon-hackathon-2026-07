# 自适应重试 v2 证据

本证据复用冻结 100 回合 primitive checkpoint campaign 中已经观察到的失败
`primitive-v2-dry-run-holdout-005`，没有扩大评测总体。

第一次 `pash_arm@nominal` 重现已登记的抬升失败。Harness 随后撤销学习型机械臂权限，选择
`pash_base@gentle_lift`：接近和垂直运动速度降为 0.75 倍，接触穿透增加 0.5 mm，抬升高度增加
15 mm。第二次完成抓取、运输、放置和释放，放置误差 1.44 cm，接触峰值 4.84 N，断吸为零。

成功尝试保存 673 帧 30 Hz 数据，包含 43 维状态、19 维动作、RGB、米制深度和任务文本；
`recovery-dataset-audit.json` 全部通过。35 MB 轨迹保留在 Radeon 工作区：
`/workspace/parcel-sorter-opt-v1/outputs/pash-recovery-known-failure-005-v2/attempt-02-pash_base/recovery-dataset`，
不提交到 Git。

这是一项配对机理验证，不是重试恢复率估计。所有报告必须分别写首试成功和最多三次最终成功。
