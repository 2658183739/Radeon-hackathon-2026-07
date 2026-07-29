# PI0.5 B3-SW and B3-SWM evidence

This directory freezes the compact evidence available before the B3-SWM
12,000-step run. Large training logs, checkpoints, and raw ROCm telemetry stay
under `/workspace/persistence/parcel-sorter-opt-v1`; their hashes are recorded
in `REMOTE_RAW_SHA256SUMS.txt`.

## Current result

- B0 (generic PI0.5 base, parcel fine-tuned) passed the six-observation offline
  screen at 12k. The earliest selected B0 checkpoint was 3k, and its strict
  pure-VLA development gate was 0/3. It is not a successful parcel policy.
- B2 (PI0.5 DROID initialization plus full action I/O projections) routed 6/6
  observations and had 17 action-fidelity errors at 12k.
- B3-SW routed 6/6 and reduced the 12k action-fidelity error count to 14. Its
  paired endpoint improved on 4/6 observations and regressed on both
  cooperative-cradle observations. The exact bootstrap lower bound was below
  zero, so the checkpoint was not promoted and no strict rollout was run.
- B3-SWM adds only population-normalized target grasp-mode weighting to the
  continuous flow loss. The two-step ROCm smoke and full static checkpoint
  audit passed. No B3-SWM action-fidelity or closed-loop result exists yet.

`RESULTS.json` provides the machine-readable claim summary. The copied JSON
artifacts preserve the B0/B2 controls, B3-SW selection, and the B3-SWM smoke
contract, audit, and ROCm summaries.

## Claim boundary

Offline action fidelity is not parcel success. B3-SWM has not yet completed
training, screening, or strict pure-VLA development. Nothing in this directory
supports superiority to PI0.5, PI0.6, or any public leaderboard entry.
