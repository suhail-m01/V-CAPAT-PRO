"""Reproducible, bounded calibration bias due to a slow temperature change."""
from dataclasses import dataclass

@dataclass
class ThermalDrift:
    coefficient_px_per_c:float=.15
    reference_c:float=20.
    correction_px:float=0.
    def raw_bias(self,temperature_c):return (temperature_c-self.reference_c)*self.coefficient_px_per_c
    def calibrate(self,reference_observation_px,known_reference_px):
        self.correction_px=reference_observation_px-known_reference_px
    def measure(self,x_px,temperature_c):return x_px+self.raw_bias(temperature_c)-self.correction_px
