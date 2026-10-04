"""TLE line validation and optional SGP4 propagation when installed."""
def parse_tle(text):
    lines=[line.strip() for line in text.splitlines() if line.strip()]
    if len(lines)==3:name,line1,line2=lines
    elif len(lines)==2:line1,line2=lines;name='UNNAMED'
    else:raise ValueError('TLE requires two numbered lines and an optional name')
    if not line1.startswith('1 ') or not line2.startswith('2 ') or len(line1)<69 or len(line2)<69:
        raise ValueError('Invalid TLE line layout')
    if line1[2:7]!=line2[2:7]:raise ValueError('TLE satellite numbers do not match')
    return name,line1,line2

def satellite_at(text,julian_date,minutes=0):
    _,l1,l2=parse_tle(text)
    try:from sgp4.api import Satrec
    except ImportError as exc:raise RuntimeError('TLE propagation requires the optional sgp4 package') from exc
    error,r,v=Satrec.twoline2rv(l1,l2).sgp4(julian_date,minutes/1440)
    if error:raise ValueError(f'SGP4 propagation error {error}')
    return {'position_km':r,'velocity_km_s':v}


def ground_station_look_angles(text, at_utc, latitude_deg, longitude_deg, height_km=0.):
    """SGP4/TEME approximate azimuth/elevation for a user-supplied TLE.

    Uses a GMST Earth rotation and WGS84 ground geodesy; no EOP, refraction,
    TEME-to-ITRF polar-motion correction or accuracy certification. The TLE's
    epoch/age remains the user's responsibility. UTC-aware input required.
    """
    import math
    from datetime import timezone
    if at_utc.tzinfo is None or at_utc.utcoffset() is None:raise ValueError('A timezone-aware UTC instant is required')
    if not -90<=latitude_deg<=90 or not -180<=longitude_deg<=180 or not -1<=height_km<=50:
        raise ValueError('Invalid ground station location')
    try:
        from sgp4.api import Satrec,jday
    except ImportError as exc:raise RuntimeError('Install sgp4 to evaluate user-supplied TLEs') from exc
    name,line1,line2=parse_tle(text)
    when=at_utc.astimezone(timezone.utc)
    jd,fr=jday(when.year,when.month,when.day,when.hour,when.minute,when.second+when.microsecond/1e6)
    err,r,v=Satrec.twoline2rv(line1,line2).sgp4(jd,fr)
    if err:raise ValueError(f'SGP4 propagation error {err}; check TLE age and reference UTC instant')
    whole=jd+fr;t=(whole-2451545)/36525
    gmst=math.radians((280.46061837+360.98564736629*(whole-2451545)+.000387933*t*t-t**3/38710000)%360)
    cs,sn=math.cos(gmst),math.sin(gmst)
    sat_x,sat_y,sat_z=cs*r[0]+sn*r[1],-sn*r[0]+cs*r[1],r[2]
    lat,lon=math.radians(latitude_deg),math.radians(longitude_deg)
    a=6378.137;e2=.00669437999014;n=a/math.sqrt(1-e2*math.sin(lat)**2)
    gx=(n+height_km)*math.cos(lat)*math.cos(lon)
    gy=(n+height_km)*math.cos(lat)*math.sin(lon)
    gz=(n*(1-e2)+height_km)*math.sin(lat)
    dx,dy,dz=sat_x-gx,sat_y-gy,sat_z-gz
    east=-math.sin(lon)*dx+math.cos(lon)*dy
    north=-math.sin(lat)*math.cos(lon)*dx-math.sin(lat)*math.sin(lon)*dy+math.cos(lat)*dz
    up=math.cos(lat)*math.cos(lon)*dx+math.cos(lat)*math.sin(lon)*dy+math.sin(lat)*dz
    return {'name':name,'time_utc':when.isoformat(),'azimuth_deg':round(math.degrees(math.atan2(east,north))%360,4),
            'elevation_deg':round(math.degrees(math.atan2(up,math.hypot(east,north))),4),
            'slant_range_km':round(math.sqrt(dx*dx+dy*dy+dz*dz),3),'above_horizon':up>0,
            'eci_position_km':tuple(round(float(x),3) for x in r),
            'note':'User-supplied TLE; GMST/TEME approximation, no EOP or atmospheric refraction. Not flight navigation.'}
