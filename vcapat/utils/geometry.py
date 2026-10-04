"""Camera pixel ↔ angular error conversion in degrees."""
def pixels_to_degrees(offset_px,fov_deg,resolution_px):
    if fov_deg<=0 or resolution_px<=0:raise ValueError('FOV and resolution must be positive')
    return offset_px*fov_deg/resolution_px

def degrees_to_pixels(angle_deg,fov_deg,resolution_px):
    if fov_deg<=0 or resolution_px<=0:raise ValueError('FOV and resolution must be positive')
    return angle_deg*resolution_px/fov_deg
