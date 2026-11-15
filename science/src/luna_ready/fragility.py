"""Deterministic single-point vertical perturbation, never a probability."""
import numpy as np
from .geometry import RADIUS_M


def single_point_vertical_change(distance_m,height_m,observer_height_m,target_elevation_deg):
    if not 0<distance_m<np.pi*RADIUS_M or not -90<target_elevation_deg<90:
        raise ValueError('Invalid distance/target')
    theta=distance_m/RADIUS_M
    denominator=np.cos(theta)-np.tan(np.deg2rad(target_elevation_deg))*np.sin(theta)
    if denominator<=0: raise ValueError('Target angle unreachable for a positive terrain radius')
    required=(RADIUS_M+observer_height_m)/denominator-RADIUS_M
    return dict(vertical_change_m=float(required-height_m),required_height_m=float(required),
                interpretation='deterministic change of one terrain sample; other ridges may control the horizon')
