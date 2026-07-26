# Geometry-Eligible Grasp Candidate Learning V2 Protocol

## Motivation

V1 tied label generation to an observed collision-reset fallback. Only four of
12 training groups and one of six development groups generated labels, and the
single development group had no safe candidate. V2 changes the population,
not the observed labels: it studies every stock-hand parcel already inside the
frozen geometry-planning scope. Collision-checked reset remains enabled as a
safety mechanism but no longer decides whether candidate labels are produced.

## Episode selection before physics

Four parallel-jaw box profiles are included: `medium_carton`,
`shoe_box_proxy`, `large_narrow_carton`, and `near_limit_box`. Their untouched
episode namespaces start at `8410000`, `8510000`, `8710000`, and `8810000`.
For each profile, inspect at most 256 deterministic randomizer outputs in
ascending ID order and select the first 16 satisfying the existing method
predicate:

```text
shape == box and height >= 0.105 m palm clearance + 0.020 m side overlap
```

This step reads only randomized parcel parameters. It must not build a Genesis
scene, query collision, execute an action, or read a task outcome. The first
eight selected IDs per profile are train, the next four development, and the
last four holdout. The selector emits a hash-bound audit before the exact IDs
are copied into the frozen TOML protocol.

## Frozen collection

- Robot: stock Genesis 1.2.3 Panda hand; no generated adapter.
- Platform: one Radeon `gfx1100`, ROCm 7.2, Genesis physics at 240 Hz.
- Controller: production expert, collision-checked reset, monotonic transport
  contract, no retries, unchanged 35 N abort.
- Planning activation: every sample inside the existing geometry predicate.
- Intervention: force exactly one of up to six statically feasible candidate
  IDs in a fresh scene.
- Budget: 32 train groups, 16 development groups, 16 locked holdout groups;
  at most 384 controller-faithful rollouts.

Train must complete before development. Model selection may use only train and
development. Holdout remains locked until exactly one scorer and all
hyperparameters are frozen. An inactive geometry output is an auditable
selection failure, not a silent omission; at least 15 of 16 development groups
must produce complete labels before model selection is considered valid.

## Model and promotion boundary

Static rank remains the baseline. V2 will compare at least an unchanged 6,276
parameter MLP and one groupwise safety-first ranker using the same versioned
features. Hard IK, collision feasibility, and the 35 N supervisor remain
outside every learned model.

Before opening holdout, the selected scorer must reduce development safety
aborts or recover task successes versus static rank, show no per-profile safety
regression, and keep six-candidate warm P95 below 5 ms on Radeon. Holdout is
executed once. ACT, Diffusion, VLA, vision embeddings, and ROS 2 remain outside
this experiment until structured ranking demonstrates held-out value.

## Later paper evaluation

Candidate-label rollouts are not the final success-rate sample. If the holdout
gate passes, the integrated method proceeds to a separately preregistered
200--500 episode comparison across ordinary boxes, difficult boxes, cylinders,
and geometry-out-of-scope boundary profiles, with paired task, safety,
latency, and profile-stratified statistics.
