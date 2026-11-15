import csv,json
from pathlib import Path
import numpy as np
from luna_ready.ephemeris import load_kernels,direction
from luna_ready.pipeline import write_json
from luna_ready.provenance import sha256
root=Path(__file__).resolve().parents[1];out=root/'data/derived';paths=load_kernels(root/'data/kernels')
records=[]
for target in ['SUN','EARTH']:
 for day,hour in [(15,0),(15,6),(15,12),(15,18),(16,0)]:
  records.append(direction(target,f'2026-11-{day}T{hour:02}:00:00',-89.466,-136.949,1948.9690908))
write_json(out/'spice_directions.json',dict(records=records,kernels=[dict(filename=p.name,sha256=sha256(p)) for p in paths],
    description='Validation epochs only, not a mission recommendation; DE421 ephemeris and MOON_ME_DE421 observer frame'))
comparisons=[]
for name in ['sun','earth']:
 path=out/f'horizons_{name}_raw.json'
 if not path.exists():continue
 raw=json.loads(path.read_text())['result']
 rows=list(csv.reader(raw.split('$$SOE')[1].split('$$EOE')[0].strip().splitlines()))
 print(name,'HORIZONS ROWS',rows,flush=True)
 for row,sp in zip(rows,[r for r in records if r['target']==name.upper()]):
  # Expected columns: date, solar marker, interfering marker, az, el, diameter, range, range-rate.
  az,el,diam,range_au=map(float,[row[3],row[4],row[5],row[6]])
  da=(sp['azimuth_deg']-az+180)%360-180;de=sp['elevation_deg']-el
  comparisons.append(dict(target=name,utc=sp['utc'],horizons_azimuth_deg=az,horizons_elevation_deg=el,
    delta_azimuth_deg=da,delta_elevation_deg=de,
    delta_range_km=sp['range_km']-range_au*149597870.7,
    horizons_angular_diameter_arcsec=diam,
    interpretation='Service comparison: SPICE DE421 vs Horizons documented ephemeris; settings and raw header retained'))
write_json(out/'spice_horizons_comparison.json',dict(comparisons=comparisons))
print(json.dumps(comparisons,indent=2))
