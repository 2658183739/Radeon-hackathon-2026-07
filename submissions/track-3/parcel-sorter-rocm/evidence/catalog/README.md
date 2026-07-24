# Catalog Evidence

`catalog-v1-submit-smoke.json` is copied from the final 20-second catalog
smoke on the verified Radeon instance after the local `configs/catalog_v1.toml`
was synchronized.

| Field | Value |
| --- | --- |
| Command | `python scripts/evaluate_catalog.py --backend rocm --episodes-per-profile 1` |
| GPU | AMD Radeon Graphics, `gfx1100` |
| VRAM | 47.98 GiB |
| ROCm | 7.2.1 / HIP runtime |
| Genesis | 1.2.3, `gs.amdgpu` |
| Config | `configs/catalog_v1.toml`, 20 s episodes |
| SHA-256 | `7b69a332faea59f6e930acfec653ec118f858c6002cd9d78d20a06bd8f142be0` |

The file contains one deterministic episode for each of the seven training
profiles. It is a regression smoke, not a statistically valid success-rate
claim. Four box profiles completed; the micro box and two cylinder profiles
remain explicit hard cases.

## Catalog v2 optimization evidence

All files below were produced on the same `gfx1100`, 47.98 GiB Radeon with
ROCm 7.2.1, PyTorch 2.9.1 ROCm, and Genesis 1.2.3. Each candidate is a
deterministic regression smoke, not a success-rate estimate.

| Artifact | Purpose / result | SHA-256 |
| --- | --- | --- |
| `catalog-v2-baseline.json` | One episode for each of 12 profiles; 8 completed | `760b09e0a38ed38ebf37dcadb91d59e5d5999d129b943d7f947c3dfe562a810f` |
| `catalog-v2-height-aware.json` | Rejected tall-parcel height candidate | `938514705e7b0815b18115bc0a97ebe5068aa80f76dfec09cc3434c11d713704` |
| `catalog-v2-seated-grasp.json` | Rejected post-close seating candidate | `829415c920c09284f2a1a536dc0c9bb3ed687e89249bc82abfccbcf9fbf92fa0` |
| `catalog-v2-rolling-friction.json` | Tube rolling friction 0.002; 18.3 mm drift, 79.27 N abort | `7d17cb091222c7b4411502d5a0f73f96996be48d9340bbd23ac839256a293a8a` |
| `catalog-v2-tube-slow-approach.json` | Rejected 2.5 mm approach; 36.74 N abort | `1ff4140e65925d3acb5108f42b8a696913d9d5b95bb0f2c4764cae6bfd318258` |
| `catalog-v2-tube-step-2mm.json` | Rejected 2.0 mm approach; 98.83 N abort | `51ab8c36fdb7f964b9c6922e1ee107cb58882d2c7d6ed3ce895409ac371898cb` |
| `catalog-v2-tube-tight-xy.json` | Rejected 5 mm XY tolerance; zero force but approach timeout | `4644c637e6cb5e3f7c384d39738f42d2d2f8c69ebf28efc30056205122fc7254` |
| `catalog-v2-tube-friction-005.json` | Rolling friction 0.005; 3.3 mm drift, 73.99 N abort | `37f99b8f1d0fefef7630453909d64fc172821c58b593cee42d4d9962b4027e99` |
| `catalog-v2-rolling-final.json` | Rejected global solver flags; catalog regressed from 8/12 to 6/12 | `ae691128f2bc2a66e6e02096757f72d00583691c7c6b062ce74fe94faa31a26a` |
| `catalog-v2-rolling-scoped.json` | Solver flags scoped to rolling-prone tubes; catalog restored to 8/12 | `f0ecdc95781825653ad3395b600e476c19daa28712420808e20bb1cf94b7d9f8` |

The retained code enables Genesis torsional and rolling friction and passes a
profile-level rolling coefficient into the parcel material. The experimental
profile-specific control overrides were removed after they failed acceptance.
The mailing tube remains an explicit limitation; the next design candidate is
a low staging cradle or a cylinder-capable end effector.

The full-catalog pair is the regression gate: the global solver configuration
was rejected, while the scoped implementation restored every non-tube profile
to its baseline outcome. Neither 8/12 value is a formal success rate.
