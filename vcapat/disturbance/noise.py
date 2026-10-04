"""Composite Poisson, additive Gaussian and salt-pepper camera noise.

The Gaussian path intentionally uses OpenCV's vectorized RNG instead of asking
NumPy to allocate hundreds of thousands of float64 normal samples per frame.
On Windows this materially improves the real-time benchmark while preserving a
deterministic sequence: every OpenCV draw is reseeded from the scenario's
NumPy Generator.
"""
import cv2
import numpy as np

_MAX_CV_SEED = 2_147_483_647


def _cv_seed(rng):
    """Seed OpenCV's RNG from the scenario RNG so runs stay reproducible."""
    cv2.setRNGSeed(int(rng.integers(0, _MAX_CV_SEED)))


def apply_noise(image, config, rng):
    result = image

    if 'poisson' in config.noise_types:
        # Poisson is inherently signal-dependent. Keep NumPy's exact sampler;
        # it is used only when explicitly selected.
        result = rng.poisson(result.astype('float32')).clip(0, 255).astype('uint8')

    if 'gaussian' in config.noise_types and config.noise_std > 0:
        # cv2.randn + cv2.add executes the full 640x480 path in optimized native
        # code and saturates directly into uint8, avoiding float64 temporaries.
        _cv_seed(rng)
        noise = np.empty(result.shape, dtype=np.float32)
        cv2.randn(noise, 0.0, float(config.noise_std))
        result = cv2.add(result, noise, dtype=cv2.CV_8U)

    if 'salt_pepper' in config.noise_types and config.salt_pepper_pct > 0:
        # Generate only the requested impulse pixels rather than a full-frame
        # float mask. Duplicate coordinates are harmless and keep this O(k).
        result = result.copy()
        count = int(result.size * float(config.salt_pepper_pct))
        if count:
            ys = rng.integers(0, result.shape[0], size=count)
            xs = rng.integers(0, result.shape[1], size=count)
            half = count // 2
            result[ys[:half], xs[:half]] = 0
            result[ys[half:], xs[half:]] = 255

    return result
