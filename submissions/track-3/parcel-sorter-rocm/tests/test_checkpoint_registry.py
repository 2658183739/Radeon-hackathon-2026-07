import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from parcel_sorter.checkpoint_registry import (
    activate_promoted_checkpoint,
    load_active_checkpoint,
)


class CheckpointRegistryTests(unittest.TestCase):
    def test_activation_is_atomic_and_loadable(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = root / "outputs/model"
            checkpoint.mkdir(parents=True)
            artifact = checkpoint / "model.safetensors"
            artifact.write_bytes(b"promoted-weights")
            artifact_sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
            evidence = root / "evidence/gate.json"
            evidence.parent.mkdir()
            evidence.write_text(
                json.dumps(
                    {
                        "promoted": True,
                        "pairing": {"candidate_checkpoint_sha256": artifact_sha},
                    }
                ),
                encoding="utf-8",
            )
            config = root / "configs/active.json"
            selected = activate_promoted_checkpoint(
                config,
                project_root=root,
                checkpoint=checkpoint,
                promotion_evidence=evidence,
                promoted_on="2026-07-27",
            )
            self.assertEqual(selected.checkpoint, checkpoint)
            self.assertFalse((config.parent / ".active.json.tmp").exists())

    def test_rejected_gate_does_not_replace_active_config(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = root / "outputs/model"
            checkpoint.mkdir(parents=True)
            artifact = checkpoint / "model.safetensors"
            artifact.write_bytes(b"candidate")
            artifact_sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
            evidence = root / "evidence/gate.json"
            evidence.parent.mkdir()
            evidence.write_text(
                json.dumps(
                    {
                        "promoted": False,
                        "pairing": {"candidate_checkpoint_sha256": artifact_sha},
                    }
                ),
                encoding="utf-8",
            )
            config = root / "configs/active.json"
            config.parent.mkdir()
            config.write_text("old-active-config", encoding="utf-8")
            with self.assertRaises(ValueError):
                activate_promoted_checkpoint(
                    config,
                    project_root=root,
                    checkpoint=checkpoint,
                    promotion_evidence=evidence,
                )
            self.assertEqual(config.read_text(encoding="utf-8"), "old-active-config")

    def test_resolves_matching_promoted_checkpoint(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = root / "outputs/model"
            checkpoint.mkdir(parents=True)
            artifact = checkpoint / "model.safetensors"
            artifact.write_bytes(b"weights")
            artifact_sha = hashlib.sha256(b"weights").hexdigest()
            evidence = root / "evidence/gate.json"
            evidence.parent.mkdir()
            evidence.write_text(
                json.dumps(
                    {
                        "promoted": True,
                        "pairing": {"candidate_checkpoint_sha256": artifact_sha},
                    }
                ),
                encoding="utf-8",
            )
            evidence_sha = hashlib.sha256(evidence.read_bytes()).hexdigest()
            config = root / "configs/active.json"
            config.parent.mkdir()
            config.write_text(
                json.dumps(
                    {
                        "protocol": "pash-active-mobile-checkpoint-v1",
                        "status": "promoted",
                        "checkpoint_relative_path": "outputs/model",
                        "artifact": "model.safetensors",
                        "artifact_sha256": artifact_sha,
                        "promotion_evidence_relative_path": "evidence/gate.json",
                        "promotion_evidence_sha256": evidence_sha,
                    }
                ),
                encoding="utf-8",
            )
            selected = load_active_checkpoint(config, project_root=root)
            self.assertEqual(selected.checkpoint, checkpoint)

    def test_rejects_gate_for_different_checkpoint(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = root / "outputs/model"
            checkpoint.mkdir(parents=True)
            artifact = checkpoint / "model.safetensors"
            artifact.write_bytes(b"weights")
            artifact_sha = hashlib.sha256(b"weights").hexdigest()
            evidence = root / "evidence/gate.json"
            evidence.parent.mkdir()
            evidence.write_text(
                json.dumps(
                    {"promoted": True, "pairing": {"candidate_checkpoint_sha256": "0" * 64}}
                ),
                encoding="utf-8",
            )
            config = root / "configs/active.json"
            config.parent.mkdir()
            config.write_text(
                json.dumps(
                    {
                        "protocol": "pash-active-mobile-checkpoint-v1",
                        "status": "promoted",
                        "checkpoint_relative_path": "outputs/model",
                        "artifact": "model.safetensors",
                        "artifact_sha256": artifact_sha,
                        "promotion_evidence_relative_path": "evidence/gate.json",
                        "promotion_evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_active_checkpoint(config, project_root=root)


if __name__ == "__main__":
    unittest.main()
