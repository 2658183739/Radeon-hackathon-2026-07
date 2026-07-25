from __future__ import annotations

import math

from .config import ExperimentConfig
from .contracts import CartesianAction, ControlDecision, RobotState
from .randomization import ParcelSample
from .state_machine import Command


DOWNWARD_QUATERNION = (0.0, 1.0, 0.0, 0.0)


def canonical_grasp_yaw(yaw_rad: float, max_abs_yaw_rad: float = math.pi / 3) -> float:
    """Exploit parallel-jaw symmetry while avoiding uncomfortable wrist rotations."""
    wrapped = (yaw_rad + math.pi / 2) % math.pi - math.pi / 2
    return wrapped if abs(wrapped) <= max_abs_yaw_rad else 0.0


def profile_grasp_yaw(sample: ParcelSample) -> float:
    """Choose a geometry-aware wrist yaw without changing the legacy baseline."""
    if sample.profile_id == "legacy_box":
        return canonical_grasp_yaw(sample.yaw_rad)
    if sample.shape == "cylinder" and sample.orientation_mode == "upright":
        return 0.0
    if sample.shape == "cylinder" and sample.orientation_mode == "horizontal":
        # Keep the fingers parallel to the tube axis so jaw closure crosses its diameter.
        return canonical_grasp_yaw(sample.yaw_rad, max_abs_yaw_rad=math.pi / 2)
    return canonical_grasp_yaw(sample.yaw_rad, max_abs_yaw_rad=math.pi / 2)


