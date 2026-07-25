# Open-Source Parcel Gripper Adapter

## Scope

This development milestone tests one physical hypothesis: the stock Panda
fingertips do not provide enough support length for some tall cartons during a
full feedback-controlled transfer. It changes support geometry instead of
tuning another score, force threshold, or controller gain.

The adapter is **default off**. It does not change the 35 N measured-force
abort, grasp rank, transport controller, or retry policy. No holdout episode
was opened.

## Design and provenance

At runtime, `build_parcel_gripper_mjcf` parses the Panda MJCF distributed with
the locked Genesis 1.2.3 source tree. It writes a generated MJCF that points to
the upstream mesh directory and adds one box collision geom and one cyan visual
geom to each finger. No third-party mesh is copied into this repository.

The frozen adapter extends each stock fingertip by 30 mm. Each half-size is
`10 x 4 x 15 mm`; its local center is `(0, 5.5, 68) mm`, so it begins at the
stock pad end at local `z=53 mm` and ends at `z=83 mm`. The accepted upstream
source is the Genesis 1.2.3 Apache-2.0 Panda MJCF.

The live Radeon geometry probe found six stock collision geoms and seven
adapter collision geoms per finger. The finger world-AABB long span increased
from approximately 56 mm to 85 mm. The generated XML contains four named
adapter geoms: one collision and one non-colliding visual geom per finger.

## Reproduction

Run from the project root on the supplied Radeon instance:

```bash
export PYTHONPATH="$PWD/src"
python scripts/probe_gripper_adapter_geometry.py \
  --backend rocm \
  --profile large_narrow_carton \
  --episode 4120001 \
  --extension-m 0.030 \
  --output outputs/gripper-adapter-development-v1/geometry-probe.json
```

Reproduce the observed mechanism pair without changing the controller:

```bash
python scripts/diagnose_counterfactual_grasp_candidates.py \
  --config configs/catalog_v2.toml \
  --profile medium_carton \
  --episode 4120001 \
  --backend rocm \
  --candidate-id canonical-long-+0.000-up-0.040 \
  --contact-wrench-telemetry \
  --contact-wrench-backend cpu \
  --parcel-gripper-adapter \
  --parcel-gripper-extension-m 0.030 \
  --output outputs/gripper-adapter-development-v1/4120001-canonical-40-adapter.json
```

The CPU option above applies only to the tiny read-only diagnostic score.
Genesis simulation, contact solving, and the closed-loop task execute on the
single Radeon through ROCm.

## Development evidence

| Frozen comparison | Stock | 30 mm adapter |
|---|---:|---:|
| `4120001`, centered `+40 mm` | missed bin, 21.81 N | completed, 24.07 N |
| `4120001`, centered `+45 mm` sentinel | completed, 10.31 N | completed, 12.55 N |
| `7130001`, six frozen train candidates | 3/6 completed | 5/6 completed |
| `7130001`, safety aborts | 2/6 | 1/6 |

Across the eight paired candidate executions, all four stock successes were
preserved and three stock failures were recovered. The remaining candidate
crossed the unchanged safety line and aborted at 36.95 N. The highest force
among adapter successes was 32.69 N. No adapter rollout dropped the parcel.

These are eight candidate executions from only two deterministic episodes,
not eight independent parcel samples and not a success-rate estimate. The
result supports retaining the adapter as a development candidate, not enabling
it by default or making a generalization claim.

## Decision boundary

- Freeze the extension at 30 mm; do not scan lengths on these observations.
- Keep the adapter default off until a separately frozen evaluation passes.
- Keep the 35 N gate independent of the adapter and any learned model.
- Do not open the existing scorer holdout to justify this geometry.
- Treat the generated MJCF and source hashes as part of every evidence record.

The current simulation keeps the stock explicit finger inertial parameters.
It therefore represents a lightweight adapter but does not yet model a
specific printed material, fastener, added mass, or compliance. Hardware
transfer requires CAD, material/mass identification, combined inertia,
collision-clearance review, and real force calibration before deployment.
