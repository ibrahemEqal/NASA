import numpy as np
import pytest
from luna_ready.disk import constant_horizon_fraction,disk_fraction
from luna_ready.fragility import single_point_vertical_change
from luna_ready.geometry import terrain_elevation_deg

@pytest.mark.parametrize('offset,expected',[(-2,0),(-1,0),(0,.5),(1,1),(2,1)])
def test_planar_segment_limits(offset,expected):
    assert constant_horizon_fraction(offset,1)==pytest.approx(expected)

@pytest.mark.parametrize('elevation,expected',[(-3,0),(0,.5),(3,1)])
def test_spherical_disk_flat_horizon(elevation,expected):
    r=disk_fraction(359.9,elevation,.27,[0,90,180,270],[0,0,0,0])
    assert r['visible_area_lower_bound']==pytest.approx(expected,abs=1e-10)
    assert r['unknown_area_fraction']==0


def test_varying_horizon_half_disk_blocked():
    # Horizon changes across center azimuth; asymmetric skyline tested at wrap.
    az=np.array([0,1,179,180,181,359.])
    h=np.array([0,5,5,0,-5,-5.])
    r=disk_fraction(0,0,.27,az,h,n_radial=80,n_angular=512)
    assert r['visible_area_lower_bound']==pytest.approx(.5,abs=1e-6)


def test_disk_missing_horizon_is_unknown():
    r=disk_fraction(10,1,.27,[0,90,180,270],[np.nan,np.nan,np.nan,np.nan])
    assert r['visible_area_lower_bound']==0
    assert r['visible_area_upper_bound']==pytest.approx(1)


def test_single_point_inverse_geometry():
    r=single_point_vertical_change(3200,2200,1948.9690908,1.2)
    assert float(terrain_elevation_deg(3200,r['required_height_m'],1948.9690908))==pytest.approx(1.2,abs=1e-10)
