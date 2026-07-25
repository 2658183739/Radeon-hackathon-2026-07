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

## Approach contact-brake negative control

`expert/radeon-contact-brake-ab-v1-*` contains compact summaries, failure
analyses, logs, comparison, and two hash manifests for a matched 20-episode
Radeon A/B. Only the 20 N contact-brake threshold changed. Candidate and
baseline both produced 1/20 successes, 12/20 force aborts, and zero drops;
candidate peak force increased from 111.28 N to 467.31 N, so it remains
disabled. Local SHA-256 values include baseline summary
`e79de0fd...3ce30`, candidate summary `b35298cf...4e11d`, and comparison
`5b8ead9a...40290`. Full digests are in
`expert/radeon-contact-brake-ab-v1-SHA256SUMS`; the remote manifest preserves
the full-summary provenance hashes.

## Vertical-barrier recovery negative control

`expert/radeon-approach-barrier-ab-v1-*` contains compact summaries, failure
analyses, logs, comparison, and two hash manifests for a matched 20-episode
Radeon A/B. The candidate set only
`control.approach_barrier_recovery_step_m=0.120`; it achieved 0/20 successes
and 12/20 force aborts versus baseline 1/20 and 12/20, with zero candidate
throughput, so it remains disabled. Local hashes include baseline summary
`5154a5d2...841b3a`, candidate summary `98196889...593c49`, and comparison
`172236b9...01e886`. Full digests are in
`expert/radeon-approach-barrier-ab-v1-SHA256SUMS`; the remote manifest preserves
the raw-summary provenance hashes.

## Pre-contact AABB guard negative control

`expert/radeon-approach-aabb-ab-v1-*` contains compact summaries, failure
analyses, both run logs, comparison, and local/remote hash manifests for the
matched 20-episode Radeon A/B. Only
`control.precontact_aabb_guard_distance_m=0.040` changed. The candidate invoked
65 filters over 6,003 measured approach samples at 1.625 ms mean synchronized
AABB cost, but produced 0/20 successes and 12/20 force aborts versus baseline
1/20 and 12/20. It regressed `7000005`, added one approach timeout, and had zero
throughput, so it remains disabled.

Local compact hashes include baseline summary `cc8e2967...d1ef6d`, candidate
summary `0d5ead5f...654f7c`, and comparison `5554bd40...de136`. Full values are
in `expert/radeon-approach-aabb-ab-v1-SHA256SUMS`; the remote manifest records
the trace-rich source summaries, comparison, analyses, and logs. Compact
episode records preserve the AABB safety aggregate while explicitly omitting
per-frame traces.

## Approach-compliance negative control

`expert/radeon-approach-compliance-ab-v1-*` contains compact summaries,
trace-derived failure analyses, both run logs, the exact comparison, and
local/remote SHA-256 manifests for a matched 20-episode single-Radeon A/B.
Only `control.approach_stiffness_scale` changed, from the 1.0 baseline to 0.50;
arm Kv used `sqrt(scale)` and finger gains stayed fixed.

Both runs achieved 1/20 successes, zero drops, and a 111.28 N maximum contact
force. The candidate reduced force aborts from 12 to 10 and P95 episode peak
force from 98.12 N to 71.07 N, but increased approach timeouts from 7 to 9 and
retained only 0.751x throughput. It recovered no episode and failed the
absolute success, force-abort, and throughput gates, so the default remains
1.0.

Local compact hashes include baseline summary `e552b842...24805f`, candidate
summary `84f2a585...4749f`, and comparison `e47f2573...0be61`. Full values are
in `expert/radeon-approach-compliance-ab-v1-SHA256SUMS`; the remote manifest
preserves hashes for the 6.9 MB and 9.1 MB trace-rich source summaries and all
derived artifacts.

## Operational-space velocity negative control

`expert/radeon-approach-velocity-ab-v1-*` records a matched 20-episode,
single-Radeon A/B in which only
`control.approach_velocity_control_enabled` changed. The candidate used the
Genesis end-effector Jacobian and bounded weighted damped least squares during
`MOVE_PREGRASP`; IK position control remained active for grasp, lift, and place.

Baseline achieved 1/20 successes, 12/20 force aborts, and zero drops. The
candidate achieved 0/20 successes, 13/20 force aborts, zero drops, and zero
successful throughput. It regressed episode `7000005`. P95 episode peak force
fell from 98.12 N to 67.55 N, but maximum force remained 111.28 N, so the
candidate failed the task, safety, and throughput gates and remains disabled.

The candidate executed 5,727 velocity-control samples on ROCm, averaging
1.983 ms of synchronized controller computation. The maximum command was
1.50 rad/s and maximum pose error was 0.1817 m. Local compact hashes are in
`expert/radeon-approach-velocity-ab-v1-SHA256SUMS`; both remote manifests
preserve the trace-rich source and compact provenance.

## Collision-checked reset diagnostic and negative control

