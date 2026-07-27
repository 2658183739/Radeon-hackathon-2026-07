"""Physical contact telemetry for the mobile right-arm V cradle."""

from __future__ import annotations

from typing import Any


def discover_mobile_v_cradle_geoms(robot: Any) -> frozenset[int]:
    """Resolve the two generated V-cradle collision geometries."""

    indices = frozenset(
        int(geom.idx)
        for link in robot.links
        for geom in link.geoms
        if "mobile_right_v_cradle_" in str(getattr(geom, "name", ""))
        and str(getattr(geom, "name", "")).endswith("_collision")
    )
    if len(indices) != 2:
        gripper = next(
            (
                link
                for link in robot.links
                if str(getattr(link, "name", "")) == "panda1_gripper"
            ),
            None,
        )
        collision_geoms = tuple(gripper.geoms) if gripper is not None else ()
        if len(collision_geoms) >= 2:
            indices = frozenset(int(geom.idx) for geom in collision_geoms[-2:])
    if len(indices) != 2:
        raise RuntimeError(
            f"expected two mobile V-cradle collision geoms, got {len(indices)}"
        )
    return indices


class MobileVCradleMonitor:
    """Measure real cradle/parcel contact without creating a hidden attachment."""

    def __init__(self, *, robot: Any, parcel: Any, torch: Any) -> None:
        self.robot = robot
        self.parcel = parcel
        self.torch = torch
        self.geom_indices = discover_mobile_v_cradle_geoms(robot)
        self.contact_steps = 0
        self.max_contact_force_n = 0.0
        self.last_contact_geoms = 0
        self.last_contact_force_n = 0.0

    def snapshot(self) -> tuple[int, float]:
        contacts = self.robot.get_contacts(with_entity=self.parcel)
        geom_a = contacts["geom_a"]
        if geom_a.numel() == 0:
            self.last_contact_geoms = 0
            self.last_contact_force_n = 0.0
            return 0, 0.0
        geom_b = contacts["geom_b"]
        valid = contacts.get("valid_mask")
        forces = contacts["force_a"]
        contacted: set[int] = set()
        mask = self.torch.zeros_like(geom_a, dtype=self.torch.bool)
        for geom_index in self.geom_indices:
            geom_mask = (geom_a == geom_index) | (geom_b == geom_index)
            if valid is not None:
                geom_mask &= valid
            if bool(geom_mask.any().item()):
                contacted.add(geom_index)
                mask |= geom_mask
        force_n = 0.0
        if bool(mask.any().item()):
            force_n = float(
                self.torch.linalg.vector_norm(forces[mask], dim=-1).max().item()
            )
            self.contact_steps += 1
        self.last_contact_geoms = len(contacted)
        self.last_contact_force_n = force_n
        self.max_contact_force_n = max(self.max_contact_force_n, force_n)
        return self.last_contact_geoms, force_n

    def summary(self) -> dict[str, float | int | bool]:
        return {
            "physical_contact": self.contact_steps > 0,
            "contact_steps": self.contact_steps,
            "last_contact_geoms": self.last_contact_geoms,
            "last_contact_force_n": self.last_contact_force_n,
            "max_contact_force_n": self.max_contact_force_n,
        }
