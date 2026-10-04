"""Simple FPA-like read, dark-current and shot-noise model (optional experiment)."""
import numpy as np

def expose(image,rng,quantum_efficiency=.8,read_noise_e=2.,dark_current_e_s=1.,exposure_s=.01,bit_depth=8):
    if not 0<quantum_efficiency<=1 or bit_depth not in (8,12,14,16) or exposure_s<=0:
        raise ValueError('Invalid FPA configuration')
    photons=image.astype('float32')*max(exposure_s*100,1e-5)
    electrons=rng.poisson(photons*quantum_efficiency+dark_current_e_s*exposure_s)
    measurement=electrons+rng.normal(0,read_noise_e,image.shape)
    full_scale=(1<<bit_depth)-1
    return np.clip(np.rint(measurement/(max(exposure_s*100,1e-5)*quantum_efficiency)*full_scale/255),0,full_scale).astype('uint16' if bit_depth>8 else 'uint8')
