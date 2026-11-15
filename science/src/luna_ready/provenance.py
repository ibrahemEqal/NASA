import hashlib
import importlib.metadata
import platform
from datetime import datetime, timezone
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(8*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def provenance(dem):
    root = Path(__file__).parent
    return dict(created_utc=datetime.now(timezone.utc).isoformat(),
                code_origin='reconstructed v0.2.0; original v0.1.1 unavailable',
                source_hashes={p.name:sha256(p) for p in sorted(root.glob('*.py'))},
                dem_filename=dem.path.name, dem_sha256=sha256(dem.path),
                metadata=dem.meta, python=platform.python_version(),
                packages={n:importlib.metadata.version(n) for n in ['numpy','rasterio','pyproj']},
                nasa_product='https://pgda.gsfc.nasa.gov/products/90',
                nasa_data='https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_80MPP_ADJ.TIF',
                site_source='https://doi.org/10.1029/2025JE009434, Wueller et al. (2026), Table A1')
