"""Bounded per-frame camera boresight jitter."""
def sample_jitter(rng,amplitude_px):
    if not 0<=amplitude_px<=20:raise ValueError('jitter amplitude must be 0–20 px')
    return float(rng.uniform(-amplitude_px,amplitude_px)),float(rng.uniform(-amplitude_px,amplitude_px))
