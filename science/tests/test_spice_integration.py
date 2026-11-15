"""Real-kernel integration tests; absent kernels cause explicit skips."""
import json
from pathlib import Path
import numpy as np
import pytest
spice=pytest.importorskip('spiceypy')
from luna_ready.ephemeris import load_kernels,direction,FRAME,KERNELS
from luna_ready.geometry import basis,RADIUS_M
ROOT=Path(__file__).resolve().parents[1]
pytestmark=pytest.mark.skipif(not all((ROOT/'data/kernels'/p).exists() for p in KERNELS),reason='NAIF kernels not downloaded')

@pytest.mark.parametrize('target',['SUN','EARTH'])
def test_geometric_topocentric_against_cartesian_subtraction(target):
    load_kernels(ROOT/'data/kernels');utc='2026-11-15T00:00:00'
    r=direction(target,utc,-89.466,-136.949,1948.9690908,'NONE');et=spice.str2et(utc)
    _,_,up=basis(-89.466,-136.949);obs=(RADIUS_M+1948.9690908)/1000*up
    center=spice.spkpos(target,et,'J2000','NONE','MOON')[0]
    rot=spice.pxform(FRAME,'J2000',et)
    independent=rot.T@(center-rot@obs)
    np.testing.assert_allclose(r['topocentric_vector_km'],independent,atol=2e-7,rtol=1e-14)


def test_saved_horizons_service_comparison():
    p=ROOT/'data/derived/spice_horizons_comparison.json'
    if not p.exists():pytest.skip('Saved Horizons responses missing')
    data=json.loads(p.read_text())['comparisons']
    assert len(data)==10
    assert max(abs(r['delta_elevation_deg']) for r in data)<1e-4
    assert max(abs(r['delta_azimuth_deg']) for r in data)<1e-4
