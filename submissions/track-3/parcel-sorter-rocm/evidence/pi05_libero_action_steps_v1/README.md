# PI0.5 LIBERO action-step evidence

This directory contains the small, machine-readable artifacts for the frozen
400+400 development comparison and the one-shot 400-unit confirmation. Raw
evaluator output and ROCm telemetry remain under
`/workspace/persistence/parcel-sorter-opt-v1`.

- `DEVELOPMENT_CONTRACT.json`: SHA-256
  `c0d2f8345500c8993f7b533a56c7221efbda20e8313c3b09c6053016a2c25dd2`
- `DEVELOPMENT_SUMMARY.json`: SHA-256
  `7be890f17ace3d66635a9381de5f3886b2e5254e22a115727c42c3a7c9f6846f`
- `CONFIRMATION_CONTRACT.json`: SHA-256
  `97e84a7d70e700e02abd2cc0ca9f339d1247887102b9bba7b97eea42afc1c195`
- `CONFIRMATION_SUMMARY.json`: SHA-256
  `1ee5f1014083600a32c417a076a1bc98bbed554f6119fc6db5c11052620db4a6`
- `CANDIDATE_RUN_SUMMARY.json`: SHA-256
  `935e60891e7fec3c5e91b03a7735102b4c11c3e9c7d351e2ca66e28606698ec6`
- `B3_SW_V1_DECISION.json`: SHA-256
  `27cba544de81740fe1d3bba53cf69447c3cf5b5e24fe8f709feec33adc3bc3f9`

The eight-action candidate scored 385/400 and the ten-action control scored
384/400. This is model-selection development evidence only. The paired
Newcombe 95% interval includes zero and the exact one-sided McNemar p-value is
0.5, so these artifacts do not support a statistical-superiority claim or a
confirmation score.

On the untouched confirmation population, the eight-action candidate scored
386/400 (96.50%, Wilson 95% CI 94.21--97.90%) and the local ten-action PI0.5
control scored 385/400 (96.25%). The paired outcomes were 12 wins, 11 losses,
and 377 ties: +0.25 percentage points with a Newcombe 95% interval of
[-2.24, 2.76] points and exact one-sided McNemar p=0.5. The candidate is
numerically higher on this frozen run, but the evidence does not establish
statistical superiority and does not permit a PI0.6 comparison.

`B3_SW_V1_DECISION.json` preserves the automatic handoff failure that occurred
after confirmation. No B3-SW model or training result is represented by that
file.
