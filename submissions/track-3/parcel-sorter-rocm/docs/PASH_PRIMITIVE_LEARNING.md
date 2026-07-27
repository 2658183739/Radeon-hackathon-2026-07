# PASH Primitive Learning and Progress-Channel SmolVLA

## Status

This extension converts the existing PASH retry writeback from a summary-only
candidate into trainable primitive episodes. It has completed both a 10-step
wiring smoke and a 2,800-step single-Radeon candidate training run. It has
**not** yet passed the frozen promotion campaign, so the retained v2 checkpoint
remains the production checkpoint.

| Capability | Evidence status |
| --- | --- |
| Event-based primitive segmentation | 4,557/4,557 frames agree with held-out instrumentation labels |
| Primitive-steerable dataset | 7 episodes, 24 task texts, 43-D state, RGB, 20-D action |
| Progress-channel SmolVLA training | 2,800 AMP steps, batch 8, completed on one Radeon/ROCm device |
| Offline Harness ablation | 42/42 stage samples entered the safety envelope; raw VLA was 0/42 |
| Closed-loop mechanism pair | both checkpoints succeeded; 2,800-step candidate placed at 0.90 cm |
| Task improvement or generalization | not established by the single paired case |

## Method

PASH now uses three adaptation time scales:

1. **Within a rollout:** Force Memory and the Harness candidate gate reduce or
   remove learned authority without changing model weights.
2. **Between attempts:** the first failed primitive selects one of at most three
   audited retry strategies using task-specific and global episodic memory.
3. **Between campaigns:** successful trajectories are segmented and relabeled,
   SmolVLA is retrained offline on Radeon, and a frozen paired gate either
   promotes the checkpoint or keeps the previous one.

The segmenter does not read `observation.stage_id` or privileged parcel pose.
It recovers two sustained base-motion intervals and two left tri-suction tool
events:

```text
idle -> base approach -> suction attach -> lift -> base transport
     -> place -> suction release -> retreat
```

These events produce six contiguous primitives: `pregrasp`,
`grasp_approach`, `lift`, `transport`, `place`, and `release`. The instrumented
stage field is used only after segmentation to measure agreement.

Each segment receives its own language instruction while retaining the parent
sorting task. A normalized progress target from 0 to 1 is appended to the
19-D control vector. The 20th output is telemetry and a future completion hint;
only the first 19 values can enter Harness. It therefore cannot bypass the
35 N limit, tool interlocks, rigid dual-arm projection, IK, or the deterministic
fast loop.

## Automatic improvement cycle

Use `--primitive-learning` on the existing resumable cycle:

```bash
cd /workspace/parcel-sorter-opt-v1
source /workspace/rdna/bin/activate
python scripts/run_mobile_self_improvement_cycle_rocm.py \
  --cycle-id primitive-v1 \
  --cycle-dir outputs/mobile-self-improvement-primitive-v1 \
  --source-campaign-audit outputs/source-frozen-holdout-v2-audit.json \
  --base-training-config configs/mobile_suction_collection_v1.json \
  --baseline-checkpoint outputs/train/mobile-smolvla-mass-aware-b8w4-2400step-v2/checkpoints/002400/pretrained_model \
  --holdout-trials 100 --holdout-seed 20260728 \
  --training-steps 2800 --batch-size 8 --num-workers 4 \
  --policy-hz 3 --evaluation-workers 4 --primitive-learning
```

The new mode inserts `build_primitive_dataset` and
`audit_primitive_dataset` before Radeon training and selects the 20-D action
contract. It preserves the existing isolated baseline/candidate evaluation,
Wilson non-inferiority gate, zero-force-violation requirement, and rollback.
Weights never change during an active robot rollout.

## Radeon smoke evidence

The source curriculum contained 7 episodes and 4,557 RGB-D frames. The
event-only segmenter generated 24 primitive task texts across four parcel
profiles and exactly matched all 4,557 instrumentation labels. Dataset audit
passed with finite 43/20 tensors, unit quaternions, binary tool commands,
metric depth, no privileged policy input, and progress in `[0, 1]`.

SmolVLA loaded 450,061,536 total parameters and trained 99,896,352 parameters
for 10 AMP steps on one `gfx1100` Radeon with ROCm 7.2.1. The run saved a
checkpoint whose model SHA-256 is
`86635367299d0ba1c30af4130138fffabc4dfe6bbe6adc8785f7f93ef9fcdb58`.
One cold checkpoint-reload call produced finite control and progress values;
Harness retained the 19-D execution contract. The cold latency is not used as
a performance claim.

Evidence files:

