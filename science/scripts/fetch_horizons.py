"""Independent JPL Horizons service comparison input; retain raw responses."""
import json,urllib.parse,urllib.request
from pathlib import Path
out=Path(__file__).resolve().parents[1]/'data/derived'
for name,target in [('sun','10'),('earth','399')]:
 params={'format':'json','COMMAND':f"'{target}'",'EPHEM_TYPE':"'OBSERVER'",'CENTER':"'coord@301'",
 'COORD_TYPE':"'GEODETIC'",'SITE_COORD':"'-136.949,-89.466,1.9489690908'",
 'START_TIME':"'2026-11-15 00:00'",'STOP_TIME':"'2026-11-16 00:00'",'STEP_SIZE':"'6 h'",
 'QUANTITIES':"'4,13,20'",'CSV_FORMAT':"'YES'",'EXTRA_PREC':"'YES'",'APPARENT':"'AIRLESS'",
 'ANG_FORMAT':"'DEG'",'SKIP_DAYLT':"'NO'",'ELEV_CUT':"'-90'"}
 url='https://ssd.jpl.nasa.gov/api/horizons.api?'+urllib.parse.urlencode(params)
 try:
  with urllib.request.urlopen(url,timeout=45) as f: data=json.load(f)
  (out/f'horizons_{name}_raw.json').write_text(json.dumps(data,indent=2))
  (out/f'horizons_{name}_request.json').write_text(json.dumps({'url':url,'parameters':params},indent=2))
  if 'error' in data: raise RuntimeError(data['error'])
  result=data['result']
  if '$$SOE' not in result: raise RuntimeError(result[-2000:])
  print(name,result[:700],result[result.index('Date__(UT') if 'Date__(UT' in result else result.index('$$SOE')-200:result.index('$$EOE')+6],flush=True)
 except Exception as e:
  print(name,type(e).__name__,str(e),flush=True)
