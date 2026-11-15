"""Run actual DEM sampling/convergence/profile experiments; no external kernels."""
import argparse
import cProfile
import io
import pstats
import time
from pathlib import Path
import numpy as np
from luna_ready.dem import LunarDEM
from luna_ready.horizon import compute_horizon
from luna_ready.pipeline import write_json
from luna_ready.provenance import provenance


def compare(a,b):
    aa=np.array([r['horizon_elevation_deg'] for r in a['rays']],float)
    bb=np.array([r['horizon_elevation_deg'] for r in b['rays']],float)
    # Compare only nested azimuth grids, without interpolating away angular peaks.
    if len(aa)>len(bb): aa,bb=bb,aa
    bb=bb[::len(bb)//len(aa)]
    delta=bb-aa
    return dict(max_abs_difference_deg=float(np.max(np.abs(delta))),
                median_abs_difference_deg=float(np.median(np.abs(delta))),
                increased_rays_over_0p01deg=int(np.sum(delta>.01)),
                decreased_rays_over_0p01deg=int(np.sum(delta<-.01)))


def main():
    p=argparse.ArgumentParser();p.add_argument('dem');p.add_argument('--output-dir',default='data/derived')
    args=p.parse_args();out=Path(args.output_dir)
    t=time.perf_counter(); dem=LunarDEM(args.dem);load=time.perf_counter()-t
    prov=provenance(dem)
    cases=[('baseline',.5,80,50000,80,2),
           ('radial40',.5,40,50000,80,2),('radial20',.5,20,50000,80,2),
           ('radial10',.5,10,50000,80,2),('nearfield',.5,10,50000,10,2),
           ('range50',.5,20,50000,20,2),('range100',.5,20,100000,20,2),('range150',.5,20,150000,20,2),
           ('angular025',.25,20,150000,20,2),('angular0125',.125,20,150000,20,2),
           ('mast0',.5,20,150000,20,0),('mast4',.5,20,150000,20,4)]
    results={};summary={'load_seconds':load,'provenance':prov,'cases':{}}
    for name,az,dr,mx,mn,mast in cases:
        t=time.perf_counter()
        r=compute_horizon(dem,-89.466,-136.949,1946.9690908,mast,az,dr,mx,mn)
        elapsed=time.perf_counter()-t
        r['provenance']=prov;r['timing_seconds']={'compute':elapsed,'shared_initial_load':load}
        results[name]=r
        write_json(out/f'{name}_horizon.json',r)
        h=np.array([x['horizon_elevation_deg'] for x in r['rays']],float)
        summary['cases'][name]=dict(compute_seconds=elapsed,rays=len(h),
             complete_rays=sum(x['sampled_ray_complete'] for x in r['rays']),
             min_horizon_deg=float(h.min()),max_horizon_deg=float(h.max()),settings=r['settings'])
        print(name,summary['cases'][name],flush=True)
    summary['comparisons']={}
    for a,b in [('baseline','radial40'),('radial40','radial20'),('radial20','radial10'),
                ('radial10','nearfield'),('range50','range100'),('range100','range150'),
                ('range150','angular025'),('angular025','angular0125'),('mast0','range150'),('range150','mast4')]:
        summary['comparisons'][f'{a}__{b}']=compare(results[a],results[b])
    # Interstitial azimuths: do finer rays rise above interpolated coarse envelope?
    for a,b in [('range150','angular025'),('angular025','angular0125')]:
        coarse=results[a]['rays'];fine=results[b]['rays']
        ac=np.array([x['azimuth_deg'] for x in coarse]);hc=np.array([x['horizon_elevation_deg'] for x in coarse])
        af=np.array([x['azimuth_deg'] for x in fine]);hf=np.array([x['horizon_elevation_deg'] for x in fine])
        predicted=np.interp(af,np.append(ac,360),np.append(hc,hc[0]))
        err=hf-predicted
        summary['comparisons'][f'{a}__{b}']['interstitial_max_abs_linear_error_deg']=float(np.max(np.abs(err)))
    prof=cProfile.Profile();prof.enable()
    compute_horizon(dem,-89.466,-136.949,1946.9690908)
    prof.disable();prof.dump_stats(str(out/'baseline_profile.pstats'))
    stream=io.StringIO();pstats.Stats(prof,stream=stream).sort_stats('cumulative').print_stats(25)
    (out/'baseline_profile.txt').write_text(stream.getvalue())
    write_json(out/'validation_summary.json',summary)
    print('COMPARISONS',summary['comparisons'],flush=True)

if __name__=='__main__':main()
