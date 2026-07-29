import json
import tempfile
import unittest
from pathlib import Path

from parcel_sorter.mobile_pi05_contract import (
    MOBILE_PI05_ABSOLUTE_ACTION_NAMES,
    MOBILE_PI05_ABSOLUTE_STATE_NAMES,
    MOBILE_PI05_INCREMENTAL_ACTION_NAMES,
    MOBILE_PI05_RESIDUAL_ACTION_NAMES,
    MOBILE_PI05_STATE_NAMES,
)
from parcel_sorter.mobile_dataset import mobile_policy_visual_keys
from parcel_sorter.mobile_pi05_training_contract import (
    build_pi05_training_contract,
    validate_pi05_training_contract,
    with_pi05_architecture_protocols,
)
from parcel_sorter.pi05_weighted_loss import PI05_STAGE_LOSS_WEIGHTING_SCOPE


class MobilePI05TrainingContractTests(unittest.TestCase):
    def _dataset(self, root: Path) -> None:
        (root / "meta").mkdir(parents=True)
        (root / "meta" / "info.json").write_text(
            json.dumps(
                {
                    "fps": 30,
                    "features": {
                        "observation.state": {
                            "shape": [80],
                            "names": list(MOBILE_PI05_STATE_NAMES),
                        },
                        "action": {
                            "shape": [14],
                            "names": list(MOBILE_PI05_RESIDUAL_ACTION_NAMES),
                        },
                        **{
                            key: {"shape": [224, 224, 3]}
                            for key in mobile_policy_visual_keys("rgbd")
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        (root / "meta" / "stats.json").write_text("{}\n", encoding="utf-8")
        (root / "PI05_RESIDUAL_DATASET_MANIFEST.json").write_text(
            json.dumps(
                {
                    "normalization_stats_policy": "quantile-v1",
                    "mode_conditioning_policy": "hidden_all_stages",
                    "task_language_policy": "mode_blind",
                }
            ),
            encoding="utf-8",
        )

    def _absolute_dataset(self, root: Path) -> None:
        (root / "meta").mkdir(parents=True)
        (root / "meta" / "info.json").write_text(
            json.dumps(
                {
                    "fps": 30,
                    "features": {
                        "observation.state": {
                            "shape": [80],
                            "names": list(MOBILE_PI05_ABSOLUTE_STATE_NAMES),
                        },
                        "action": {
                            "shape": [23],
                            "names": list(MOBILE_PI05_ABSOLUTE_ACTION_NAMES),
                        },
                        **{
                            key: {"shape": [224, 224, 3]}
                            for key in mobile_policy_visual_keys("rgbd")
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        (root / "meta" / "stats.json").write_text("{}\n", encoding="utf-8")
        (root / "PI05_ABSOLUTE_DATASET_MANIFEST.json").write_text(
            json.dumps(
                {
                    "normalization_stats_policy": "quantile-v1",
                    "mode_conditioning_policy": "hidden_all_stages",
                    "task_language_policy": "mode_blind",
                }
            ),
            encoding="utf-8",
        )

    def _incremental_dataset(self, root: Path) -> None:
        self._absolute_dataset(root)
        info_path = root / "meta" / "info.json"
        info = json.loads(info_path.read_text(encoding="utf-8"))
        info["features"]["action"] = {
            "shape": [21],
            "names": list(MOBILE_PI05_INCREMENTAL_ACTION_NAMES),
        }
        info_path.write_text(json.dumps(info), encoding="utf-8")
        (root / "PI05_ABSOLUTE_DATASET_MANIFEST.json").replace(
            root / "PI05_INCREMENTAL_DATASET_MANIFEST.json"
        )

    def test_builds_and_validates_fingerprinted_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._dataset(root)
            contract = build_pi05_training_contract(
                root,
                base_model="pi05_base",
                base_revision="abc",
                chunk_size=30,
                n_action_steps=10,
            )

        digest = validate_pi05_training_contract(
            contract, state_dim=80, action_dim=14, chunk_size=30
        )
        self.assertEqual(digest, contract["contract_sha256"])
        self.assertEqual(contract["policy_visual_modality"], "rgbd")
        self.assertEqual(
            contract["policy_visual_keys"],
            list(mobile_policy_visual_keys("rgbd")),
        )

    def test_rejects_contract_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._dataset(root)
            contract = build_pi05_training_contract(
                root,
                base_model="pi05_base",
                base_revision="abc",
                chunk_size=30,
                n_action_steps=10,
            )
        contract["action_semantics"] = "absolute_joint_position"

        with self.assertRaisesRegex(ValueError, "fingerprint"):
            validate_pi05_training_contract(
                contract, state_dim=80, action_dim=14, chunk_size=30
            )

    def test_builds_expert_independent_absolute_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._absolute_dataset(root)
            contract = build_pi05_training_contract(
                root,
                base_model="pi05_base",
                base_revision="abc",
                chunk_size=30,
                n_action_steps=10,
            )

        digest = validate_pi05_training_contract(
            contract, state_dim=80, action_dim=23, chunk_size=30
        )
        self.assertEqual(digest, contract["contract_sha256"])
        self.assertEqual(contract["action_contract"], "absolute_v1")
        self.assertEqual(
            contract["absolute_delta_policy"]["expert_reference"],
            "forbidden",
        )

    def test_builds_expert_independent_incremental_se3_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._incremental_dataset(root)
            contract = build_pi05_training_contract(
                root,
                base_model="pi05_base",
                base_revision="abc",
                chunk_size=30,
                n_action_steps=1,
            )

        digest = validate_pi05_training_contract(
            contract, state_dim=80, action_dim=21, chunk_size=30
        )
        self.assertEqual(digest, contract["contract_sha256"])
        self.assertEqual(contract["action_contract"], "incremental_se3_v1")
        self.assertEqual(
            contract["absolute_delta_policy"]["rotation"],
            "shortest_rotation_vector_target_times_current_inverse",
        )

    def test_requires_exact_augmented_architecture_protocols(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._dataset(root)
            contract = build_pi05_training_contract(
                root,
                base_model="pi05_base",
                base_revision="abc",
                chunk_size=30,
                n_action_steps=10,
                state_token_protocol="state-v1",
                mode_head_protocol="contextualized-head-v2",
                mode_head_class_weights=[0.75, 1.0, 1.5],
                stage_loss_weights=[2.0, 2.0, 1.25, 0.5, 0.75, 0.5],
                action_projection_protocol="full-action-io-v1",
            )

        validate_pi05_training_contract(
            contract,
            state_dim=80,
            action_dim=14,
            chunk_size=30,
            required_state_token_protocol="state-v1",
            required_mode_head_protocol="contextualized-head-v2",
            required_action_projection_protocol="full-action-io-v1",
            required_stage_loss_weights=[2.0, 2.0, 1.25, 0.5, 0.75, 0.5],
        )
        self.assertEqual(contract["mode_head_class_weights"], [0.75, 1.0, 1.5])
        self.assertEqual(
            contract["stage_loss_weights"],
            [2.0, 2.0, 1.25, 0.5, 0.75, 0.5],
        )
        self.assertEqual(
            contract["stage_loss_weighting_scope"],
            PI05_STAGE_LOSS_WEIGHTING_SCOPE,
        )
        with self.assertRaisesRegex(ValueError, "mode_head_protocol"):
            validate_pi05_training_contract(
                contract,
                state_dim=80,
                action_dim=14,
                chunk_size=30,
                required_mode_head_protocol="raw-head-v1",
            )

        with self.assertRaisesRegex(ValueError, "stage_loss_weights"):
            validate_pi05_training_contract(
                contract,
                state_dim=80,
                action_dim=14,
                chunk_size=30,
                required_stage_loss_weights=[1.0] * 6,
            )

    def test_visual_contract_rejects_checkpoint_dataset_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._dataset(root)
            contract = build_pi05_training_contract(
                root,
                base_model="pi05_base",
                base_revision="abc",
                chunk_size=30,
                n_action_steps=10,
            )

        with self.assertRaisesRegex(ValueError, "policy_visual_keys"):
            validate_pi05_training_contract(
                contract,
                state_dim=80,
                action_dim=14,
                chunk_size=30,
                required_visual_keys=mobile_policy_visual_keys("rgbd_wrist"),
            )

    def test_refingerprints_full_action_projection_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._dataset(root)
            contract = build_pi05_training_contract(
                root,
                base_model="pi05_base",
                base_revision="abc",
                chunk_size=30,
                n_action_steps=10,
            )

        updated = with_pi05_architecture_protocols(
            contract,
            state_token_protocol="state-v1",
            mode_head_protocol="mode-v2",
            action_projection_protocol="full-action-io-v1",
        )

        self.assertNotEqual(updated["contract_sha256"], contract["contract_sha256"])
        validate_pi05_training_contract(
            updated,
            state_dim=80,
            action_dim=14,
            chunk_size=30,
            required_action_projection_protocol="full-action-io-v1",
        )


if __name__ == "__main__":
    unittest.main()
