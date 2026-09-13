"""
AI motion estimator + adaptive error model.
"""

from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass
class ImuSample:
    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float


@dataclass
class MotionEstimate:
    accel_north: float
    accel_east: float
    bias_correction: float
    vibration_flag: bool


class AIMotionEstimator:
    def __init__(self, model_path: str | None = None):
        self.model = None
        if model_path:
            self.model = self._load_model(model_path)

    def _load_model(self, path: str):
        return None

    def estimate(self, window: List[ImuSample], heading_rad: float) -> MotionEstimate:
        if self.model is not None:
            return self._model_predict(window, heading_rad)
        return self._stub_predict(window, heading_rad)

    def _model_predict(self, window: List[ImuSample], heading_rad: float) -> MotionEstimate:
        raise NotImplementedError("Wire up real model inference here once trained")

    def _stub_predict(self, window: List[ImuSample], heading_rad: float) -> MotionEstimate:
        latest = window[-1]
        accel_forward = latest.accel_x
        accel_lateral = latest.accel_y

        accel_north = accel_forward * np.cos(heading_rad) - accel_lateral * np.sin(heading_rad)
        accel_east = accel_forward * np.sin(heading_rad) + accel_lateral * np.cos(heading_rad)

        vibration_flag = abs(latest.accel_z) > 2.0

        return MotionEstimate(
            accel_north=float(accel_north),
            accel_east=float(accel_east),
            bias_correction=0.0,
            vibration_flag=vibration_flag,
        )


class AdaptiveErrorModel:
    def adjust(self, estimate: MotionEstimate, base_q_scale: float = 1.0) -> float:
        if estimate.vibration_flag:
            return base_q_scale * 3.0
        return base_q_scale
