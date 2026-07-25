# Reset-Fallback Gate Validation Results

## Scope

This development-validation campaign compared collision-checked reset with
reset-fallback-risk-gated geometry planning on one AMD Radeon GPU through
ROCm. It used 12 supported parcel profiles and five matched episodes per
profile, for 60 episodes per group and 120 closed-loop episodes total. The
35 N force boundary, randomized samples, profile blocks, and local episode
IDs `120000`--`120004` were frozen before execution. The reserved
confirmatory IDs `200000`--`200039` were not inspected.

## Overall result

| Metric | Collision-checked reset | Risk-gated planner | Candidate change |
| --- | ---: | ---: | ---: |
| Success | 35/60 (58.3%) | 33/60 (55.0%) | -2 episodes |
| Force abort | 17/60 (28.3%) | 19/60 (31.7%) | +2 episodes |
| Drop | 0/60 | 0/60 | 0 |
| Mean episode peak force | 22.87 N | 29.54 N | +6.67 N |
| P95 episode peak force | 51.21 N | 69.00 N | +17.78 N |
| Maximum episode peak force | 104.73 N | 233.75 N | +129.02 N |
| Successful throughput | 307.42/hour | 279.88/hour | 0.910x |

The exact paired McNemar p-value was 0.625 for both success and force-abort
outcomes. The paired mean peak-force change was +6.67 N, with a deterministic
10,000-sample bootstrap 95% interval of [-0.53, +16.85] N and a paired
sign-flip p-value of 0.163. These intervals do not establish a population
effect, but the observed direction fails the development acceptance rule and
provides no reason to expose the reserved confirmation set.

## Gate and attribution audit

The candidate reported 17 reset-fallback episodes, five geometry-eligible
episodes, five planner-active episodes, and zero gate-avoided episodes. All
five geometry-eligible episodes also satisfied the reset-fallback gate, so the
new gate saved no planning work beyond the existing geometry eligibility
rule. Five planning attempts consumed 31,965.11 ms, or 6,393.02 ms per attempt.

Within the five planner-active episodes, the baseline achieved 3/5 successes
and the candidate achieved 2/5. The candidate recovered `5120003`, regressed
`4120001` and `7120004`, and increased mean peak force in this subset by
42.55 N. This subset is descriptive and too small for a general claim.

One additional regression, `5120000`, occurred while the planner was inactive
and recorded zero planning attempts. Its continuous state first diverged at
frame 104, while the high-level decision first diverged at frame 121. It is
therefore classified as an execution-nondeterminism candidate, not a planner
effect. This classification is conservative: repeated executions are still
required to measure the simulator/GPU variance directly.

## Engineering decision

Reject reset-fallback-risk-gated planning as the next confirmatory method and
keep it disabled by default. It reduced neither planning work nor aggregate
safety risk in this validation, and its planner-active subset contained more
regressions than recoveries. Do not tune the 35 N boundary and do not inspect
the reserved confirmation episodes to rescue the hypothesis.

The useful deliverable is a reproducible negative result: the gate mechanism,
matched campaign, causal-attribution audit, and execution-divergence evidence
show why a strong single-profile result did not generalize across parcel
profiles. The next experiment should quantify same-condition execution
repeats before another controller intervention is selected.

## Reproduction and integrity

The campaign is reproduced with:

```bash
bash scripts/run_reset_fallback_gate_campaign_rocm.sh
```

`paper-evaluation.json` contains the Wilson intervals, exact McNemar tests,
paired bootstrap intervals, sign-flip tests, and profile strata.
`gate-attribution-audit.json` separates planner-active and planner-inactive
outcome changes. `COMPACT-SHA256SUMS` was verified locally and on the Radeon
host. `REMOTE-SUMMARY-SHA256SUMS` preserves the hashes of the two 20+ MB
trace-rich source summaries retained in the Radeon workspace.
