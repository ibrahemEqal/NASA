import json
import time
from pathlib import Path
from .dem import LunarDEM
from .horizon import compute_horizon
from .provenance import provenance


def write_json(path, result):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


def compute_horizon_from_dem(path, output, southern_coverage_limit_deg=-80., **settings):
    t = time.perf_counter()
    dem = LunarDEM(path, southern_coverage_limit_deg)
    loaded = time.perf_counter()
    result = compute_horizon(dem, **settings)
    computed = time.perf_counter()
    result['provenance'] = provenance(dem)
    result['timing_seconds'] = dict(load=loaded-t, compute=computed-loaded,
                                    provenance=time.perf_counter()-computed)
    write_json(output, result)
    return result
