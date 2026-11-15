"""Finite opaque disk geometry; no irradiance, atmosphere, or radio-link model."""
import numpy as np
from .geometry import basis


def constant_horizon_fraction(center_offset_rad, angular_radius_rad):
    """Analytic *small-angle planar* disk segment (explicit approximation)."""
    if not angular_radius_rad>0: raise ValueError('Disk radius must be positive')
    q=np.clip(np.asarray(center_offset_rad)/angular_radius_rad,-1,1)
    return (np.arccos(-q)+q*np.sqrt(1-q*q))/np.pi


def disk_fraction(azimuth_deg,elevation_deg,angular_radius_deg,horizon_azimuths_deg,
                  horizon_elevations_deg,n_radial=64,n_angular=256):
    """Integrate apparent projected area over an orthographic circular disk.

    Rays use exact unit-sphere directions; projected radial coordinate squared
    has uniform area measure. Horizon is periodic linear interpolation of an
    explicitly sampled profile. This cannot recover missing terrain peaks.
    A NaN endpoint makes that segment unknown; report an area bound, not a
    fabricated visibility fraction. Refinement is caller-controlled.
    """
    if not 0<angular_radius_deg<90 or n_radial<2 or n_angular<4:
        raise ValueError('Invalid disk or integration resolution')
    ha=np.asarray(horizon_azimuths_deg,float);he=np.asarray(horizon_elevations_deg,float)
    if len(ha)<2 or ha.shape!=he.shape or np.any(np.diff(ha)<=0) or ha[0]!=0 or ha[-1]>=360:
        raise ValueError('Horizon azimuths must be ordered from 0 to less than 360')
    # Coordinates are (east,north,up). Construct a center and its tangent axes.
    az,el,alpha=np.deg2rad([azimuth_deg,elevation_deg,angular_radius_deg])
    center=np.array([np.cos(el)*np.sin(az),np.cos(el)*np.cos(az),np.sin(el)])
    tangent_az=np.array([np.cos(az),-np.sin(az),0.])
    tangent_el=np.cross(tangent_az,center)
    nodes,weights=np.polynomial.legendre.leggauss(n_radial)
    q=(nodes+1)/2; weights=weights/2
    phi=(np.arange(n_angular)+.5)*2*np.pi/n_angular
    rho=np.sqrt(q)[:,None]*np.sin(alpha)
    v=(np.sqrt(1-rho*rho)[...,None]*center+
       rho[...,None]*(np.cos(phi)[None,:,None]*tangent_az+np.sin(phi)[None,:,None]*tangent_el))
    a=np.rad2deg(np.arctan2(v[...,0],v[...,1]))%360
    e=np.rad2deg(np.arctan2(v[...,2],np.hypot(v[...,0],v[...,1])))
    horizon=np.interp(a,np.append(ha,360),np.append(he,he[0]))
    known=np.isfinite(horizon)
    w=weights[:,None]/n_angular
    visible=float(np.sum(w*((e>horizon)&known)))
    unknown=float(np.sum(w*~known))
    return dict(visible_area_lower_bound=visible,visible_area_upper_bound=min(1.,visible+unknown),
                unknown_area_fraction=unknown,n_radial=n_radial,n_angular=n_angular,
                geometry='finite disk, uniform apparent projected area; exact spherical directions')
