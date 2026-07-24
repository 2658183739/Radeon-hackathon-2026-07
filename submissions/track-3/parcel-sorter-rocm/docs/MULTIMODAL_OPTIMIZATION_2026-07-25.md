# Multimodal Optimization Record: 2026-07-25

This is a learnable engineering record, not private chain-of-thought. Each step
captures the observable input, alternatives, decision, reason, code surface,
and verification result.

## Outcome

- Fixed a 1,000x depth-scale defect: Genesis rasterizer depth is already in
  metres and must not be multiplied by `0.001`.
- Added raw metric depth plus a deterministic three-channel depth view for
  standard LeRobot visual backbones.
- Added dataset quality gates that allow the old shard for RGB training but
  reject it for RGB-D.
- Made learned-policy inference discover RGB-D inputs from checkpoint config.
- Completed collection, one ACT RGB-D update, checkpoint save/load, and one
  Genesis closed-loop inference run on the single Radeon.
- Did not claim task improvement from a one-step smoke model.

## Step record

| Step | Evidence or event | Decision and reason | Verification |
| --- | --- | --- | --- |
| 1 | Old metadata declared metres, but depth median was `0.00117156` | Treat the modality as suspect before adding a model branch | Compared stats with physical camera distance |
| 2 | Source multiplied all Genesis depth by `0.001` | Inspect upstream implementation instead of editing metadata | Genesis camera near/far are documented in metres; point-cloud reconstruction uses depth directly |
| 3 | Upstream and scene scale agreed that raw depth is metres | Remove the conversion, preserve float32 | Unit test now preserves `0.8` and `3.4185` m |
| 4 | ACT/Diffusion ResNet visual inputs expect three channels | Keep raw depth and add an invert-normalized 0.25-4.0 m grayscale view repeated to RGB | Shape, dtype, clipping and invalid-pixel tests |
| 5 | Old data has no derived view and invalid raw scale | Add a pre-training metadata audit; warning for RGB, hard error for RGB-D | Old RGB audit passes with warning; RGB-D exits 2 |
| 6 | A manual inference flag could disagree with a checkpoint | Read visual feature keys from checkpoint config | Existing RGB checkpoints remain valid; unknown camera keys are rejected |
| 7 | New one-episode shard was collected on Radeon | Validate sensor scale before training | 152 frames; depth `0.737-3.535` m, median `1.164` m; audit passed |
| 8 | First training smoke used split 0 with default eval steps | Classify as a config failure, not a ROCm/RGB-D failure | LeRobot rejected before model creation |
| 9 | The invalid combination was reusable | Add shell preflight requiring eval steps 0 when split is 0 | Bash syntax passed; corrected retry started |
| 10 | Corrected RGB-D ACT smoke used two visual inputs | Keep as pipeline evidence only | 51,577,736 parameters; one update; 2.71 s progress step; 0.98 GB reported peak |
| 11 | Saved checkpoint requested both camera keys | Run it through the generic safe policy adapter | Closed loop completed without interface error; mean 3.48 ms, P95 11.53 ms |
| 12 | One-update policy failed the parcel task | Preserve the failure and avoid capability language | Success 0/1, no force event; interface result only |

The first remote verification wrapper ended with a PowerShell/Bash variable
expansion error after all 71 tests and both audits had run. The expected exit
code check was repeated with single-quoted remote input and returned exactly 2.
This is recorded as orchestration failure, not a project-code failure.

## Code capability map

| File | New capability | Boundary |
| --- | --- | --- |
| `genesis_env.py` | Correct float32 metric depth | No retroactive repair of old arrays |
| `dataset.py` | Raw depth plus deterministic depth view | Fixed 0.25-4.0 m encoding is an ablation input, not a calibrated sensor model |
| `data_quality.py` | Feature-shape and depth-plausibility audit | Metadata audit; it does not inspect every pixel |
| `audit_dataset.py` | CLI gate and JSON evidence output | Fails RGB-D requests when features/scale are invalid |
| `policy.py` | Checkpoint-driven RGB or RGB-D batching | Supports only declared overhead RGB and derived depth keys |
| `train_act_rocm.sh` | `ACT_USE_DEPTH=true` and split/eval guard | Requires newly collected depth-view feature |
| `train_diffusion_rocm.sh` | `DIFFUSION_USE_DEPTH=true` and split/eval guard | Training effectiveness still unverified |

## Reproduction commands

Audit an RGB-only-compatible old shard:

```bash
python scripts/audit_dataset.py --dataset-root <dataset>
```

Require valid RGB-D and train matched ACT:

```bash
python scripts/audit_dataset.py --dataset-root <dataset> --require-depth-rgb
ACT_USE_DEPTH=true ACT_STEPS=30000 ACT_SEED=42 \
  bash scripts/train_act_rocm.sh <dataset> outputs/train/act-rgbd-seed42
```

The matched RGB control uses the same command, output directory and seed with
`ACT_USE_DEPTH=false`. Never reuse an output directory between conditions.

## Next decision gate

Collect fifteen exact catalog-v2 blocks, yielding 300 successful episodes if
all target strata can be completed. Do not silently replace failed hard
profiles with easy profiles. Freeze the episode manifest, then train RGB and
RGB-D ACT for three seeds. Promote depth only if held-out closed-loop success
improves without higher drop/force rates and the latency cost is reported.