`expert/radeon-contact-link-diagnostic-v1-*` records link-level, 240 Hz
initialization evidence. Failed episode `7000001` began with a hand/carton
collision on physics substep zero at about 1,270.85 N; successful episode
`7000005` had no initialization contact and later used only finger contacts,
peaking at 17.12 N. Some randomized parcels therefore intersected the
historical robot reset geometry before the 30 Hz controller could act.

`expert/radeon-collision-checked-reset-ab-v1-*` records the resulting matched
20-episode single-Radeon A/B. The candidate queried Genesis collision pairs
before integration and used a fixed fallback pose only when robot/parcel
intersection existed. It checked all 20 episodes, selected the fallback in 14,
found 86 initial geometry pairs, and verified zero pairs after every fallback.
Mean synchronized reset-check cost was 3.707 ms per episode.

Success improved from 1/20 to 5/20 with no regressed successful episodes;
force aborts fell from 12/20 to 8/20 and successful throughput rose from 17.80
to 97.00 parcels/hour. Nevertheless, 25% success and 40% force-abort rates are
far outside the 90% and 5% release gates. The feature remains disabled and is
classified as a useful diagnostic/negative control, not a deployable
optimization. Local hashes are in
`expert/radeon-collision-checked-reset-ab-v1-SHA256SUMS`; the two remote
manifests preserve full and compact provenance.

## Surface-aware pregrasp elimination probes

`expert/radeon-surface-aware-pregrasp-probes-v1-*` records a sequential Radeon
elimination study, not a formal success-rate experiment. Prior trajectories
showed seven high-carton timeouts ending only 40--50 mm above the nominal grasp
centre with XY already aligned. The candidate replaced the spherical capture
window with an opt-in band that required 15 mm XY alignment, at least 20 mm of
vertical side overlap, and at most 55 mm positive vertical error.

Version 1 applied the band to every non-flat box. Its first preservation probe
regressed successful episode `7000005` from 17.12 N and completion to a 56.50 N
force abort after moving the transition by about one control frame. Version 2
restricted the band to cartons at least 150 mm high. It restored `7000005`
exactly, but converted target timeout `7000000` from a low-force failure into a
66.22 N force abort after two retries. The third probe and formal 20+20 A/B were
therefore cancelled by the preregistered safety rule.

The implementation and unused fixed runner remain disabled as a reproducible
negative control. These probes show that an expanded completion predicate
cannot substitute for an IK- and collision-feasible grasp pose. Local hashes
are in `expert/radeon-surface-aware-pregrasp-probes-v1-SHA256SUMS`; remote
manifests preserve the three complete source summaries and derived compact
artifacts.

## Geometry-aware grasp-planning result

`expert/radeon-geometry-aware-grasp-planning-ab-v2-tiered-*` contains compact
summaries, trace-derived failure analyses, both run logs, the exact comparison,
and local/remote SHA-256 manifests for a fixed 20+20 single-Radeon A/B. The
candidate changed only `task.geometry_aware_grasp_planning_enabled` relative to
the collision-checked reset baseline.

Success improved from 5/20 to 15/20, force aborts fell from 8/20 to 4/20, no
success regressed, and drops remained zero. Successful throughput increased
from 98.25 to 359.36 parcels/hour, while maximum force fell from 111.30 N to
46.99 N. The candidate remains experimental because it missed the 90% success
and 5% force-abort gates.

`expert/radeon-geometry-aware-grasp-planning-v2-probe-ledger.json` records the
ordered preservation, swept-gate, step-size, and cross-sentinel decisions. Full
trace summaries remain in the Radeon workspace; their hashes are in the remote
manifest.

## Reset-fallback risk-gate validation

`expert/radeon-reset-fallback-gate-validation-v1/` archives a frozen 60+60
matched, multi-profile Radeon validation. Collision-checked reset achieved
35/60 successes and 17/60 force aborts; the gated planner achieved 33/60 and
19/60, with zero drops in both groups. Mean episode peak force increased by
6.67 N (paired bootstrap 95% interval -0.53 to +16.85 N), and successful
throughput fell to 0.910x.

The attribution audit found five planner-active episodes, one recovery, two
regressions, and zero episodes in which the new gate avoided planning beyond
the existing geometry rule. One further regression occurred with zero planner
attempts and state divergence preceding decision divergence. The candidate is
rejected and remains disabled. See `RESULTS.md` in the evidence directory for
the complete interpretation and artifact map.

## Reset-gate execution repeatability

`expert/radeon-reset-gate-repeatability-v1/` contains a seeded blocked study of
the four validation-discordant episodes, with five nested executions per
episode and condition. The three planner-active discordances repeated exactly:
one recovery and two regressions. The planner-inactive episode succeeded 2/5
under both conditions, and all four successes occurred when the condition ran
second in its block. This identifies a process-local order/carry-over effect
rather than an inactive-planner effect.

The 40 executions are technical repeats of four experimental units, not 40
independent task samples. Exact schedules, event records, position summaries,
source-summary hashes, and bilingual interpretation are retained in the
directory.
