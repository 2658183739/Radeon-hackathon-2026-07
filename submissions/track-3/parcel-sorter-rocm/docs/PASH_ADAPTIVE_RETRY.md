# PASH Adaptive Retry and Skill Acquisition

## Purpose

This extension fills the gap between within-rollout Harness decisions and
between-campaign weight retraining. It implements a **PASH Episodic Adaptation
Loop** that can make up to three separately audited attempts, identify the first
failed primitive, change control authority safely, and remember which strategy
worked for related parcel contexts.

The design absorbs two ideas from the references supplied during development.
Harness VLA separates learned contact primitives from deterministic motion and
uses task-specific and global memory for scheduling. InSight segments complete
tasks into primitives, identifies a primitive gap, acquires only that missing
skill, and writes audited success data back into a unified VLA. This repository
implements those ideas independently for one Radeon, SmolVLA, dual Panda arms,
tri-suction, and parcel handling.

Development references are the Harness VLA [project](https://harnessvla.github.io/),
[RPent repository](https://github.com/RLinf/RPent), and
[arXiv:2607.08448](https://arxiv.org/abs/2607.08448), plus the supplied summary
of *InSight: Self-Guided Skill Acquisition via Steerable VLAs*. The final paper
must cite the original InSight publication metadata rather than the secondary
article used for discovery.

## Three adaptation timescales

1. **Within a rollout:** the 3 Hz Force-Memory Harness selects a safe residual
   scale and falls back to the 240 Hz expert when required.
2. **Between attempts:** up to three scene attempts use the failed primitive,
   task memory, and global memory to select control authority.
3. **Between data cycles:** successful recoveries become primitive-acquisition
   candidates. Only audited sensor/action data enter Radeon retraining, and a
   frozen 100-trial Wilson gate controls checkpoint promotion.

Weights never change during an active rollout. Online adaptation means
primitive scheduling and authority selection; weight improvement remains a
near-line, reversible process.

## Strategies and safety rules

| Strategy | Learned authority | Force Memory | Role |
| --- | --- | --- | --- |
| `pash_arm` | base plus bounded left-arm transport residual | on | default high-capability attempt |
| `pash_base` | base residual only; expert arms | on | safe recovery after contact or precision failure |
| `expert_recovery` | shadow VLA; expert execution | off | conservative recovery after force risk or exhausted learned strategies |

A 35 N event permits only expert recovery on the next attempt. Suction, lift,
placement, or release failures remove learned arm authority. Cooperative-cradle
runs also exclude arm residuals because full dual-arm residual control has not
passed its gate.

## Task and global memory

The memory stores both `profile:mass_band:failed_primitive` and
`*:mass_band:failed_primitive`. Per-strategy attempts, successes, and force
aborts feed a deterministic bandit score with a strong force-risk penalty. The
task context contributes 75% and global transfer contributes 25%.

The first failed gate in `scene stability -> suction latch -> lift -> transport
-> placement -> release` is the primitive gap. A later successful recovery is
written to `primitive-acquisition-manifest.json` with its source failure,
recovery strategy, summary paths, and primitive task text. It remains only a
candidate until RGB-D frames and actions pass dataset audit.

## Radeon development result

The first `pash_arm` attempt succeeded for a 0.40 kg small carton, so no extra
retry ran. It lifted 8.11 cm, transported 30 cm, and placed at 2.20 cm error
with zero suction breaks and 6.25 N peak contact force. SmolVLA made 84
inferences and materially actuated 4,694 physics steps. The left-arm residual
actuated 2,343 steps with 30/30 accepted IK updates. Force Memory tightened once
to a minimum cap of 0.292; emergency stops were zero. Warm mean/P95 inference
was 200.54/209.89 ms.

This is integration evidence, not evidence that retries improve success. See
`evidence/mobile_bimanual/adaptive_retry_v1/` for compact metrics and hashes.

```bash
PYTHONPATH=src:. python scripts/run_mobile_adaptive_retry_rocm.py \
  --output outputs/pash-adaptive-retry \
  --strategy-memory outputs/pash-strategy-memory.json \
  --smolvla-checkpoint <checkpoint> \
  --backend rocm --max-attempts 3 --policy-hz 3 \
  --parcel-profile small_carton \
  --parcel-size-m 0.20 0.12 0.20 \
  --parcel-mass-kg 0.40 --parcel-friction 0.80
```

Any paper ablation must report first-attempt success, eventual success within
three attempts, mean attempts, force aborts, and strategy distribution
separately.
