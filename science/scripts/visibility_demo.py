"""A seven-day numerical experiment, NOT a mission operational recommendation."""
import json,time
from pathlib import Path
from datetime import datetime,timedelta,timezone
import numpy as np
from luna_ready.ephemeris import load_kernels,direction
from luna_ready.disk import disk_fraction
from luna_ready.intervals import sampled_intervals
from luna_ready.pipeline import write_json
from luna_ready.provenance import sha256
root=Path(__file__).resolve().parents[1];out=root/'data/derived';kernels=load_kernels(root/'data/kernels')
horizon_path=out/'refined_horizon.json';h=json.loads(horizon_path.read_text())
az=np.array([r['azimuth_deg'] for r in h['rays']])
el=np.array([r['horizon_elevation_deg'] if r['sampled_ray_complete'] else np.nan for r in h['rays']])
start=datetime(2026,11,15,tzinfo=timezone.utc);records=[];t=time.perf_counter()
for index in range(337):
 utc=(start+timedelta(minutes=30*index)).isoformat().replace('+00:00','Z')
 for target in ['SUN','EARTH']:
  r=direction(target,utc,-89.466,-136.949,1948.9690908)
  inner=disk_fraction(r['azimuth_deg'],r['elevation_deg'],r['angular_radius_inner_deg'],az,el)
  outer=disk_fraction(r['azimuth_deg'],r['elevation_deg'],r['angular_radius_outer_deg'],az,el)
  # Earth ellipsoid projected silhouette is contained between concentric
  # circles of min/max body radii, regardless of orientation. Fractions need
  # area normalization as well; these are conservative numerical shape bounds.
  ratio=(r['radius_inner_km']/r['radius_outer_km'])**2
  lo=inner['visible_area_lower_bound']*ratio
  hi=min(1.,outer['visible_area_upper_bound']/ratio)
  # Exact containment gives zero/full visibility when the outer circle is
  # entirely hidden/visible, avoiding loose normalization at those endpoints.
  if outer['visible_area_upper_bound']<1e-12:lo=hi=0.
  if outer['visible_area_lower_bound']>1-1e-12:lo=hi=1.
  coarse=disk_fraction(r['azimuth_deg'],r['elevation_deg'],r['angular_radius_outer_deg'],az,el,32,128)
  r.update(disk_visible_fraction_lower=lo,disk_visible_fraction_upper=hi,
     outer_disk_fraction=outer['visible_area_lower_bound'],inner_disk_fraction=inner['visible_area_lower_bound'],
     disk_quadrature_refinement_difference=abs(outer['visible_area_lower_bound']-coarse['visible_area_lower_bound']),
     horizon_at_center_deg=float(np.interp(r['azimuth_deg'],np.append(az,360),np.append(el,el[0]))),
     shape_method='Concentric min/max-radius circle enclosure; not an oriented Earth limb solution',
     terrain_status='provisional sampled 80m DEM horizon')
  records.append(r)
 if index%96==0:print('completed time samples',index+1,flush=True)
intervals={}
for target in ['SUN','EARTH']:
 rr=[r for r in records if r['target']==target];ts=[r['utc'] for r in rr]
 state=[True if r['disk_visible_fraction_lower']>1e-6 else False if r['disk_visible_fraction_upper']<=1e-6 else None for r in rr]
 intervals[target]=dict(any_disk_visible_sample_runs=sampled_intervals(ts,state,True),
                        full_occlusion_sample_runs=sampled_intervals(ts,state,False),
                        unknown_samples=sum(s is None for s in state))
write_json(out/'visibility_demo.json',dict(records=records,intervals=intervals,
 source_horizon_file=horizon_path.name,source_horizon_sha256=sha256(horizon_path),
 kernels=[dict(filename=p.name,sha256=sha256(p)) for p in kernels],
 time_step_minutes=30,start_utc=records[0]['utc'],stop_utc=records[-1]['utc'],
 compute_seconds=time.perf_counter()-t,physical_visibility_certified=False,
 limitations=['Geometric visibility only; no power, link budget, Earth ground-station coverage, or landing-safety model.',
 'Sampled 30-minute runs do not exclude between-sample reversals. Transition times are bracketed, not exact.',
 'Terrain horizon is provisional; no independent real-terrain horizon validation or DEM error/effective-resolution layer.',
 'Earth shape handled by numerical min/max-circle enclosures; no atmosphere or refraction.',
 'Disk-area quadrature differences are deterministic numerical diagnostics, not confidence intervals.',
 'Center reception aberration applied to finite-disk geometry; differential limb light time and relativistic bending not modeled.']))
print('seconds',time.perf_counter()-t,'intervals',intervals,flush=True)
