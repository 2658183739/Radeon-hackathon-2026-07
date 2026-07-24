# Components, Verified Capability, and Remaining Work

| Component | Implementation | Verification status |
| --- | --- | --- |
| Physics | Pinned Genesis World 1.2.3 | Radeon physics, contact, and headless rendering verified |
| Robot | Franka Panda MJCF from Genesis | Pick, lift, transport, and placement executed |
| Parcel task | Random size, mass, friction, pose, and two bins | 80% over 120 episodes; fixed 10-seed baseline 90% |
| Catalog v2 | 12 weighted Box/Cylinder training strata plus 4 evaluation boundaries | One-case-per-profile regression complete; 8/12 completed, not a success-rate claim |
| Tube handling | Correct cylinder geometry, scoped rolling physics, axis grasp, friction pads, centered close | Lifted 35.5 mm in one diagnostic; transfer/placement still unresolved |
| Sensors | RGB-D, joints, end-effector pose, contact | Shapes verified; depth stored in metres |
| Expert | Truth-based geometry, IK, PD, gripper force | 96/120 formal success; phase-aware approach added |
| Safety | Verification, retry, bin check, force abort | Unit-tested and exercised on Radeon |
| Data | JSONL plus LeRobotDataset RGB-D | 96 successful episodes, 11,753 frames |
| Learning | LeRobot ACT 52M | 5,000-step ROCm run; best measured range result at step 4,000 |
| Diffusion | Configurable LeRobot Diffusion entry | 76.6M one-step ROCm path smoke only; no policy claim |
| VLA | SmolVLA offline-checkpoint entry | Dependencies verified; base checkpoint, training, and evaluation pending |
| RGB-D fusion | Metric depth recorded independently from RGB | Fusion model and matched ablation pending |
| ROS 2 | Planned adapter boundary | Not implemented; simulator-policy contract takes priority |
| GPU | Parallel simulation and training benchmark | 46,582 env-steps/s; 80 samples/s AMP batch 32 |
| Evidence | Summary JSON, logs, hashes, MP4 support | Small raw evidence committed; large artifacts pending release |

## Next gates

1. Add a versioned concave finger adapter or V-cradle and run a matched
   multi-episode ablation; do not continue single-episode force tuning.
2. Grow to at least 300 successful balanced expert episodes.
3. Run three-seed ACT and compact Diffusion training with the same held-out set.
4. Add RGB-D late fusion and a matched RGB-only ablation.
5. Profile the complete frame on Radeon before low-level optimization.
