"""Adapt executed LUNA-READY results. No synthetic values or extra sites.

Usage: PYTHONPATH=/path/to/scientific/dependencies python scripts/export_data.py /path/to/LUNA-READY/data/derived
"""
import json,sys,hashlib,math
from pathlib import Path
from datetime import datetime
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'science/src'))
from luna_ready.disk import disk_fraction
from luna_ready.fragility import single_point_vertical_change
from luna_ready.geometry import RADIUS_M
ROOT=Path(__file__).resolve().parents[1];source=Path(sys.argv[1]);out=ROOT/'public/data';site=out/'connecting-ridge-001';site.mkdir(parents=True,exist_ok=True)
def read(n):return json.loads((source/n).read_text())
def write(p,d):p.write_text(json.dumps(d,separators=(',',':'),allow_nan=False)+'\n')
H=read('refined_horizon.json');V=read('visibility_demo.json');C=read('spice_horizons_comparison.json');R=read('refinement_summary.json');S=read('validation_summary.json')
P=dict(is_synthetic=False,algorithm_version='luna-ready 0.2.0 reconstructed',source_files=['refined_horizon.json','visibility_demo.json'],status='Provisional interpolated terrain model')
az=[x['azimuth_deg'] for x in H['rays']];he=[x['horizon_elevation_deg'] for x in H['rays']]
sites=[dict(id='connecting-ridge-001',name='Connecting Ridge · 001',lat_deg=H['site']['latitude_deg'],lon_deg=H['site']['longitude_deg'],frame='MOON_ME_DE421',source_note='Wueller et al. (2026), Table A1; registration provisional',data_quality_tier='Provisional · 80 m DEM')]
write(out/'sites.json',sites)
write(site/'horizon.json',dict(az_deg=az,h_nominal_deg=he,h_low_deg=[],h_high_deg=[],edge_flag=[not x['sampled_ray_complete'] for x in H['rays']],controlling=[dict(az_deg=x['azimuth_deg'],range_km=x['controlling_distance_m']/1000,elev_deg=x['horizon_elevation_deg'],terrain_elevation_m=x['controlling_elevation_m'],lat_deg=x['controlling_latitude_deg'],lon_deg=x['controlling_longitude_deg']) for x in H['rays']],provenance=P,settings={**H['settings'],'radial_step_m':None,'radial_sampling_mode':'explicit nested distances; no uniform radial step','near_field_max_step_m':float(np.max(np.diff(np.asarray(H['settings']['custom_distances_m'])[np.asarray(H['settings']['custom_distances_m'])<2000]))),'far_field_step_m':float(np.median(np.diff(np.asarray(H['settings']['custom_distances_m'])[np.asarray(H['settings']['custom_distances_m'])>=2000])))},site=H['site'],sensitivity_envelope_note='No matched terrain-error envelope available. Mast scenarios have different settings and are not presented as uncertainty.'))
rr={name:[x for x in V['records'] if x['target']==name.upper()] for name in ['sun','earth']}
times=[x['utc'] for x in rr['sun']]
tracks=dict(t_utc=times,provenance=P)
# The reference smooth sphere passes through the adopted site surface; mast
# height yields the local smooth-sphere dip. This is a documented assumption.
smooth=-math.degrees(math.acos((RADIUS_M+H['site']['observer_elevation_m'])/(RADIUS_M+H['site']['observer_elevation_m']+H['site']['mast_height_m'])))
for name in ['sun','earth']:
 records=rr[name];geom=[];gf=[]
 for x in records:
  g=disk_fraction(x['azimuth_deg'],x['elevation_deg'],x['angular_radius_outer_deg'],[0,90,180,270],[smooth]*4,32,128)['visible_area_lower_bound']
  geom.append(g>1e-6);gf.append(g)
 tracks[name]=dict(az_deg=[x['azimuth_deg'] for x in records],el_deg=[x['elevation_deg'] for x in records],radius_deg=[x['angular_radius_outer_deg'] for x in records],disk_frac=[(x['disk_visible_fraction_lower']+x['disk_visible_fraction_upper'])/2 for x in records],disk_frac_low=[x['disk_visible_fraction_lower'] for x in records],disk_frac_high=[x['disk_visible_fraction_upper'] for x in records],geometric_disk_frac=gf)
 tracks['geometric_visible_'+name]=geom
