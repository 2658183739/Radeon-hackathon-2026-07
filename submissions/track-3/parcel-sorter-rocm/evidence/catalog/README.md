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

## 2026-07-25 centered-grasp evidence

The sequence below continues from the scoped rolling-physics comparator. Every
single-tube file is one fixed diagnostic episode, not a success-rate estimate.
The two regression files cover one fixed episode for each of twelve profiles.

| Artifact | Decision / observed result | SHA-256 |
| --- | --- | --- |
| `catalog-v2-tube-geometry-fix.json` | Canonical cylinder geometry; 72.92 N abort | `72bbfb7c134cee44eeef844c7eceef501fe68f567d306cae4d8ed817b732e13d` |
| `catalog-v2-tube-geometry-xy005.json` | Rejected 5 mm XY gate; zero force, approach timeout | `b33c729900b7c75c93bcd6cb18003c610768c9219c446341889f0e9a73732907` |
| `catalog-v2-tube-geometry-xy010.json` | Rejected 10 mm XY-only candidate; 63.77 N | `2040561aee1cc71a148235d1b9f68191ab194e3472d79c39e6500f91d121c20c` |
| `catalog-v2-tube-geometry-xy010-step0025.json` | Rejected combined candidate; 143.33 N | `032649742823ada893a1e4d88484e284c53ad9748e198270ed7ece1dfd61af9d` |
| `catalog-v2-tube-rails-prototype.json` | Rejected dual-rail prototype; no improvement, 72.92 N | `47973f22b4ccedc3e35887e385b89307a1329f2f6d41059752475f46b916efd8` |
| `catalog-v2-tube-axis-aligned.json` | Kept axis-aligned gripper direction; improved to 43.54 N | `23009ac98a15447059756857c8035f4c095b3cfd67ae0d1c8e74a905c7031459` |
| `catalog-v2-tube-axis-step005.json` | Kept 5 mm final approach; 34.26 N, then lost grasp | `07671138052ed0760d11de62c0cafd83c4cad1a14e49b9d80053f52ad454be16` |
| `catalog-v2-tube-stable-contact.json` | Three stable frames reached lift; recovery aborted at 48.05 N | `f0c10d4f919f4c3219e15c8299c4648c8bdd9e09bc24f2cdd6620c36b3a6d969` |
| `catalog-v2-tube-lift-step010.json` | Kept 10 mm lift request; contact lasted longer, recovery 35.12 N | `87cb904706bbaa8d2c4f9719689b3755efb503352cb89955fab64470da64b979` |
| `catalog-v2-tube-pad-friction200.json` | Kept friction-pad model; peak 15.62 N, three lift attempts | `17f31300b072fe34577d32a7bc94b8522f509450c6096273f850ffd774824de0` |
| `catalog-v2-tube-centered-grasp.json` | Kept 10 mm close tolerance; first true lift to 66.4 mm center height | `d406edbaf642b355874e3d3bbb01838dcbd4d0e2526512db8e5677122444a462` |
| `catalog-v2-tube-force025.json` | Rejected 25 N close force; 69.2 mm, 36.46 N safety violation | `808ce89fec19993756ee1aa33a23ac81bcebc70b3d1d365c674d76165dcb8a8c` |
| `catalog-v2-tube-force035.json` | Rejected 35 N close force; 69.9 mm, 35.19 N safety violation | `7ec0738ccc77369f656127d8ec175abe243fafd499bddb0aa76e79d01486d96f` |
| `catalog-v2-centered-regression.json` | Rejected global three-frame stability; catalog regressed to 5/12 | `73a33b088c2e8ea524700f1076afa1985c1255645c1b40e8a0a60ccd7f0bea00` |
| `catalog-v2-tube-scoped-regression.json` | Kept profile-scoped stability; exact baseline outcome restored to 8/12 | `1e99926b5a9d481349d84758d463902158ee5d264c53cba79245a1154dd83605` |

The retained implementation fixes cylinder construction, aligns the grasp to
the tube axis, uses tube-specific approach/lift/tolerance/stability values, and
models higher-friction finger pads. It does not claim mailing-tube task success:
the best retained diagnostic lifted the object but did not transfer and place
it. The next accepted change requires a structural gripper/fixture candidate
and repeated held-out evaluation.
