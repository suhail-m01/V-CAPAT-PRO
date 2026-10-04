"""Finite-scale time-correlated Fourier phase screens (visualization)."""
import numpy as np

class PhaseScreen:
    """Finite-outer-scale Fourier phase screen with frozen-flow/AR(1) evolution.

    Normalization is to unit RMS before converting to a bounded pixel displacement.
    r0 scales the pixel warp only; it does not prescribe an absolute phase variance.
    """
    def __init__(self, seed: int, grid: int = 96):
        self.rng = np.random.default_rng(seed)
        self.grid = grid
        self.screen = None
        self.frame = 0
        k = np.fft.fftfreq(grid)
        ky, kx = np.meshgrid(k, k, indexing='ij')
        k2 = kx*kx + ky*ky
        # Outer scale prevents divergence at DC; inner-scale roll-off limits aliasing.
        self.filter = (k2 + (1 / grid)**2) ** (-11/12) * np.exp(-k2 / .08)
        self.filter[0,0] = 0

    def _fresh(self):
        white = self.rng.standard_normal((self.grid, self.grid))
        field = np.fft.ifft2(np.fft.fft2(white) * self.filter).real
        field -= field.mean()
        return (field / max(float(field.std()), 1e-9)).astype('float32')

    def step(self, r0_m: float):
        if r0_m <= 0: raise ValueError('Fried parameter r0 must be positive')
        novel = self._fresh()
        if self.screen is None: self.screen = novel
        else:
            # One grid-cell frozen-flow shift every three frames plus innovation.
            advected = np.roll(self.screen, 1 if self.frame % 3 == 0 else 0, axis=1)
            self.screen = (.985 * advected + .17255 * novel).astype('float32')
        self.frame += 1
        strength = min(4.5, .30 / r0_m)
        dx = strength * self.screen
        dy = strength * np.roll(self.screen, self.grid // 4, axis=0)
        return dx, dy

    @property
    def temporal_correlation(self):
        return .985
