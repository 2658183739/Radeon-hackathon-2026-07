# Mobile SmolVLA Self-Improvement Cycle

## Purpose

`scripts/run_mobile_self_improvement_cycle_rocm.py` provides one resumable command for
failure replay, expert curriculum collection, dataset audit, Radeon training, offline
Harness ablation, frozen closed-loop evaluation, and checkpoint promotion. It is a
controlled nearline process between episodes; an active robot rollout never mutates its
weights.

## Current v3 cycle

- Source failure: the frozen v2 0.72 kg medium carton failed to lift before suction latch.
- Automatic bridge: preserve size, friction, and offset while reducing mass to 0.648 kg.
- Training curriculum: six successful expert cases plus the bridge, seven cases total.
- New holdout: generate and hash 100 unseen parameter trials with seed `20260728` before training.
- Stratification: 25 trials each for small cartons, flat mailers, electronics boxes, and medium cartons.
- Isolation: neither episode IDs nor complete physical parameter tuples may overlap training.

Once the v2 failure is inspected to create training curriculum, v2 is development evidence
and can never be reused as the v3 holdout.

## Radeon command

```bash
cd /workspace/parcel-sorter-opt-v1
/workspace/rdna/bin/python scripts/run_mobile_self_improvement_cycle_rocm.py \
  --cycle-id v3 \
  --cycle-dir outputs/mobile-self-improvement-v3-cycle1 \
  --source-campaign-audit outputs/source-frozen-holdout-v2-audit.json \
  --base-training-config configs/mobile_suction_collection_v1.json \
  --baseline-checkpoint outputs/train/mobile-smolvla-mass-aware-b8w4-2400step-v2/checkpoints/002400/pretrained_model \
  --holdout-trials 100 --holdout-seed 20260728 \
  --training-steps 2800 --batch-size 8 --num-workers 4 --policy-hz 3 \
  --evaluation-workers 4
```

Add `--resume` after interruption. `--dry-run` freezes inputs and renders commands without
executing them; `--stop-after <step>` supports controlled staging. Resume is rejected if a
replay, curriculum, or frozen holdout artifact has changed.

## Promotion gate

A candidate writes `promoted-checkpoint.json` only when both baseline and candidate complete
the same holdout of at least 100 trials, candidate success is at least 80%, point-estimate and
Wilson-lower-bound non-inferiority stay within five percentage points, force violations are
zero, VLA actuation occurs in every trial, and every trial records one Radeon GPU with ROCm.
The baseline and candidate physical-parameter sequences are compared exactly before the
statistical gate is accepted. Rejected candidates remain isolated and report
`completed_not_promoted` with individual checks. A passing candidate atomically replaces
`configs/active_mobile_smolvla.json`; the registry stores and verifies both the model SHA-256
and promotion-evidence SHA-256 before the next episode can load it.

## Measured result on 2026-07-27

The full cycle ran on one AMD Radeon `gfx1100` with ROCm 7.2.1. All seven curriculum
episodes succeeded. The generated 0.648 kg bridge placed within 1.30 cm and reached 8.60 N
peak contact force. The merged dataset contains 4,557 frames, complete six-stage coverage,
a 43/19 state/action contract, and no privileged parcel pose in policy inputs.

SmolVLA v3 trained for 2,800 steps (4.92 epochs) with AMP, batch 8, and four workers in
about 7 minutes 20 seconds. Peak memory was 2.21 GB and final-step loss was 0.037. On 42
training episode-stage samples, raw v3 scored 0.019790 MAE and 0/42 action-envelope passes;
Harness-Lite scored 0.005370 MAE and 42/42 passes, versus 0.004468 for the executor-matched expert.

Four isolated rollout workers raised observed GPU utilization from roughly 13% sequentially
to as high as 85%. The audit found two infrastructure failures with missing summaries. They
were rerun under identical settings after fixing scientific-notation negative CLI arguments,
so they were not miscounted as task failures.

| Frozen 100-trial campaign | v2 baseline | v3 candidate |
| --- | ---: | ---: |
| Overall success | 96/100 | 91/100 |
| Wilson 95% | 90.16%--98.43% | 83.77%--95.19% |
| Small carton | 25/25 | 23/25 |
| Flat mailer | 22/25 | 22/25 |
| Electronics box | 25/25 | 25/25 |
| Medium carton | 24/25 | 21/25 |
| Mean successful placement error | 1.40 cm | 1.06 cm |
| 35 N force violations | 0 | 0 |

Paired outcomes were 90 both-success, three both-fail, one candidate-only success, and six
baseline-only successes. v3 passed the absolute 80%, point non-inferiority, zero-force,
all-VLA-actuated, and all-single-Radeon gates, but failed Wilson lower-bound non-inferiority.
The cycle therefore reports `completed_not_promoted` and retains v2. The result shows that a
single boundary bridge can improve placement precision and offline error without improving
full-distribution closed-loop reliability.

The cycle directory records source SHA-256 values, the holdout hash, exact commands, per-step
logs, dataset audit, offline ablation, compact paired campaigns, Wilson intervals, and the
promotion decision. Large datasets and weights remain in the Radeon workspace.
Compact evidence and SHA-256 values are checked in under
`evidence/mobile_bimanual/self_improvement_v3/`.

## Subsequent primitive-progress promotion

The rejected v3 result remains negative evidence; it is not the current model.
The later 2,800-step primitive-progress candidate reused the paired frozen
100-trial protocol, scored 94/100 against the 96/100 baseline, had zero force
violations, and passed every registered gate. Its model artifact and promotion
record now form the active double-hash registry in
`configs/active_mobile_smolvla.json`. Future cycles use the same rule: rejected
candidates leave that file byte-for-byte unchanged, while a passing candidate
is activated atomically between episodes.
