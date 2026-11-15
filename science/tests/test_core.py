import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from pyproj import CRS
from luna_ready.geometry import RADIUS_M, basis, destinations, terrain_elevation_deg
from luna_ready.dem import LunarDEM, NODATA, OUTSIDE_COVERAGE, OUTSIDE_RASTER
from luna_ready.horizon import radial_grid, summarize_ray, compute_horizon

CRS_MOON = CRS.from_proj4('+proj=stere +lat_0=-90 +lon_0=0 +k=1 +R=1737400 +units=m +type=crs')


def make_dem(tmp_path, array, transform=None):
    path = tmp_path/'test.tif'
    with rasterio.open(path, 'w', driver='GTiff', width=array.shape[1], height=array.shape[0],
                       count=1, dtype='float32', crs=CRS_MOON,
                       transform=transform or from_origin(-400,400,80,80), nodata=np.nan) as ds:
        ds.write(array.astype('float32'),1)
    return LunarDEM(path)


def test_sphere_horizon_analytic():
    d = np.linspace(1, 100000, 300)
    np.testing.assert_allclose(terrain_elevation_deg(d, 0, 0), -np.rad2deg(d/(2*RADIUS_M)), atol=1e-12)


def test_sphere_mast_tangent():
    h = 2.
    d = RADIUS_M*np.arccos(RADIUS_M/(RADIUS_M+h))
    expected = -np.rad2deg(np.arccos(RADIUS_M/(RADIUS_M+h)))
    assert float(terrain_elevation_deg(d,0,h)) == pytest.approx(expected,abs=1e-10)


def test_angle_matches_independent_cartesian():
    rng=np.random.default_rng(13)
    d=rng.uniform(1,150000,200); z=rng.uniform(-7000,7000,200); ho=1949.
    t=d/RADIUS_M
    v=np.stack([(RADIUS_M+z)*np.sin(t), (RADIUS_M+z)*np.cos(t)-(RADIUS_M+ho)],axis=1)
    np.testing.assert_allclose(terrain_elevation_deg(d,z,ho),np.rad2deg(np.arctan2(v[:,1],v[:,0])),atol=1e-8)


def test_great_circle_distance_and_bearing():
    lat0,lon0=-89.466,-136.949
    az=np.array([0,90,180,270])[:,None]; d=np.array([80,50000])[None,:]
    lat,lon=destinations(lat0,lon0,az,d)
    e,n,u=basis(lat0,lon0)
    p,l=np.deg2rad(lat),np.deg2rad(lon)
    v=np.stack([np.cos(p)*np.cos(l),np.cos(p)*np.sin(l),np.sin(p)],axis=-1)
    angle=np.arctan2(np.linalg.norm(np.cross(u,v),axis=-1),v@u)
    np.testing.assert_allclose(angle*RADIUS_M,np.broadcast_to(d,lat.shape),atol=1e-8)
    got=np.rad2deg(np.arctan2(v@e,v@n))%360
    np.testing.assert_allclose((got-az+180)%360-180,0,atol=1e-8)


def test_ridge_attribution_and_missing_sample():
    d=np.array([80.,160.,240.]); h=np.array([0.,100.,0.]); flags=np.zeros(3,dtype='uint8')
    r=summarize_ray(30,d,h,flags,2)
    assert r['controlling_distance_m']==160
    assert r['sampled_ray_complete']
    flags[2]=NODATA; h[2]=np.nan
    r=summarize_ray(30,d,h,flags,2)
    assert not r['sampled_ray_complete'] and r['nodata']
    assert r['controlling_elevation_m']==100
    assert r['first_invalid_distance_m']==240


def test_entire_ray_invalid():
    r=summarize_ray(0,np.array([80.]),np.array([np.nan]),np.array([NODATA]),2)
    assert r['horizon_elevation_deg'] is None and r['valid_sample_count']==0


def test_radial_endpoint():
    np.testing.assert_array_equal(radial_grid(201,80),[80,160,201])
    np.testing.assert_array_equal(radial_grid(200,80,10),[10,90,170,200])


def test_bilinear_plane_and_crs_round_trip(tmp_path):
    rows,cols=np.indices((10,10))
    dem=make_dem(tmp_path,rows*3+cols*2+100.)
    x=dem.transform.c+4.25*dem.transform.a; y=dem.transform.f+5.75*dem.transform.e
    lon,lat=dem.inverse.transform(x,y)
    xx,yy=dem.forward.transform(lon,lat)
    # PROJ round-trip near the pole: 10 micrometer acceptance in projected meters.
    assert xx==pytest.approx(x,abs=1e-5) and yy==pytest.approx(y,abs=1e-5)
    z,f=dem.sample(lat,lon)
    assert int(f)==0
    assert z==pytest.approx(100+3*5.25+2*3.75,abs=1e-7)


def test_nodata_in_stencil_is_not_zero(tmp_path):
    a=np.ones((10,10)); a[4,4]=np.nan
    dem=make_dem(tmp_path,a)
    x=dem.transform.c+4.8*dem.transform.a; y=dem.transform.f+4.8*dem.transform.e
    lon,lat=dem.inverse.transform(x,y)
    z,f=dem.sample(lat,lon)
    assert np.isnan(z) and int(f)&NODATA


def test_outside_raster(tmp_path):
    dem=make_dem(tmp_path,np.zeros((10,10)))
    lon,lat=dem.inverse.transform(1000,1000)
    z,f=dem.sample(lat,lon)
    assert np.isnan(z) and int(f)&OUTSIDE_RASTER


def test_coverage_stencil_straddling_boundary(tmp_path):
    # All finite data: scientific coverage still rejects the northern corner.
    rho=2*RADIUS_M*np.tan(np.deg2rad(5))
    dem=make_dem(tmp_path,np.ones((10,10)),from_origin(-400,rho+400,80,80))
    lon,lat=dem.inverse.transform(0,rho-10)
    assert lat < -80
    z,f=dem.sample(lat,lon)
    assert np.isnan(z) and int(f)&OUTSIDE_COVERAGE
    lon,lat=dem.inverse.transform(0,rho-200)
    z,f=dem.sample(lat,lon)
    assert float(z)==pytest.approx(1) and int(f)==0


def test_chunk_equivalence(tmp_path):
    dem=make_dem(tmp_path,np.zeros((100,100)),from_origin(-4000,4000,80,80))
    args=dict(latitude_deg=-89.99,longitude_deg=0,observer_elevation_m=0,mast_height_m=2,
              max_range_m=800,azimuth_step_deg=30,radial_step_m=40)
    a=compute_horizon(dem,chunk_rays=1,**args)
    b=compute_horizon(dem,chunk_rays=7,**args)
    assert a['rays']==b['rays'] and a['sampled_rays_complete']
    assert not a['physical_horizon_certified']


@pytest.mark.parametrize('distance',[0,-10,np.pi*RADIUS_M])
def test_invalid_distances(distance):
    with pytest.raises(ValueError): terrain_elevation_deg(distance,0,0)
