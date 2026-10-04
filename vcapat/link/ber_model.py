"""Illustrative uncoded coherent BPSK AWGN BER vs assumed linear SNR."""
import math

def bpsk_ber(snr_linear):
    if snr_linear<0:raise ValueError('SNR must be nonnegative')
    return .5*math.erfc(math.sqrt(snr_linear))

def pointing_snr(reference_snr,angle_error_rad,beamwidth_rad):
    if beamwidth_rad<=0:raise ValueError('Beamwidth must be positive')
    return reference_snr*math.exp(-(angle_error_rad/beamwidth_rad)**2)
