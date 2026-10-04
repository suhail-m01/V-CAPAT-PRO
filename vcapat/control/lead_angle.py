"""Point-ahead estimation in angular units."""
import numpy as np
LIGHT_SPEED_M_S = 299_792_458.0

def lead_angle_rad(angular_rate_rad_s: float, distance_km: float, round_trip: bool = True) -> float:
    """Angular motion during light travel. Round-trip factor is a selectable assumption.

    This is not a Doppler velocity formula: v_transverse / D = angular_rate. When
    angular_rate is estimated from tracked world motion, lead is omega * flight time.
    """
    if not 10 <= distance_km <= 40_000:
        raise ValueError('Link distance must be 10–40,000 km')
    if not np.isfinite(angular_rate_rad_s):
        raise ValueError('Angular rate must be finite')
    return float(angular_rate_rad_s * distance_km * 1000 / LIGHT_SPEED_M_S * (2 if round_trip else 1))

