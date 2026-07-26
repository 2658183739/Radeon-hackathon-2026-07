# Groupwise Safety-First Grasp Ranker

## Motivation

The existing 6,276-parameter MLP predicts four labels independently for every
candidate. Its pointwise objective does not directly express the deployed
decision: choose one candidate from the statically feasible candidates for the
same parcel. V2 therefore adds a groupwise training objective while retaining
the identical feature schema, network, parameter count, inference API, and
lexicographic runtime rank key. This isolates the effect of the objective from
model capacity.

## Frozen ordering semantics

Candidates are grouped by `(profile, episode)`. Every group contributes equal
weight even when the number of feasible candidates differs. The objective has
four calibrated pointwise terms and two within-group pairwise terms:

1. safe candidates must score below force-aborted candidates on the unsafe
   logit;
2. successful candidates must score above failed candidates, but only among
   safe candidates;
3. unsafe probability, success probability, log peak force, and log duration
   retain their calibrated losses.

Safety pairs have weight 2.0 and safe-success pairs weight 1.0. Success is
never allowed to compensate for a safety abort. Runtime selection still uses
the independent hard IK/collision gates followed by unsafe probability,
success probability, predicted force, duration, and static rank.

## Implementation and verification

`grouped_grasp_row_indices()` creates stable episode groups.
`groupwise_grasp_preference_pairs()` builds only within-group preferences.
`train_grasp_scorer_rocm.py --objective groupwise-safety-first` applies
group-balanced calibration and pairwise logistic losses. The default
`pointwise` objective remains unchanged for the baseline.

A five-step Radeon smoke used two completed v2 train groups (12 rows). It ran
on `AMD Radeon Graphics` with HIP 7.2 in 1.39 seconds and produced a valid
checkpoint. Its in-sample selection avoided two baseline safety aborts and
recovered one success. This result verifies wiring only: two observed groups,
five steps, and in-sample evaluation cannot support a generalization claim or
model selection.

## Evaluation boundary

The exact pointwise and groupwise hyperparameters must be frozen before the
development split is executed. Both methods train on the same complete train
dataset and fixed seed. Development selects at most one scorer using the
preregistered safety, task, per-profile, and Radeon latency gates. Holdout
remains unavailable until that selection is frozen.