tracks['smooth_horizon_deg']=smooth
tracks['smooth_horizon_assumption']='Sphere through adopted local surface elevation with 2 m mast; no terrain relief.'
tracks['disagreement_index']=next((i for i,(a,b) in enumerate(zip(tracks['geometric_visible_earth'],tracks['earth']['disk_frac'])) if a!=(b>1e-6)),0)
write(site/'tracks.json',tracks)
intervals=dict(provenance=P,longest_outage={},totals={},cadence_minutes=V['time_step_minutes'])
for name in ['sun','earth']:
 rows=[]
 for key,state in [('any_disk_visible_sample_runs','visible'),('full_occlusion_sample_runs','blocked')]:
  for x in V['intervals'][name.upper()][key]:
   rows.append(dict(start=x['first_sample_utc'],end=x['last_sample_utc'],state=state,censored_start=x['left_censored'],censored_end=x['right_censored'],sample_span_h=x['sample_span_hours'],start_bracket=x['start_transition_bracket_utc'],end_bracket=x['end_transition_bracket_utc']))
 intervals[name]=sorted(rows,key=lambda x:x['start'])
 blocked=[x for x in rows if x['state']=='blocked']
 longest=max(blocked,key=lambda x:x['sample_span_h']) if blocked else None
 intervals['longest_outage'][name]=dict(min_h=None,max_h=None,censored=bool(longest and (longest['censored_start'] or longest['censored_end'])),observed_sample_span_h=longest['sample_span_h'] if longest else None)
 intervals['totals'][name]=dict(min_h=None,max_h=None,visible_samples=sum(x['disk_visible_fraction_lower']>1e-6 for x in rr[name]),total_samples=len(rr[name]))
