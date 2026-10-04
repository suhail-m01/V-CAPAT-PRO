"""Data-driven demo badges; never award when measurements are unavailable."""
def earned_achievements(rows,summary):
    badges=[]
    if summary.get('acquisition_s') is not None and summary['acquisition_s']<1:badges.append('Sharpshooter · lock in under one second')
    if summary.get('duration_s',0)>=60 and summary.get('pointing_rmse_px') is not None and summary['pointing_rmse_px']<3:badges.append('Precision Master · sixty seconds below three pixels RMSE')
    if summary.get('minimum_processing_fps') is not None and summary['minimum_processing_fps']>=60 and len(rows)>=60:badges.append('Speed Demon · sixty frames above sixty processing FPS')
    if max((r.get('designated_id') or 0 for r in rows),default=0)>=4:badges.append('Constellation Commander · designated fifth beacon')
    return badges
