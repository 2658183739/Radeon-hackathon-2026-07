# PASH-VLA: Payload-Aware Safety-Harness VLA

## Method

PASH-VLA is a system-level method built on SmolVLA rather than a claim of a newly trained
foundation model. It targets one AMD Radeon, a mobile bimanual robot, and parcel handling by
combining a low-rate vision-language policy, short contact-force memory, a deterministic expert,
and an auditable near-line improvement loop.

```text
RGB + 43-D state + task text
        -> SmolVLA (3 Hz, 19-D proposal)
        -> force-memory temporal gate
        -> Harness-Lite residual candidates
        -> progress / deadline / contact / IK safety gates
        -> 240 Hz expert + tri-suction/V-cradle execution
        -> failure replay -> bridge curriculum -> Radeon retraining
        -> frozen holdout + Wilson promotion gate
```

The model contributes only residuals inside the safety contract. It cannot send torques or bypass
suction, cradle, placement confirmation, or the 35 N abort rule.

## Three attributable contributions

### 1. Payload-aware cooperative end effectors

Three physical compliant cups on the left arm create the seal; a physical V-cradle on the right
arm provides continuous support. Two sealed cups and 24 consecutive cradle-contact physics steps
are required before lift. Independent incremental IK is used for both arms during lift and place.

### 2. Force-Memory Harness VLA

Each VLA call retains the last six contact-force samples. If the peak exceeds 20 N or the window
rises by more than 8 N, the allowable VLA residual is tightened; stable low load leaves the policy
unchanged. A 2 N rise deadband avoids reacting to simulation noise, and the 35 N hard abort remains
unchanged. The implementation is `force_memory_scale_cap()` and is explicitly enabled with
`--force-memory-harness`; it is off by default to protect the frozen SmolVLA v2 baseline.

### 3. Failure-driven near-line self-improvement

Failed trajectories are ranked by failure stage, payload boundary, and safety events to produce a
bridge curriculum. Collection, training, offline Harness-envelope checks, frozen evaluation, and
checkpoint promotion are separate gates. Promotion requires success, Wilson non-inferiority, zero
force violations, actual VLA actuation, and single-Radeon/ROCm provenance. Active episodes never
mutate model weights, making the process replayable, reversible, and reviewable.

## AMD/ROCm path

Genesis physics, headless RGB-D, SmolVLA AMP training, HIP inference, and frozen evaluation run on
one Radeon. The Force-Memory Harness is a lightweight deterministic Python gate and introduces no
CUDA-only operator. SmolVLA inference still uses ROCm PyTorch; the optimization targets safe
end-to-end response and GPU budget instead of hiding contact failures with a larger model.

## Evidence boundary

- SmolVLA v2 frozen holdout: 96/100 with zero 35 N violations.
- tri-suction/V-cradle v24: one successful 1.44 m carton case, 2.16 cm error, zero suction breaks,
  and 30.65 N peak cradle force; mechanism evidence only.
- Force-Memory PASH-VLA has pure-function and Harness unit coverage plus one Radeon development
  regression: 11 of 68 inference calls tightened the residual, two fully fell back, and zero
  emergency stops occurred. The same extra-long carton succeeded with 2.11 cm error, zero suction
  breaks, and 30.64 N peak cradle force. It remains unpromoted because this is not a statistical
  `off/on` paired evaluation.
- The failure-bridge v3 scored 91/100 and was rejected by the Wilson gate, proving the gate can
  block regressions rather than proving that every self-improvement cycle helps.

## Ablation matrix

| Group | Comparators | Metrics |
| --- | --- | --- |
| Harness | raw VLA / numeric clipping / Harness-Lite / PASH-VLA | action MAE, selected scale, fallback, force abort |
| Force memory | no history / six-sample history / soft-gate variants | success, peak force, first-contact impulse, P95 latency |
| Self-improvement | no replay / replay without promotion / isolated promotion | frozen success, Wilson interval, regressions |
| End effector | suction only / dual arm without cradle / tri-suction + cradle | lift, suction breaks, load sharing, placement error |
| Modality | RGB / RGB-D | MAE, VRAM, P50/P95, profile-stratified success |

A single v24 case cannot support an 80% generalization or SCI claim. A publishable claim needs
new frozen size/mass/friction/offset combinations, multiple seeds, confidence intervals, and paired
comparisons for every causal ablation.
