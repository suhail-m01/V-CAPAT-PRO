"""Optional contrast-preserving range/lead HUD drawn on an annotated BGR frame."""
import cv2

def overlay_hud(frame,range_km,lead_xy=(0,0),bearing_deg=0):
    result=frame.copy();h,w=result.shape[:2]
    cv2.putText(result,f'RANGE {range_km:,.0f} KM',(14,52),cv2.FONT_HERSHEY_SIMPLEX,.43,(90,230,185),1,cv2.LINE_AA)
    cv2.putText(result,f'BEARING {bearing_deg:+.2f} DEG',(14,72),cv2.FONT_HERSHEY_SIMPLEX,.43,(90,230,185),1,cv2.LINE_AA)
    cv2.putText(result,f'LEAD {lead_xy[0]:+.1f} / {lead_xy[1]:+.1f} PX',(14,92),cv2.FONT_HERSHEY_SIMPLEX,.43,(90,230,185),1,cv2.LINE_AA)
    return result
