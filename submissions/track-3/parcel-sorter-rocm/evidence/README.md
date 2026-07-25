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
| `expert/radeon-dataset-400-v2-failure-analysis.json` | Trace-derived failure attribution for the 400-attempt Radeon expert run | `12aae22a747759f96edb3a742e17cc6ba54c90480448198bd93f4153eecd7993` |
| `act/checkpoint-4000-episodes-10-19.json` | ACT 4,000-step closed-loop evaluation | `d9e4a88af2e5d0f77c3e74cc9b79f04eb62af794f3bda895132aa97b44953b0d` |
| `act/checkpoint-5000-episodes-10-19.json` | ACT 5,000-step same-seed evaluation | `73bdbfc5b312adb7606fb1b05691fc2ab859d61cb68f25bf9a980ce8b8b63956` |
| `training/act-5000-amp-b32.log` | Formal 5,000-step ACT training log | `862896542df367351d4e2143935441ece03d06a8d64b7401f9fefade6f1278f3` |
| `training/act-model-sweep-smoke-5k-v2.json` | Six-cell ACT RGB/RGB-D 5,000-step integration smoke manifest and checkpoint hashes | `a144d87fe667c4ce1f5f34934747a7aa54e905106d73d97abe8db21d0362820a` |
| `training/act-model-sweep-smoke-5k-v2-status.csv` | Machine-readable six-cell status table; all statuses are 0 | N/A |
| `expert/radeon-reset-ab-v1-comparison.json` | Matched Radeon reset-pose A/B; candidate C rejected by safety/task gates | `42ca67ec0566297514ae898c7e1ffd8d6830ae1f26c1c88684306000cece90a6` |
| `expert/radeon-reset-ab-v1-baseline-summary.json` | Compact 20-episode baseline summary; raw traces remain on the cloud instance | `43aca26198a4a3a51f78d47dd89ee40584fc0c976265b0deb505d3eec2615732` |
| `expert/radeon-reset-ab-v1-candidate-c-summary.json` | Compact 20-episode pose-C summary; raw traces remain on the cloud instance | `a3aadb9f27e1c5642bac9a913e691d043b8a9ba6c7db8f85616b45651fe6ac81` |
| `expert/radeon-reset-ab-v1-run.log` | Radeon preflight, Genesis run log, and post-summary exit diagnostic | `aef02638c6546c2d4645fca2143248d760ed88eedd396e2610bfddb807ad9a2e` |
| `expert/radeon-reset-ab-v1-SHA256SUMS` | Hash manifest for the reset A/B evidence | N/A |
| `expert/radeon-size-aware-ab-v1-comparison.json` | Matched Radeon size-aware transit A/B; 20 mm margin candidate rejected | `c21b9f33b584e882a133d68f09dfaebd42671c3d60ce54ceddc20e8222cda12f` |
| `expert/radeon-size-aware-ab-v1-baseline-summary.json` | Compact 20-episode baseline summary for the size-aware comparison | `82cce9c23f755fc95c998810f40e53ea9fb2c337d12304f92307f06db2db17e6` |
| `expert/radeon-size-aware-ab-v1-candidate-size-aware-summary.json` | Compact rejected size-aware candidate summary; raw traces remain on the cloud instance | `e9711e6225df1207a427c792d8ba6d47fd1f929b0ab1d5ca7663a5a6e2f8c26f` |
| `expert/radeon-size-aware-ab-v1-baseline-failure-analysis.json` | Trace-derived baseline failure attribution for the matched 20 episodes | `7f478ea03a6ba0e6859afb5496aba5eed4614be7cc087b4bdb66ff19e9e8daa4` |
| `expert/radeon-size-aware-ab-v1-candidate-failure-analysis.json` | Trace-derived candidate failure attribution and retry regression | `03e133f66884a776616d694b66899522529a3b7d9d1c06e811cc8d34b927ae7f` |
| `expert/radeon-size-aware-ab-v1-candidate.log` | Candidate Radeon Genesis log, including final summary and runtime warnings | `2e9a5a57dd66af12020dae7f083e6be21ecfb5804fda24594cb5c1cccf1ad8ac` |
| `expert/radeon-size-aware-ab-v1-SHA256SUMS` | Hash manifest for the size-aware negative-control evidence | N/A |
| `expert/radeon-retry-retreat-ab-v1-comparison.json` | Matched Radeon recovery-aware retry A/B; promising but below absolute safety/task gates | `47cfd58a09e344db8c60751167e5504285d82f27276249e00d26dd07df9efec2` |
| `expert/radeon-retry-retreat-ab-v1-baseline-summary.json` | Compact 20-episode baseline summary for recovery retry comparison | `ae38f67d6665a18b1bad46cc38f1244b5189ed55011343077f9f16f6b76c9d1b` |
| `expert/radeon-retry-retreat-ab-v1-candidate-summary.json` | Compact recovery-aware retry candidate summary; not accepted as default | `cd4103caf414687eee3c44e44933b9a4c164f46edc7ab05e730197164cecfeb3` |
| `expert/radeon-retry-retreat-ab-v1-baseline-failure-analysis.json` | Baseline trace-derived failure attribution | `b468064bdbd200e5b021cddda98856e9124c01a5033ae8c807850a5d5fcd99e6` |
| `expert/radeon-retry-retreat-ab-v1-candidate-failure-analysis.json` | Candidate trace-derived retry and force attribution | `36a826c40de6d3743f0fdc4e50eb9302478a9068ac8194d33b0b3ed9b0dcf10f` |
| `expert/radeon-retry-retreat-ab-v1-SHA256SUMS` | Hash manifest for the recovery-aware retry experiment | N/A |
| `expert/radeon-approach-step-ab-v1-baseline-summary.json` | Compact baseline summary for the 40 mm approach-step control | `40274f8e6149a8aeb26129933c47aba2e43c84679e30be3f75dafd5c85125d89` |
| `expert/radeon-approach-step-ab-v1-candidate-summary.json` | Compact rejected 20 mm approach-step summary | `ed7f367eac7e16def48d4198088179836a6e60323b16e2aa30033b63f6a3e489` |
| `expert/radeon-approach-step-ab-v1-comparison.json` | Matched A/B comparison and acceptance gates | `1e7a66633d4b4b1bb2ebae3eb33753bd634c25b361acb631342ccd29b299e52b` |
| `expert/radeon-approach-step-ab-v1-baseline-failure-analysis.json` | Trace-derived baseline failure attribution | `d9b237a79e0c3adcb0c799481df6bac9a74b0bef04935f4cde0d7b1b95b3a568` |
| `expert/radeon-approach-step-ab-v1-candidate-failure-analysis.json` | Trace-derived candidate failure attribution | `2fa7f0a7a4a674855199e152b5f6de2e06e1e16d588a5f4ce4806d7015622c34` |
| `expert/radeon-approach-step-ab-v1-SHA256SUMS` | Local compact-artifact hash manifest | N/A |
| `expert/radeon-approach-step-ab-v1-remote-SHA256SUMS` | Remote full-summary and runtime-artifact hash manifest | `9651fd81e8e65609d6e3fc222a6fb94101cf4dd7d407b35f381f6084648c7b39` |
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

The approach-step A/B compact summaries omit per-frame traces but retain the
source summary path, byte count, SHA-256, full configuration, randomization,
terminal result, and per-profile metrics. The remote manifest is the digest for
the full trace-rich files on the Radeon instance.

The 400-attempt failure analysis is derived from the trace-rich remote summary,
whose path, byte count, and SHA-256 are embedded in the artifact. It contains
per-failed-episode attribution and aggregates, but not every raw trace frame.
Factor comparisons are descriptive; they are not causal estimates.

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