- `evidence/training/pash-primitive-dataset-v2-manifest.json`
- `evidence/training/pash-primitive-dataset-v2-audit.json`
- `evidence/training/pash-primitive-smolvla-rocm-smoke-v1.json`
- `evidence/training/pash-primitive-smolvla-single-inference-rocm-v1.json`
- `evidence/training/pash-primitive-smolvla-rocm-smoke-v1.log`

## Full Radeon candidate training

The same audited dataset was used for one 2,800-step candidate run with batch
size 8, four data workers, AMP, and one Radeon. The job logged all 2,800 updates
and completed in 442 seconds at 6.33 steps/s. Mean loss over the first 100
updates was 1.5761 and over the final 100 was 0.0733. The saved model SHA-256 is
`b83d5299123e1cfeac3463679e021816f0999799492f6fafea828bf823761482`.

Checkpoint reload evaluated the middle frame of every episode-stage pair: 7
episodes x 6 primitives = 42 samples. Primitive-progress MAE was 0.1157 and
warm inference mean/P95 was 146.55/147.47 ms. Raw VLA actions were outside the
registered expert envelope on all 42 samples; deterministic clipping and
Harness-Lite brought 42/42 inside. Harness-Lite reduced mean action MAE from
0.00656 raw to 0.00527 with zero offline fallbacks and emergency stops. This is
why the project retains Harness authority instead of treating lower training
loss as permission for unconstrained execution.

Evidence files:

- `evidence/training/pash-primitive-smolvla-rocm-2800step-v1.json`
- `evidence/training/pash-primitive-smolvla-rocm-2800step-v1.log`
- `evidence/training/pash-primitive-smolvla-2800step-offline-ablation-v1.json`
- `evidence/training/pash-primitive-smolvla-2800step-training-curve-v1.png`
- `evidence/training/pash-primitive-smolvla-2800step-training-curve-v1.pdf`
- `evidence/training/pash-primitive-smolvla-rocm-2800step-v1-SHA256SUMS`

The curve shows every logged update plus a fixed 100-update rolling mean. It is
one training trajectory (`n=1 run`), so no uncertainty band or convergence
claim is added. `scripts/plot_primitive_training_curve.py` reproduces both
formats from the complete log and rejects logs with a different update count.

## Matched closed-loop mechanism comparison

Both the 10-step smoke checkpoint and the 2,800-step candidate were loaded into
the same unmodified Harness-controlled `small_carton` task. Both completed
pickup, transport, placement, and release. The candidate reduced placement
error from 1.28 cm to 0.90 cm and inference calls from 79 to 69. Its suction
latched once and never broke; peak contact force was 5.48 N, Harness fell back
twice, emergency stops were zero, and the deterministic transport deadline
handoff was no longer needed.

Compact evidence is in `evidence/mobile_bimanual/primitive_learning_v1/` and
`evidence/mobile_bimanual/primitive_learning_2800step_v1/`. The 29.4% placement
error reduction and 12.7% call reduction are descriptive results for one
deterministic paired case. They do not establish a task success rate, causal or
statistical improvement, convergence, unseen-object generalization, or a
promotion over the retained v2 checkpoint.

## Failure record

The first generated dataset stored task text as a normal parquet column.
LeRobot v3 expects task text as the named pandas index, so training failed
before the first batch with `Task cannot be None`. The builder was corrected to
preserve that schema, the dataset was rebuilt as v2, an actual LeRobot sample
returned non-null text and a 20-D action, and the second training run completed.
The failed run is not counted as training evidence.

## Research provenance and limits

Harness VLA motivated the separation between learned contact primitives,
deterministic motion, memory, and retry scheduling
([project](https://harnessvla.github.io/),
[paper](https://arxiv.org/abs/2607.08448)). InSight motivated primitive-level
relabeling, a progress channel, gap acquisition, and offline writeback:
Maggie Wang, Lars Osterberg, Stephen Tian, Ola Shorinwa, Jiajun Wu, and Mac
Schwager, *InSight: Self-Guided Skill Acquisition via Steerable VLAs*,
[arXiv:2606.24884](https://arxiv.org/abs/2606.24884),
DOI `10.48550/arXiv.2606.24884`.

The InSight metadata was retrieved from OpenAlex `/works` with exact-title
search on 2026-07-27; OpenAlex returned the arXiv identifier, DOI, authors, date,
and CC-BY repository record. The arXiv Atom title-search request timed out, so
the report cites the resolved arXiv record rather than the secondary article.

This implementation is an original PASH adaptation for a tri-suction,
V-cradle, mobile dual-Franka simulator. It does not copy Harness VLA or InSight
code. The current 10-step smoke proves wiring, not convergence, task improvement,
unseen-object generalization, autonomous VLM gap discovery, or sim-to-real.
