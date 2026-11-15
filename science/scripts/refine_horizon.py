"""Explicit nested near-field grids and longer range; no terrain up-resolution claim."""
import argparse,time
from pathlib import Path
import numpy as np
from luna_ready.dem import LunarDEM
from luna_ready.horizon import compute_horizon
from luna_ready.pipeline import write_json
from luna_ready.provenance import provenance
from validate_real_dem import compare

p=argparse.ArgumentParser();p.add_argument('dem');p.add_argument('--output-dir',default='data/derived');args=p.parse_args()
out=Path(args.output_dir);dem=LunarDEM(args.dem);prov=provenance(dem);results={};summ={'cases':{},'comparisons':{},'provenance':prov}
for name,near_step,maxrange,azstep in [('near5',5,150000,.5),('near1',1,150000,.5),
 ('near0p25',.25,150000,.5),('range250',1,250000,.5),('range275',1,275000,.5),('refined',1,275000,.125)]:
 d=np.unique(np.concatenate([np.arange(near_step,2000,near_step),np.arange(2000,maxrange,20),[maxrange]]))
 t=time.perf_counter();r=compute_horizon(dem,-89.466,-136.949,1946.9690908,
    azimuth_step_deg=azstep,max_range_m=maxrange,distances_m=d)
 r['provenance']=prov;r['timing_seconds']={'compute':time.perf_counter()-t};results[name]=r
 write_json(out/f'{name}_horizon.json',r)
 h=np.array([x['horizon_elevation_deg'] for x in r['rays']]);
 summ['cases'][name]={'min_horizon_deg':float(h.min()),'max_horizon_deg':float(h.max()),
 'complete_rays':sum(x['sampled_ray_complete'] for x in r['rays']),'ray_count':len(h),
 'compute_seconds':r['timing_seconds']['compute']}
 print(name,summ['cases'][name],flush=True)
for a,b in [('near5','near1'),('near1','near0p25'),('near1','range250'),('range250','range275'),('range275','refined')]:
 summ['comparisons'][f'{a}__{b}']=compare(results[a],results[b])
write_json(out/'refinement_summary.json',summ)
print('COMPARISONS',summ['comparisons'],flush=True)
