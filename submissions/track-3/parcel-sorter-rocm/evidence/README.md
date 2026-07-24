# Radeon Evidence Index

This directory contains raw outputs copied from the verified single-GPU Radeon
run plus paired evidence notes that quote commands and artifact hashes. They are
small enough for Git and allow the reported aggregates to be audited without
the full dataset or checkpoint.

| File | Purpose | SHA-256 |
| --- | --- | --- |
| `expert/randomized-120-summary.json` | Formal 120-episode randomized expert result | `67fde67024579c317b375ea26a9a4b0a2d4890399d0bc5cf6e800051493e3cf5` |
| `expert/fixed-10-summary.json` | Fixed-seed expert regression baseline | `582844f397103668be4f52155ff87be3ceffec3b638937f36f0a77d4f89928a5` |
| `expert/final-approach-001-120-summary.json` | Rejected 0.01 m approach candidate, matched 120 episodes | `e1b63e28560958f3c2db5e0643665c85c6b5e7117fbe0f6df95e3f6428b4813f` |
| `expert/final-approach-001-comparison.json` | Per-episode baseline/candidate comparison and acceptance decision | `7e7bc9a8e211c305ab390b7e44c37a6080bb8ec2c9803ca56adc1119743eced9` |
| `act/checkpoint-4000-episodes-10-19.json` | ACT 4,000-step closed-loop evaluation | `d9e4a88af2e5d0f77c3e74cc9b79f04eb62af794f3bda895132aa97b44953b0d` |
| `act/checkpoint-5000-episodes-10-19.json` | ACT 5,000-step same-seed evaluation | `73bdbfc5b312adb7606fb1b05691fc2ab859d61cb68f25bf9a980ce8b8b63956` |
| `training/act-5000-amp-b32.log` | Formal 5,000-step ACT training log | `862896542df367351d4e2143935441ece03d06a8d64b7401f9fefade6f1278f3` |
| `benchmarks/parallel-radeon.json` | 1/16/64/128 environment Genesis sweep | `120e9fc4e972ebf9d4b22d4a00a5f100dba8481d65dba6cc1eca8814bb570398` |
| `benchmarks/act-training-amp-b32.log` | 200-step AMP, batch 32 throughput run | `36cc6539305a0585fe7d5b4db3fd62155fa2acef75f6fef1c045efca44215cbe` |
| `benchmarks/act-training-fp32-b8.log` | 200-step FP32, batch 8 throughput run | `009384c98d41b0bcf5876f275044a6d15172183d7b554927b4fcfbcf0a57f92e` |
| `benchmarks/act-training-fp32-b32.log` | 200-step FP32, batch 32 throughput run | `2f49edbf551c4b8f9ab827cab300c24deb2e0842966a8928b1eb6377068cd634` |
| `catalog/catalog-v1-submit-smoke.json` | Final 20-second, seven-profile catalog smoke | `7b69a332faea59f6e930acfec653ec118f858c6002cd9d78d20a06bd8f142be0` |
| `catalog/catalog-v2-baseline.json` | Twelve-profile deterministic baseline smoke | `760b09e0a38ed38ebf37dcadb91d59e5d5999d129b943d7f947c3dfe562a810f` |
| `catalog/catalog-v2-rolling-scoped.json` | Full catalog after scoped rolling-friction correction | `f0ecdc95781825653ad3395b600e476c19daa28712420808e20bb1cf94b7d9f8` |
| `catalog/README.md` | Catalog v2 candidate matrix, hashes, and keep/reject decisions | N/A |
| `training/diffusion-1-step-rocm.md` | One-step Diffusion Radeon training-path smoke | N/A |
| `training/diffusion-compact-1step-rocm.md` | Compact 76.6M-parameter Diffusion one-step smoke and checkpoint hashes | N/A |
| `multimodal/README.md` | Historical depth rejection, corrected sensor audit, and RGB-D ACT smoke | N/A |

The JSON summaries include the complete config, runtime versions, per-episode
randomization values, terminal state, and task metrics. ACT evaluation files
also contain the deterministic episode range and inference latency samples.
The rejected candidate is intentionally retained: reproducibility includes
negative results, and the comparison records why it must not become the default.

The catalog smoke is intentionally a small regression artifact. It reports four
completed box profiles and three explicit hard cases; it is not a formal
success-rate estimate. The paired catalog README records the command and hash.

Catalog v2 evidence likewise records one deterministic episode per profile and
several same-episode control/physics candidates. It must not be combined into a
formal success rate. See `catalog/README.md` for exact results and hashes.

The large generated artifacts are deliberately not stored in Git:

- 96-episode, 11,753-frame historical RGB/state LeRobotDataset: approximately
  225 MB; its depth scale is invalid and must not be used for RGB-D;
- ACT model weights: approximately 206 MB per checkpoint;
- optimizer state: approximately 413 MB per checkpoint;
- MP4 recordings and full JSONL frame traces.

They should be attached to the final submission through release or object
storage with separately published SHA-256 hashes. The documented commands
regenerate them from this source revision.
