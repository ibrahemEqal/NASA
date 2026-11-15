"""Spherical, planetocentric geometry. Meters and degrees at public boundaries."""
import numpy as np

RADIUS_M = 1737400.0


def basis(latitude_deg, longitude_deg):
    p, l = np.deg2rad([latitude_deg, longitude_deg])
    up = np.array([np.cos(p)*np.cos(l), np.cos(p)*np.sin(l), np.sin(p)])
    east = np.array([-np.sin(l), np.cos(l), 0.])
    north = np.cross(up, east)
    return east, north, up


def destinations(latitude_deg, longitude_deg, azimuth_deg, distances_m, radius_m=RADIUS_M):
    """Great-circle rays, azimuth clockwise from local geographic north.

    Vector formulation avoids asin/longitude cancellation near the poles.
    Result shape broadcasts azimuth and distance inputs.
    """
    east, north, up = basis(latitude_deg, longitude_deg)
    a = np.deg2rad(np.asarray(azimuth_deg))[..., None]
    d = (np.asarray(distances_m)/radius_m)[..., None]
    tangent = np.cos(a)*north + np.sin(a)*east
    v = np.cos(d)*up + np.sin(d)*tangent
    lat = np.rad2deg(np.arctan2(v[..., 2], np.hypot(v[..., 0], v[..., 1])))
    lon = np.rad2deg(np.arctan2(v[..., 1], v[..., 0]))
    return lat, lon


def terrain_elevation_deg(distance_m, height_m, observer_height_m, radius_m=RADIUS_M):
    d = np.asarray(distance_m, dtype=float)
    if np.any(d <= 0) or np.any(d >= np.pi*radius_m):
        raise ValueError("Distances must be positive and less than a half circumference")
    theta = d/radius_m
    rt = radius_m + np.asarray(height_m)
    # Stable form of rt*cos(theta) - (R+h_observer).
    vertical = np.asarray(height_m) - observer_height_m - 2*rt*np.sin(theta/2)**2
    horizontal = rt*np.sin(theta)
    return np.rad2deg(np.arctan2(vertical, horizontal))
