# Mobile SmolVLA RGB-D Ablation

## Question and paired protocol

This experiment tests whether adding the already recorded metric depth view improves the mobile
SmolVLA policy enough to justify a closed-loop campaign. RGB v3 and RGB-D v1 use the same seven
expert episodes, 4,557 frames, task text, 43-D non-privileged state, 19-D action, seed 11, AMP,
batch 8, four workers, 2,800 updates, frozen vision encoder, and expert-only training. RGB-D adds
`observation.images.overhead_depth_rgb` through the upstream SmolVLA multi-image interface. The
raw metric TIFF remains the source of record.

The RGB-D dataset audit checked all state/action/task stages and 65 distributed depth pairs.
Every stored three-channel depth image exactly matched the deterministic encoding of its metric
depth source. No parcel ground-truth pose is a policy input.

## Single-Radeon training

Training ran on one AMD Radeon `gfx1100` with ROCm 7.2.1 and PyTorch 2.9.1+ROCm.

| Metric | RGB v3 | RGB-D v1 |
| --- | ---: | ---: |
| Updates / epochs | 2,800 / 4.92 | 2,800 / 4.92 |
| Wall time | about 7m20s | 8m51s |
| Steady throughput | about 63 samples/s | about 43 samples/s |
| Peak VRAM | 2.21 GB | 2.75 GB |
| Final-step loss | 0.037 | 0.038 |

The second visual stream increased training time by about 20.7%, peak VRAM by about 24.4%, and
reduced steady throughput by about 31.7%. It still used less than 6% of the 47.98 GiB Radeon VRAM.

## Paired 42-stage result

Both checkpoints were reset and evaluated with identical episode, stage, frame, and seed keys.

| Executable path | RGB mean MAE | RGB-D mean MAE | RGB-D change | RGB / RGB-D envelope |
| --- | ---: | ---: | ---: | ---: |
| Raw SmolVLA | 0.019790 | 0.020097 | +1.55% | 0/42 / 0/42 |
| Safety clipped | 0.020893 | 0.020955 | +0.30% | 42/42 / 42/42 |
| Harness-Lite | 0.005370 | 0.005442 | +1.35% | 42/42 / 42/42 |

Mean offline inference latency increased from 145.63 ms to 159.69 ms (+9.65%). The preregistered
gate requires paired Harness improvement, no envelope regression, and at most 25% latency growth.
RGB-D passed the safety and latency checks but failed the improvement check, so the decision is
`rgb_retained` and a 100-trial RGB-D campaign is not authorized.

## Online integration check

One known development carton was run only to verify the online two-image path. It completed
pickup, 30 cm transport, placement, and release with 68 RGB-D inferences and 3,410 VLA-actuated
physics steps. Peak contact force was 7.70 N, no emergency stop occurred, and warm inference was
211.44 ms on average. This one development run is not a success-rate or generalization result.

## Interpretation

The implementation establishes real RGB-D training and online inference on ROCm, but the current
top-view depth stream adds little information on this small, visually simple training population.
Future depth work needs a disjoint ambiguity-focused dataset (appearance-matched height changes,
occlusion, clutter, and transparent/low-texture proxies) and a new frozen evaluation. It must not
tune on the current paired samples or claim that adding a modality alone improves capability.

Compact evidence is in `evidence/mobile_bimanual/rgbd_v1/`; the 907 MB model remains on the Radeon
host and is bound by `checkpoint-SHA256SUMS`.
