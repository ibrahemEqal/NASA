"""Topocentric SPICE directions in the DEM's explicit DE421 lunar ME frame."""
from pathlib import Path
import numpy as np
import spiceypy as spice
from .geometry import basis,RADIUS_M

FRAME='MOON_ME_DE421'
KERNELS=['naif0012.tls','pck00011.tpc','moon_080317.tf','moon_pa_de421_1900-2050.bpc','de421.bsp']


def load_kernels(directory):
    paths=[Path(directory)/x for x in KERNELS]
    for path in paths:
        if not path.is_file():raise FileNotFoundError(path)
    spice.kclear()
    for path in paths:spice.furnsh(str(path))
    return paths


def direction(target,utc,latitude_deg,longitude_deg,observer_height_m,abcorr='CN+S'):
    if abcorr not in ('NONE','LT','LT+S','CN','CN+S'):
        raise ValueError('Supported reception corrections: NONE/LT/LT+S/CN/CN+S')
    east,north,up=basis(latitude_deg,longitude_deg)
    obspos=(RADIUS_M+observer_height_m)/1000*up
    et=spice.str2et(utc)
    state,lt=spice.spkcpo(target,et,FRAME,'OBSERVER',abcorr,obspos,'MOON',FRAME)
    v=state[:3];distance=float(np.linalg.norm(v))
    enu=np.array([v@east,v@north,v@up])
    radii=spice.bodvrd(target,'RADII',3)[1]
    return dict(target=target,utc=spice.et2utc(et,'ISOC',3)+'Z',azimuth_deg=float(np.rad2deg(np.arctan2(enu[0],enu[1]))%360),
       elevation_deg=float(np.rad2deg(np.arctan2(enu[2],np.hypot(enu[0],enu[1])))),
       range_km=distance,light_time_s=float(lt),topocentric_vector_km=v.tolist(),
       radius_inner_km=float(min(radii)),radius_outer_km=float(max(radii)),
       angular_radius_inner_deg=float(np.rad2deg(np.arcsin(min(radii)/distance))),
       angular_radius_outer_deg=float(np.rad2deg(np.arcsin(max(radii)/distance))),
       frame=FRAME,frame_evaluation='OBSERVER',aberration=abcorr,
       observer_moon_fixed_km=obspos.tolist())