class ScriptedPickPlaceExpert:
    """Ground-truth Cartesian expert used before a visual policy is trained."""

    def __init__(self, config: ExperimentConfig, sample: ParcelSample) -> None:
        self.config = config
        self.sample = sample
        size_z = (
            sample.dimensions_m[2]
            if sample.dimensions_m is not None
            else config.task.parcel_base_size_m[2] * sample.size_scale_xyz[2]
        )
        self._initial_parcel_z = size_z / 2
        self._grasp_origin_xy: tuple[float, float] | None = None
        self._descent_committed = False
        self._drop_descent_committed = False
        self._retry_retreat_pending = False
        self._last_retry_count = 0
        half_yaw = profile_grasp_yaw(sample) / 2
        self._grasp_quaternion = (0.0, math.cos(half_yaw), math.sin(half_yaw), 0.0)

    @property
    def destination_position(self) -> tuple[float, float, float]:
        if self.sample.destination == "left":
            return self.config.task.left_bin_center_m
        return self.config.task.right_bin_center_m

    def action(self, decision: ControlDecision, state: RobotState) -> CartesianAction:
        if decision.retry_count != self._last_retry_count:
            self._descent_committed = False
            self._drop_descent_committed = False
            self._grasp_origin_xy = None
            self._retry_retreat_pending = (
                decision.retry_count > 0
                and self.config.task.retry_retreat_distance_m > 0
            )
            self._last_retry_count = decision.retry_count
        command = Command(decision.command)
        current = state.end_effector_pose[:3]
        parcel = state.parcel_pose[:3]

        if command == Command.MOVE_PREGRASP:
            desired = self._retry_or_safe_approach_position(current, parcel)
        elif command == Command.MOVE_LIFT:
            grasp_xy = self._grasp_origin_xy or (parcel[0], parcel[1])
            desired = (
                grasp_xy[0],
                grasp_xy[1],
                self._initial_parcel_z
                + self.grasp_hand_clearance_m()
                + self.config.task.lift_height_m,
            )
        elif command == Command.MOVE_DROP:
            desired = self._safe_drop_position(current)
        else:
            desired = tuple(float(value) for value in current)
        if command == Command.CLOSE_GRIPPER:
            self._grasp_origin_xy = (parcel[0], parcel[1])

        step_limit = self.config.control.max_ee_step_m
        if command == Command.MOVE_PREGRASP:
            if self.config.control.approach_step_m is not None:
                step_limit = min(step_limit, self.config.control.approach_step_m)
            if self._is_final_approach(current, parcel):
                step_limit = min(step_limit, self.config.control.final_approach_step_m)
                if self.sample.final_approach_step_m is not None:
                    step_limit = min(step_limit, self.sample.final_approach_step_m)
        elif command == Command.MOVE_LIFT and self.sample.lift_step_m is not None:
            step_limit = min(step_limit, self.sample.lift_step_m)
        target = self._bounded_step(current, desired, step_limit)
        target_quaternion = self._grasp_quaternion
        if command == Command.MOVE_PREGRASP:
            transit_z = parcel[2] + self.approach_clearance_m()
            horizontal_distance = math.hypot(current[0] - parcel[0], current[1] - parcel[1])
            if (
                horizontal_distance > self.config.task.position_tolerance_m
                and current[2] < transit_z - self.config.task.position_tolerance_m
            ):
                target_quaternion = DOWNWARD_QUATERNION
        gripper = 1.0 if command in {
            Command.SEARCH,
            Command.MOVE_PREGRASP,
            Command.OPEN_GRIPPER,
        } else -1.0
        return CartesianAction(
            target_position=target,
            target_quaternion=target_quaternion,
            gripper=gripper,
            command=command.value,
        )

    def pregrasp_position(self, parcel_pose: tuple[float, ...]) -> tuple[float, float, float]:
        return (
            parcel_pose[0],
            parcel_pose[1],
            parcel_pose[2] + self.grasp_hand_clearance_m(),
        )

    def grasp_hand_clearance_m(self) -> float:
        clearance = self.config.task.grasp_hand_clearance_m
        if self.sample.shape == "cylinder" and self.sample.orientation_mode == "upright":
            return clearance + 0.008
        return clearance

    def approach_clearance_m(self) -> float:
        """Return the horizontal-transit clearance for the current parcel.

        The legacy value is retained by default.  When enabled, only the
        parcel's vertical envelope above the baseline parcel is added, plus a
        separately audited margin.  This keeps the candidate causal: it changes
        the transit height without changing reset pose, physics, or the final
        grasp target.
        """
        base_clearance = self.config.task.approach_clearance_m
        if not self.config.task.size_aware_approach_enabled:
            return base_clearance
        dimensions = self.sample.dimensions_m or tuple(
            base * scale
            for base, scale in zip(
                self.config.task.parcel_base_size_m,
                self.sample.size_scale_xyz,
                strict=True,
            )
        )
        if self.sample.shape == "cylinder" and self.sample.orientation_mode == "horizontal":
            vertical_extent = dimensions[1]
        else:
            vertical_extent = dimensions[2] / 2.0
        baseline_extent = self.config.task.parcel_base_size_m[2] / 2.0
        return (
            base_clearance
            + max(0.0, vertical_extent - baseline_extent)
            + self.config.task.approach_clearance_margin_m
        )

    def pregrasp_tolerance_m(self) -> float:
        """Scale the close-pose window by grasp surface size and shape."""
        if self.sample.pregrasp_tolerance_m is not None:
            return self.sample.pregrasp_tolerance_m
        dimensions = self.sample.dimensions_m or tuple(
            base * scale
            for base, scale in zip(
                self.config.task.parcel_base_size_m,
                self.sample.size_scale_xyz,
                strict=True,
            )
        )
        if self.sample.shape == "cylinder":
            return max(self.config.task.position_tolerance_m, 0.035)
        is_flat_parcel = max(dimensions[:2]) > 0.12 and dimensions[2] <= 0.04
        if is_flat_parcel:
            return min(self.config.task.position_tolerance_m, 0.010)
        has_large_grasp_surface = max(dimensions[:2]) > 0.12 and dimensions[2] > 0.04
        if has_large_grasp_surface:
            return max(self.config.task.position_tolerance_m, 0.035)
        return self.config.task.position_tolerance_m

    def _safe_approach_position(
        self,
        current: tuple[float, ...],
        parcel_pose: tuple[float, ...],
    ) -> tuple[float, float, float]:
        tolerance = self.config.task.approach_xy_tolerance_m
        transit_z = parcel_pose[2] + self.approach_clearance_m()
        horizontal_distance = math.hypot(
            current[0] - parcel_pose[0],
            current[1] - parcel_pose[1],
        )

        if self._descent_committed:
            return self.pregrasp_position(parcel_pose)
        if horizontal_distance > tolerance and current[2] < transit_z - tolerance:
            return (current[0], current[1], transit_z)
        if horizontal_distance > tolerance:
            return (parcel_pose[0], parcel_pose[1], transit_z)
        self._descent_committed = True
        return self.pregrasp_position(parcel_pose)

    def _retry_or_safe_approach_position(
        self,
        current: tuple[float, ...],
        parcel_pose: tuple[float, ...],
    ) -> tuple[float, float, float]:
        """Create separation before re-approaching a parcel that moved on retry."""
        if not self._retry_retreat_pending:
            return self._safe_approach_position(current, parcel_pose)

        retreat_distance = self.config.task.retry_retreat_distance_m
        horizontal_distance = math.hypot(
            current[0] - parcel_pose[0],
            current[1] - parcel_pose[1],
        )
        if horizontal_distance >= retreat_distance:
            self._retry_retreat_pending = False
            return self._safe_approach_position(current, parcel_pose)

        if horizontal_distance > 1e-6:
            direction_x = (current[0] - parcel_pose[0]) / horizontal_distance
            direction_y = (current[1] - parcel_pose[1]) / horizontal_distance
        else:
            direction_x, direction_y = 1.0, 0.0
        retreat_z = max(
            current[2],
            parcel_pose[2] + self.grasp_hand_clearance_m() + 0.03,
        )
        return (
            parcel_pose[0] + direction_x * retreat_distance,
            parcel_pose[1] + direction_y * retreat_distance,
            retreat_z,
        )

    def _is_final_approach(
        self,
        current: tuple[float, ...],
        parcel_pose: tuple[float, ...],
    ) -> bool:
        return math.hypot(
            current[0] - parcel_pose[0],
            current[1] - parcel_pose[1],
        ) <= self.config.task.approach_xy_tolerance_m

    def lift_position(self) -> tuple[float, float, float]:
        return (
            self.sample.position_xy[0],
            self.sample.position_xy[1],
            self._initial_parcel_z
            + self.grasp_hand_clearance_m()
            + self.config.task.lift_height_m,
        )

    def drop_position(self) -> tuple[float, float, float]:
        destination = self.destination_position
        return (destination[0], destination[1], self.config.task.drop_hand_height_m)

    def _safe_drop_position(
        self,
        current: tuple[float, ...],
    ) -> tuple[float, float, float]:
        destination = self.destination_position
        tolerance = self.config.task.position_tolerance_m
        transfer_z = max(
            self.config.task.drop_hand_height_m + 0.10,
            self.lift_position()[2] + 0.05,
        )
        horizontal_distance = math.hypot(
            current[0] - destination[0],
            current[1] - destination[1],
        )
        if self._drop_descent_committed:
            return self.drop_position()
        if current[2] < transfer_z - tolerance:
            return (current[0], current[1], transfer_z)
        if horizontal_distance > tolerance:
            return (destination[0], destination[1], transfer_z)
        self._drop_descent_committed = True
        return self.drop_position()

    def _bounded_step(
        self,
        current: tuple[float, ...],
        desired: tuple[float, float, float],
        limit: float,
    ) -> tuple[float, float, float]:
        delta = tuple(float(target - value) for value, target in zip(current, desired, strict=True))
        distance = math.sqrt(sum(value * value for value in delta))
        if distance <= limit or distance == 0:
            return desired
        scale = limit / distance
        return tuple(float(value + offset * scale) for value, offset in zip(current, delta, strict=True))
