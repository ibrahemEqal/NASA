import argparse
import json
from .pipeline import compute_horizon_from_dem
from .dem import LunarDEM


def main():
    p = argparse.ArgumentParser()
    commands = p.add_subparsers(dest='command', required=True)
    inspect = commands.add_parser('inspect-dem')
    inspect.add_argument('dem')
    h = commands.add_parser('compute-horizon')
    h.add_argument('dem')
    h.add_argument('--latitude', type=float, required=True)
    h.add_argument('--longitude', type=float, required=True)
    h.add_argument('--observer-elevation-m', type=float, required=True)
    h.add_argument('--mast-height-m', type=float, default=2.)
    h.add_argument('--southern-coverage-limit-deg', type=float, default=-80.)
    h.add_argument('--max-range-km', type=float, default=50.)
    h.add_argument('--azimuth-step-deg', type=float, default=.5)
    h.add_argument('--radial-step-m', type=float, default=80.)
    h.add_argument('--min-range-m', type=float)
    h.add_argument('--output', required=True)
    args = p.parse_args()
    if args.command == 'inspect-dem':
        print(json.dumps(LunarDEM(args.dem).meta, indent=2))
        return
    result = compute_horizon_from_dem(args.dem, args.output,
        southern_coverage_limit_deg=args.southern_coverage_limit_deg,
        latitude_deg=args.latitude, longitude_deg=args.longitude,
        observer_elevation_m=args.observer_elevation_m, mast_height_m=args.mast_height_m,
        max_range_m=args.max_range_km*1000, azimuth_step_deg=args.azimuth_step_deg,
        radial_step_m=args.radial_step_m, min_range_m=args.min_range_m)
    print(json.dumps(dict(rays=len(result['rays']), sampled_rays_complete=result['sampled_rays_complete'],
                          timing_seconds=result['timing_seconds']), indent=2))

if __name__ == '__main__':
    main()
