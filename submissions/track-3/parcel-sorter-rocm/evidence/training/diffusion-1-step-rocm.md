# Diffusion One-Step Radeon Smoke

This is a training-path smoke, not a policy capability result.

| Field | Value |
| --- | --- |
| Command | `DIFFUSION_STEPS=1 DIFFUSION_BATCH_SIZE=2 DIFFUSION_NUM_WORKERS=0 bash scripts/train_diffusion_rocm.sh <dataset> outputs/train/diffusion-script-smoke-v2` |
| Dataset split | 86 train episodes / 10 eval episodes |
| Policy | LeRobot Diffusion, 263,762,728 parameters |
| Device | AMD Radeon Graphics, `cuda:0` HIP device |
| ROCm | PyTorch 2.9.1 ROCm 7.2.1 |
| Result | Model created, optimizer created, one forward/backward step completed, checkpoint saved |
| Duration | About 53 seconds for one step, including setup |

The first attempt stopped before model creation because `diffusers` was absent.
The bootstrap now installs LeRobot's `diffusion` and `smolvla` extras. The
second attempt completed. No success rate, loss trend, or competition claim is
derived from one optimization step.
