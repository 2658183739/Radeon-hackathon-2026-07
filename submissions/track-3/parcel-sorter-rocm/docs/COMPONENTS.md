# Components, Verified Capability, and Remaining Work

| Component | Implementation | Verification status |
| --- | --- | --- |
| Physics | Pinned Genesis World 1.2.3 | Radeon physics, contact, and headless rendering verified |
| Robot | Franka Panda MJCF from Genesis | Pick, lift, transport, and placement executed |
| Parcel task | Random size, mass, friction, pose, and two bins | 80% over 120 episodes; fixed 10-seed baseline 90% |
| Sensors | RGB-D, joints, end-effector pose, contact | Shapes verified; depth stored in metres |
| Expert | Truth-based geometry, IK, PD, gripper force | 96/120 formal success; phase-aware approach added |
| Safety | Verification, retry, bin check, force abort | Unit-tested and exercised on Radeon |
| Data | JSONL plus LeRobotDataset RGB-D | 96 successful episodes, 11,753 frames |
| Learning | LeRobot ACT 52M | 5,000-step ROCm run; best measured range result at step 4,000 |
| GPU | Parallel simulation and training benchmark | 46,582 env-steps/s; 80 samples/s AMP batch 32 |
| Evidence | Summary JSON, logs, hashes, MP4 support | Small raw evidence committed; large artifacts pending release |

## Next gates

1. Re-evaluate the phase-aware approach on the same 120 episodes.
2. Run image-transform and training-seed ablations.
3. Grow the dataset with hard-example recollection.
4. Add RGB-D policy fusion and stratified robustness reporting.
5. Profile the complete frame on Radeon before low-level optimization.
6. Upload hashed model/data artifacts and record the final video.
