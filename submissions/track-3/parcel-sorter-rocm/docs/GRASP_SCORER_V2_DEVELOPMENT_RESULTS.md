# Grasp Scorer V2: Development Promotion Result

## Decision

The one-shot v2 development result is `no_promotion`. Neither pointwise nor
groupwise-safety-first passed the preregistered gate, no model was selected,
and holdout was not opened. Runtime selection remains the static geometry
baseline. V2 development cannot be reused for tuning or another selection.

All 16 development groups and 96 closed-loop candidate executions completed,
with four groups per profile and zero collection failures. Independent checks
verified unchanged frozen checkpoint hashes before evaluation and verified the
decision, dataset, and both evaluation hashes afterward.

## Gate Results

| Method | Successes | Safety aborts | Mean peak force | Six-candidate warm P95 | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| Static geometry baseline | 9/16 | 4/16 | 36.10 N | N/A | Current default |
| Pointwise | 6/16 | 9/16 | 134.95 N | 0.909 ms | Reject |
| Groupwise safety-first | 7/16 | 8/16 | 125.88 N | 0.924 ms | Reject |

Both models met the 5 ms latency gate, but both regressed safety aborts in all
four profiles and produced neither aggregate task nor safety improvement.
Latency cannot compensate for task and safety failure.

## Failure Attribution

The 192 train rows represent only 32 independent physical groups, while each
network has 6,276 parameters. Both objectives drove train loss nearly to zero.
On development, pointwise departed from the static first choice in 13/16
groups and groupwise in 12/16, often selecting high static-rank candidates.
Actual peak force among their aborted selections averaged 222.15 N and 229.79
N, while predicted means were only 21.53 N and 26.69 N.

The worst `medium_carton:8410034` candidate reached 1,489.78 N. Groupwise
predicted 23.74 N and unsafe probability 0.000155. Only 14 of 96 development
rows used a globally unseen candidate ID, and each model selected only two of
them. The failure is therefore not explained by unseen discrete IDs alone. It
is more consistent with too few physical groups, discontinuous contact-force
spikes, and static features that do not support calibrated dynamic-risk
prediction.

## Candidate-Set Headroom

A posthoc oracle is diagnostic only, not deployable: 15/16 groups contained a
safe candidate, 13 contained a safe successful candidate, and only one was
entirely unsafe. A safety-first oracle upper bound is 13/16 successes and 1/16
safety abort, compared with the static baseline's 9/4. Candidate generation
still has useful headroom; the rejected component is the v2 learned ranker,
not the arm or candidate set.

## Next Research Boundary

V2 is closed. Thresholds, losses, or another model cannot be selected on the
same development split. Any v3 ranker requires a fully disjoint
train/development/holdout population frozen before new physics. Capacity and
calibration should be chosen by train-only cross-validation, with uncertainty
or OOD abstention and fallback to the static baseline. Relative geometry
features and short dynamic contact probes are new hypotheses that require the
new population.

See `evidence/training/grasp-scorer-v2-development-evidence.json` for the
machine-readable record.
