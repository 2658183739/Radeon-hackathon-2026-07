# Parcel Gripper Adapter Mass and Inertia

## Question and boundary

The first 30 mm adapter study retained the stock Panda finger inertia. This
follow-up asks whether the same geometry remains useful after modeling a
finite adapter mass, shifted center of mass, and full inertia tensor. It is a
physical-fidelity gate, not a density or geometry search.

The adapter remains default off. Extension is frozen at 30 mm, effective
density is fixed at 1240 kg/m3, and the measured-force abort remains 35 N.
Only the already observed `4120001 medium_carton` mechanism pair is used. No
scorer holdout, new episode, or `7130001` expansion is opened.

## Implementation

Each generated adapter box is `20 x 8 x 30 mm`, giving a volume of
`4.8e-6 m3` and a mass of `5.952 g` at the fixed effective density. Each
finger therefore changes from `15.000 g` to `20.952 g`.

`combine_rigid_body_with_box_inertia` computes the uniform-box inertia at its
own center and applies the parallel-axis theorem to both the stock finger and
adapter around the combined center of mass. The MJCF generator replaces the
stock `diaginertia` with an explicit six-component `fullinertia`:

```text
mass = 0.020952 kg
center = (0, 0.00156242840779, 0.0193172966781) m
fullinertia =
  2.26856869553e-05  2.27234426117e-05  1.10904434364e-06
  0                   0                  -1.59367697595e-06 kg m2
```

The generated filename includes both frozen physical parameters:
`panda_parcel_adapter_30p0mm_1240kgm3.xml`. Configuration validates an
effective-density range of 100--2500 kg/m3, but no density scan was performed.
Production, diagnostic, and geometry-probe CLIs expose the value explicitly.
Telemetry distinguishes `stock_explicit_inertia` from
`combined_rigid_body` and reports added mass per finger.

## Radeon validation

The live Genesis 1.2.3 scene accepted the full inertia tensor on one Radeon
`gfx1100` through ROCm 7.2. The geometry contract remained unchanged: each
finger had seven collision geoms instead of six, the AABB long span increased
from about 56 mm to 85 mm, and the generated XML contained four adapter geoms.
The generated MJCF SHA-256 is
`c1785752199e90c2631c3bff46eb6733545d35f707819686dec590c236e95e32`.
The synchronized source compiled and the complete remote suite passed all 259
tests.

The preregistered elimination order was the known failed `+40 mm` mechanism
grasp followed by the known successful `+45 mm` sentinel:

| Candidate | Lightweight adapter | Mass-aware adapter | Gate |
|---|---:|---:|---|
| `+40 mm` mechanism grasp | completed, 24.07 N | completed, 13.14 N | passed |
| `+45 mm` success sentinel | completed, 12.55 N | aborted, 38.34 N | failed |

The sentinel regression repeated exactly: both mass-aware runs crossed the
35 N line at frame 204 with a 38.3364 N peak. At frame 202 the measured force
was still 5.06 N. At frame 203, contact count changed from 8 to 19, bilateral
support was lost, and the contact diagnostic reported a 38.34 N peak. This is
a deterministic contact-dynamics branch change in the tested simulator, not
evidence that the added mass directly produces 38 N.

## Decision

The mass/inertia implementation is retained as a reproducible, default-off
physical-model capability. The mass-aware adapter is rejected for promotion:
it preserves the original recovery mechanism but regresses a success sentinel
into a safety abort. The stop rule cancels the planned `7130001` group and any
new paired campaign. The result must not be described as a robustness or
success-rate experiment.

The next admissible step is an independently specified contact-model
investigation, such as checking finger-actuator dynamics and collision-pair
identity around frames 202--204. It must not tune extension or density against
this observed sentinel. Compliance, fasteners, and hardware force calibration
remain outside the current model.

## Reproduction

Run on the supplied Radeon instance from the project root:

```bash
export PYTHONPATH="$PWD/src"
python scripts/probe_gripper_adapter_geometry.py \
  --backend rocm \
  --profile large_narrow_carton \
  --episode 4120001 \
  --extension-m 0.030 \
  --density-kg-m3 1240 \
  --output outputs/gripper-adapter-inertia-development-v2/geometry-probe.json

python scripts/diagnose_counterfactual_grasp_candidates.py \
  --config configs/catalog_v2.toml \
  --profile medium_carton \
  --episode 4120001 \
  --backend rocm \
  --candidate-id canonical-long-+0.000-up-0.045 \
  --contact-wrench-telemetry \
  --contact-wrench-backend cpu \
  --parcel-gripper-adapter \
  --parcel-gripper-extension-m 0.030 \
  --parcel-gripper-density-kg-m3 1240 \
  --output outputs/gripper-adapter-inertia-development-v2/4120001-canonical-45-adapter-mass-aware.json
```

The CPU selection applies only to the small read-only diagnostic score.
Genesis simulation, contact solving, and the closed-loop task execute on the
single Radeon through ROCm.
