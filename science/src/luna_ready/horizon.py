import numpy as np
from .geometry import destinations, terrain_elevation_deg, RADIUS_M
from .dem import OUTSIDE_RASTER, NODATA, OUTSIDE_COVERAGE


def radial_grid(max_range_m, radial_step_m, min_range_m=None):
    start = radial_step_m if min_range_m is None else min_range_m
    if not (0 < start <= max_range_m and radial_step_m > 0):
        raise ValueError('Require 0 < min range <= max range and positive step')
    d = np.arange(start, max_range_m, radial_step_m)
    return np.append(d, max_range_m)


def summarize_ray(azimuth_deg, distances, heights, flags, observer_height_m):
    valid = (flags == 0) & np.isfinite(heights)
    result = dict(azimuth_deg=float(azimuth_deg), valid_sample_count=int(valid.sum()),
                  requested_sample_count=len(distances), sampled_ray_complete=bool(valid.all()),
                  nodata=bool(np.any(flags & NODATA)),
                  outside_raster=bool(np.any(flags & OUTSIDE_RASTER)),
                  outside_coverage=bool(np.any(flags & OUTSIDE_COVERAGE)))
    if not valid.any():
        result.update(horizon_elevation_deg=None, controlling_distance_m=None,
                      controlling_elevation_m=None, first_invalid_distance_m=float(distances[0]))
        return result
    angles = terrain_elevation_deg(distances, heights, observer_height_m)
    i = int(np.argmax(np.where(valid, angles, -np.inf)))
    result.update(horizon_elevation_deg=float(angles[i]), controlling_distance_m=float(distances[i]),
                  controlling_elevation_m=float(heights[i]),
                  first_invalid_distance_m=None if valid.all() else float(distances[np.flatnonzero(~valid)[0]]))
    return result


def compute_horizon(dem, latitude_deg, longitude_deg, observer_elevation_m, mast_height_m=2.,
                    azimuth_step_deg=.5, radial_step_m=80., max_range_m=50000.,
                    min_range_m=None, chunk_rays=32, distances_m=None):
    if not (-90 < latitude_deg <= dem.coverage_limit):
        raise ValueError('Observer must be inside coverage and away from exact pole')
    if not np.isfinite([longitude_deg, observer_elevation_m, mast_height_m]).all() or mast_height_m < 0:
        raise ValueError('Invalid observer specification')
    if not 0 < azimuth_step_deg <= 360 or not np.isclose(360/azimuth_step_deg, round(360/azimuth_step_deg)):
        raise ValueError('Azimuth step must divide 360')
    if chunk_rays < 1:
        raise ValueError('chunk_rays must be positive')
    z, flags = dem.sample(latitude_deg, longitude_deg)
    if int(flags) != 0:
        raise ValueError('Observer DEM sample is invalid')
    distances = radial_grid(max_range_m, radial_step_m, min_range_m) if distances_m is None else np.asarray(distances_m,float)
    if distances.ndim != 1 or len(distances)==0 or not np.isfinite(distances).all() or np.any(distances<=0) or np.any(np.diff(distances)<=0) or distances[-1]!=max_range_m:
        raise ValueError('Custom distances must be finite, positive, increasing and end at max range')
    azimuths = np.arange(round(360/azimuth_step_deg))*azimuth_step_deg
    rays = []
    for offset in range(0, len(azimuths), chunk_rays):
        az = azimuths[offset:offset+chunk_rays]
        lat, lon = destinations(latitude_deg, longitude_deg, az[:, None], distances[None, :])
        heights, flags = dem.sample(lat, lon)
        for a, h, f in zip(az, heights, flags):
            ray = summarize_ray(a, distances, h, f, observer_elevation_m+mast_height_m)
            if ray['controlling_distance_m'] is not None:
                clat, clon = destinations(latitude_deg, longitude_deg, a, ray['controlling_distance_m'])
                ray.update(controlling_latitude_deg=float(clat),controlling_longitude_deg=float(clon))
            else:
                ray.update(controlling_latitude_deg=None,controlling_longitude_deg=None)
            rays.append(ray)
    return dict(rays=rays, sampled_rays_complete=all(r['sampled_ray_complete'] for r in rays),
                physical_horizon_certified=False,
                site=dict(latitude_deg=latitude_deg, longitude_deg=longitude_deg,
                          longitude_convention='east-positive, -180..180',
                          observer_elevation_m=observer_elevation_m, mast_height_m=mast_height_m,
                          dem_sample_elevation_m=float(z), coordinate_status='provisional frame match'),
                settings=dict(azimuth_step_deg=azimuth_step_deg, radial_step_m=radial_step_m,
                              min_range_m=float(distances[0]), max_range_m=max_range_m,
                              southern_coverage_limit_deg=dem.coverage_limit, chunk_rays=chunk_rays,
                              reference_radius_m=RADIUS_M,
                              custom_distances_m=None if distances_m is None else distances.tolist()),
                limitations=['Sample completeness is only completeness on the requested discrete grid.',
                             'Terrain between rays/samples, inside minimum range, and beyond maximum range is not certified.',
                             '80m pixel spacing is not independently established effective terrain resolution.',
                             'No elevation-error raster or independent terrain-horizon validation yet.'])
