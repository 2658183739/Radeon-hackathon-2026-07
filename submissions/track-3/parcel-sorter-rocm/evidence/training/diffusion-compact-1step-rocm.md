# Compact Diffusion One-Step Radeon Smoke

This is a matched training-path optimization smoke, not a closed-loop policy
capability result.

| Field | Value |
| --- | --- |
| Experiment | `diffusion-compact-smoke-v1` |
| Repository state | local change set after `8dea503` |
| Command | `DIFFUSION_STEPS=1 DIFFUSION_BATCH_SIZE=2 DIFFUSION_NUM_WORKERS=0 DIFFUSION_DOWN_DIMS=256,512,1024 DIFFUSION_HORIZON=32 DIFFUSION_N_ACTION_STEPS=8 DIFFUSION_INFERENCE_STEPS=10 DIFFUSION_USE_AMP=true bash scripts/train_diffusion_rocm.sh <dataset> outputs/train/diffusion-compact-smoke-v1` |
| Dataset split | 86 train episodes / 10 eval episodes |
| Policy | LeRobot Diffusion, 76,597,288 parameters |
| Device | AMD Radeon Graphics, `cuda:0` HIP device, one visible GPU |
| ROCm | PyTorch 2.9.1 ROCm 7.2.1 |
| Result | One forward/backward/optimizer step completed; checkpoint saved |
| Step duration | 23.60 s training progress time; 41.10 s wrapper time including setup |
| Model SHA-256 | `de1241d77d41517d68e7e3ec114b5b37f3d1595b2b847eb13abc2d391a2e54f5` |
| Config SHA-256 | `c86a3f0b81a546611f91a122317da2d68318dfdc781927d541a8af7d53c89643` |
| Train config SHA-256 | `e0767a9580e7a98b610d66093ed45cff8df5e83b34c0f05592dc43aca283dd79` |

The previous one-step smoke used `[512,1024,2048]`, 263,762,728 parameters,
and about 53 seconds including setup. The compact run is approximately 71%
smaller by parameter count and 55% shorter in the observed one-step wall time.
This comparison is directional because setup and cache state were not controlled
as a formal benchmark. The next experiment must use identical seeds, warm-up,
and closed-loop episodes before selecting a model.

The first retry failed before model creation because the dynamic LeRobot CLI
expects `down_dims` as one list-valued argument. The script now emits
`"[256,512,1024]"` and checks the horizon/downsampling invariant before launch.
That failure is recorded as command integration, not a model failure.
