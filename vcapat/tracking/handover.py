"""Image innovation trigger for an alternative visible beacon."""
import math

def should_handover(track_state,detected,predicted,beacon_size_px):
    return (track_state in ('LOCKED','COASTING','REACQUIRING') and detected is not None and predicted is not None
            and math.dist(tuple(detected),tuple(predicted))>max(12,beacon_size_px*1.2))
