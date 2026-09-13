"""
Lightweight EKF for fusing IMU-derived motion estimates with GNSS when available.
"""

import numpy as np

METERS_PER_DEG_LAT = 111_320.0


def _meters_per_deg_lng(lat_deg: float) -> float:
    return 111_320.0 * np.cos(np.radians(lat_deg))


class DeadReckoningEKF:
    def __init__(self, init_lat: float, init_lng: float):
        self.x = np.array([init_lat, init_lng, 0.0, 0.0])
        self.P = np.eye(4) * 1e-3
        self.Q = np.diag([1e-9, 1e-9, 0.05, 0.05])
        self.R_gnss = np.diag([1e-9, 1e-9])

    def predict(self, dt: float, accel_north: float, accel_east: float):
        lat, lng, v_n, v_e = self.x

        v_n_new = v_n + accel_north * dt
        v_e_new = v_e + accel_east * dt

        d_lat = (v_n * dt) / METERS_PER_DEG_LAT
        d_lng = (v_e * dt) / _meters_per_deg_lng(lat)

        self.x = np.array([lat + d_lat, lng + d_lng, v_n_new, v_e_new])

        F = np.eye(4)
        F[0, 2] = dt / METERS_PER_DEG_LAT
        F[1, 3] = dt / _meters_per_deg_lng(lat)
        self.P = F @ self.P @ F.T + self.Q

    def update_gnss(self, gnss_lat: float, gnss_lng: float):
        H = np.zeros((2, 4))
        H[0, 0] = 1.0
        H[1, 1] = 1.0

        z = np.array([gnss_lat, gnss_lng])
        y = z - H @ self.x
        S = H @ self.P @ H.T + self.R_gnss
        K = self.P @ H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y
        self.P = (np.eye(4) - K @ H) @ self.P

    def position(self) -> tuple[float, float]:
        return float(self.x[0]), float(self.x[1])

    def drift_estimate_m(self) -> float:
        sigma_lat_m = np.sqrt(self.P[0, 0]) * METERS_PER_DEG_LAT
        sigma_lng_m = np.sqrt(self.P[1, 1]) * _meters_per_deg_lng(self.x[0])
        return float(np.sqrt(sigma_lat_m**2 + sigma_lng_m**2))

    def confidence(self) -> float:
        drift = self.drift_estimate_m()
        return float(np.clip(1.0 - drift / 50.0, 0.0, 1.0))