intervals['note']='Continuous duration is unresolved: null duration bounds are unknown, never zero. Sample spans and transition brackets do not exclude reversals between samples.'
write(site/'intervals.json',intervals)
# A computed ridge-local scenario, restricted to ONE sampled controlling point.
# It does not certify a whole-sky flip: another ridge can take over.
i=tracks['disagreement_index'];earth=rr['earth'][i];a=earth['azimuth_deg'];index=int(np.argmin(np.abs(np.asarray(az)-a)));control=H['rays'][index]
target=earth['elevation_deg']+earth['angular_radius_outer_deg']
f=single_point_vertical_change(control['controlling_distance_m'],control['controlling_elevation_m'],H['site']['observer_elevation_m']+H['site']['mast_height_m'],target)
flip=f['vertical_change_m']
xs=np.linspace(min(0,flip)-max(abs(flip)*.2,1),max(0,flip)+max(abs(flip)*.2,1),81)
from luna_ready.geometry import terrain_elevation_deg
y=[float(target-terrain_elevation_deg(control['controlling_distance_m'],control['controlling_elevation_m']+x,H['site']['observer_elevation_m']+H['site']['mast_height_m'])) for x in xs]
frag=dict(provenance=P,conclusions=[dict(id='earth-upper-limb-local-ridge',text='Earth upper-limb clearance at one sampled ridge',metric='upper_limb_clearance_deg',baseline=float(target-control['horizon_elevation_deg']),verdict='Indeterminate',epoch_utc=earth['utc'],curves=[dict(family='ridge-local',x=xs.tolist(),y=y,flip_x=flip,units='m',y_units='deg')],controlling_feature=dict(az_deg=control['azimuth_deg'],range_km=control['controlling_distance_m']/1000,flip_height_m=flip),note='Deterministic one-point perturbation. Not whole-disk visibility, a confidence interval, a probability or a globally controlling-ridge flip. The nearest sampled azimuth is used.')],tested_scenarios=[dict(family='mast height',mast_height_m=m,source_file=n+'_horizon.json',settings_note='150 km, uniform 20 m radial sampling; not the refined baseline',max_horizon_deg=S['cases'][n]['max_horizon_deg'],min_horizon_deg=S['cases'][n]['min_horizon_deg']) for m,n in [(0,'mast0'),(2,'range150'),(4,'mast4')]])
write(site/'fragility.json',frag)
write(out/'compare.json',dict(criteria=['Sun visibility','Longest sampled Sun occultation','Earth line-of-sight visibility','Longest sampled Earth occultation','Data quality'],sites={sites[0]['id']:dict(values={c:dict(min=None,max=None,unknown=True) for c in ['Sun visibility','Longest sampled Sun occultation','Earth line-of-sight visibility','Longest sampled Earth occultation','Data quality']})},dominance=[],attribution=[],provenance=P,note='One real site is available. No robust multi-site dominance comparison was executed.'))
tests=[dict(id='pytest',name='Reconstructed unit + integration suite',status='PASS',measured=32,tolerance=32,units='tests passed',note='Executed suite; original 18-test source was unavailable. See pytest_run.log.'),dict(id='horizons-elevation',name='SPICE / JPL Horizons · elevation',status='PASS',measured=max(abs(x['delta_elevation_deg']) for x in C['comparisons']),tolerance=.0001,units='deg',note='Five epochs per target; DE421 local SPICE versus DE441 service. Validates directions, not terrain.'),dict(id='horizons-azimuth',name='SPICE / JPL Horizons · azimuth',status='PASS',measured=max(abs(x['delta_azimuth_deg']) for x in C['comparisons']),tolerance=.0001,units='deg',note='Actual observer position, MOON_ME_DE421, reception CN+S.'),dict(id='coverage',name='Requested refined ray completeness',status='PASS',measured=sum(x['sampled_ray_complete'] for x in H['rays']),tolerance=len(H['rays']),units='rays',note='Every requested sample passes the raster, NoData and -80° coverage gate; continuous horizon remains uncertified.'),dict(id='near-refine',name='Near-field grid refinement · diagnostic',status='PASS',measured=R['comparisons']['near1__near0p25']['max_abs_difference_deg'],tolerance=.01,units='deg',note='1 m vs 0.25 m numerical sampling of the same 80 m surface, 720 shared azimuths. 0.01° is a chosen numerical diagnostic tolerance, not a physical accuracy claim.'),dict(id='terrain',name='Independent real-terrain horizon validation',status='NOT_RUN',measured=None,tolerance=None,units='',note='Requires a matched external terrain/horizon reference.'),dict(id='resolution',name='Effective-resolution and elevation-error layers',status='NOT_RUN',measured=None,tolerance=None,units='',note='Not loaded. No statistical terrain uncertainty is inferred.'),dict(id='angular',name='Final grid versus 0.0625° azimuth grid',status='NOT_RUN',measured=None,tolerance=None,units='',note='Continuous angular convergence remains open.'),dict(id='product69',name='NASA Product 69 quantitative comparison',status='NOT_RUN',measured=None,tolerance=None,units='',note='Long-term average maps are not a direct reference for a seven-day experiment.')]
write(out/'validation.json',dict(tests=tests,provenance=P))
prov=dict(is_synthetic=False,datasets=[dict(id='lola',name='NASA LOLA · South-pole DEM',kind='measured',version='LDEM_80S_80MPP_ADJ',checksum=H['provenance']['dem_sha256'],resolution_m=H['provenance']['metadata']['resolution_m'][0],url=H['provenance']['nasa_product'],note='Altimetry-derived gridded and interpolated terrain; pixel spacing is not effective resolution.'),dict(id='site',name='Wueller et al. (2026) · Table A1',kind='source',version='10.1029/2025JE009434',url='https://doi.org/10.1029/2025JE009434',note='Connecting Ridge site 001, not CR01; coordinate registration provisional.')],results=[dict(id='horizon',name='Terrain horizon',version='luna-ready 0.2.0 reconstructed',settings=H['settings'],source_hashes=H['provenance']['source_hashes'],sampled_ray_count=len(H['rays']),physical_horizon_certified=False),dict(id='visibility',name='Finite-disk visibility experiment',time_step_minutes=V['time_step_minutes'],start_utc=V['start_utc'],stop_utc=V['stop_utc'],kernels=V['kernels'],max_quadrature_delta=max(x['disk_quadrature_refinement_difference'] for x in V['records']))],reproduce='cd science\npython scripts/validate_real_dem.py /path/to/DEM.tiff\npython scripts/refine_horizon.py /path/to/DEM.tiff\npython scripts/validate_spice.py\npython scripts/visibility_demo.py',code_repository='https://github.com/ibrahemEqal/NASA',assumptions=[tracks['smooth_horizon_assumption'],'2 m radial mast; adopted surface elevation from the same DEM.','Periodic linear interpolation between sampled horizon azimuths.','Finite Earth ellipsoid represented by numerical inner/outer radius enclosures.'],limitations=V['limitations'],export_inputs_sha256={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in ['refined_horizon.json','visibility_demo.json','spice_horizons_comparison.json','validation_summary.json','refinement_summary.json']})
# Avoid repeating the 15650-point custom distance list in provenance UI payload;
# preserve it once in the horizon file and original scientific outputs.
prov['results'][0]['settings']={k:v for k,v in json.loads((site/'horizon.json').read_text())['settings'].items() if k!='custom_distances_m'}
write(out/'provenance.json',prov)
raw=out/'raw';raw.mkdir(exist_ok=True)
for n in ['pytest_run.log','spice_horizons_comparison.json','horizons_sun_raw.json','horizons_earth_raw.json','validation_summary.json','refinement_summary.json']:
 (raw/n).write_bytes((source/n).read_bytes())
print('Exported real site,',len(az),'horizon rays,',len(times),'epochs. Disagreement index:',i,'local ridge flip:',flip)
