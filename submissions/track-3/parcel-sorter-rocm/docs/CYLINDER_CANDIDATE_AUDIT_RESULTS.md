# Cylinder Candidate Population V1 Audit Result

## Result

Commit `4788d21` froze 128 samples, planner parameters, analytic tolerances,
and four implementation hashes before the formal audit ran. The result is
`candidate_population_valid`: 128/128 samples passed with `errors=[]`.

This establishes that both current parallel-jaw cylinder profiles generate
finite, unique, axis-consistent analytic candidates. It contains no IK,
collision, physics step, or task outcome. It therefore authorizes static ROCm
IK/collision screening only, not closed-loop success, runtime activation, or a
positive paper claim.

## Population

| Profile | Samples | Observed size range | Candidates/sample | Minimum aperture margin | Maximum axis error |
| --- | ---: | --- | ---: | ---: | ---: |
| `upright_canister` | 64 | diameter 40.66–69.71 mm, height 60.43–158.12 mm | 16 | 10.29 mm | 0 |
| `mailing_tube` | 64 | length 160.38–299.60 mm, diameter 35.24–64.94 mm | 18 | 15.06 mm | `4.44e-16` |

The largest absolute approach/axis dot product for horizontal candidates is
`2.74e-16`, and the maximum quaternion-norm error is zero. The horizontal
rolling-risk index is at most 0.2; this is a fixed ranking heuristic, not a
failure probability.

## Causal boundary

The audit records no outcome fields, scene construction, robot action, or
physics step. Upright episodes start at `10100000` and horizontal episodes at
`10200000`, with 64 deterministic samples in each namespace. Selection depends
only on the frozen catalog and `DomainRandomizer`.

## Hashes

```text
protocol:
57404ae62ce0b9094bf600a84eeb007e0ae480452b6d1eab4a7452c4f3ac410a
population:
1aeaf2993f64d0a3b6dd970e93f0fa1f622e3b043984e80020f8f2df9b5cfcf5
result file:
1c19e5a0f5d35b1d2f8a234053057af40f5049ab96e23607b64f20fea16adf2c
```

The complete 136,094-byte artifact is
`evidence/planning/cylinder-candidate-audit-v1.json`.

## Reproduction

```bash
cd /workspace/parcel-sorter-opt-v1
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/audit_cylinder_candidate_population.py \
  --protocol configs/cylinder_candidate_audit_v1.toml \
  --output outputs/cylinder-candidate-audit-v1/result.json
```

The next frozen screen must quantify the gap between candidate existence and
robot IK/collision feasibility. A weak profile must trigger candidate redesign
on a new development population, not reinterpretation of this analytic result.
