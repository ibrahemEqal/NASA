"""Load once, batch sampling; never perform per-sample raster I/O."""
from pathlib import Path
import numpy as np
import rasterio
from pyproj import CRS, Transformer
from .geometry import RADIUS_M

# Bit flags are independent; more than one reason can apply.
OUTSIDE_RASTER = 1
NODATA = 2
OUTSIDE_COVERAGE = 4


class LunarDEM:
    def __init__(self, path, southern_coverage_limit_deg=-80.):
        if not -90 < southern_coverage_limit_deg <= 0:
            raise ValueError("Invalid southern coverage limit")
        self.path = Path(path)
        self.coverage_limit = float(southern_coverage_limit_deg)
        with rasterio.open(path) as ds:
            if ds.count != 1 or ds.crs is None:
                raise ValueError("A georeferenced single-band DEM is required")
            self.crs = CRS(ds.crs)
            ell = self.crs.ellipsoid
            if not (abs(ell.semi_major_metre-RADIUS_M) < 0.001 and
                    abs(ell.semi_minor_metre-RADIUS_M) < 0.001):
                raise ValueError("Expected a 1737400 m lunar sphere")
            op = self.crs.coordinate_operation
            if not self.crs.is_projected or op is None or 'stereographic' not in op.method_name.lower():
                raise ValueError("Expected a polar stereographic projected CRS")
            params = {p.name.lower(): p.value for p in op.params}
            origin = params.get('latitude of natural origin', params.get('latitude of standard parallel'))
            if origin != -90:
                raise ValueError("Expected south-polar stereographic projection")
            if any(a.unit_name.lower() not in ('metre', 'meter') for a in self.crs.axis_info):
                raise ValueError("Projected coordinate units must be meters")
            self.transform = ds.transform
            if ds.transform.b != 0 or ds.transform.d != 0:
                raise ValueError("Rotated rasters are not supported")
            self.array = ds.read(1, masked=True).astype(np.float64).filled(np.nan)
            self.array = self.array*ds.scales[0]+ds.offsets[0]
            self.meta = dict(width=ds.width, height=ds.height, dtype=ds.dtypes[0],
                             resolution_m=list(ds.res), crs_wkt=ds.crs.to_wkt(),
                             bounds_m=list(ds.bounds), scale=ds.scales[0], offset=ds.offsets[0],
                             reference_radius_m=RADIUS_M, nodata=str(ds.nodata),
                             frame='MOON_ME (DE421), from NASA product 90 documentation')
        self.forward = Transformer.from_crs(self.crs.geodetic_crs, self.crs, always_xy=True)
        self.inverse = Transformer.from_crs(self.crs, self.crs.geodetic_crs, always_xy=True)

    def sample(self, latitude_deg, longitude_deg):
        """Bilinear interpolation between pixel centers, with strict 4-cell stencil.

        Reject every stencil touching invalid coverage or nodata, even if that
        corner's interpolation weight is zero. No extrapolation or gap filling.
        """
        lat, lon = np.broadcast_arrays(np.asarray(latitude_deg, float), np.asarray(longitude_deg, float))
        x, y = self.forward.transform(lon, lat)
        col = (np.asarray(x)-self.transform.c)/self.transform.a
        row = (np.asarray(y)-self.transform.f)/self.transform.e
        col, row = col-.5, row-.5
        finite = np.isfinite(col) & np.isfinite(row)
        ci = np.floor(np.where(finite, col, 0)).astype(np.int64)
        ri = np.floor(np.where(finite, row, 0)).astype(np.int64)
        inside = finite & (ci >= 0) & (ri >= 0) & (ci+1 < self.array.shape[1]) & (ri+1 < self.array.shape[0])
        flags = np.where(inside, 0, OUTSIDE_RASTER).astype(np.uint8)
        flags |= np.where((lat <= self.coverage_limit) & (lat >= -90) & np.isfinite(lon), 0, OUTSIDE_COVERAGE).astype(np.uint8)
        cc = np.clip(ci, 0, self.array.shape[1]-2)
        rr = np.clip(ri, 0, self.array.shape[0]-2)
        tx, ty = col-ci, row-ri
        out = np.zeros(lat.shape, dtype=float)
        for dr, dc, weight in [(0, 0, (1-tx)*(1-ty)), (0, 1, tx*(1-ty)),
                                (1, 0, (1-tx)*ty), (1, 1, tx*ty)]:
            z = self.array[rr+dr, cc+dc]
            cx = self.transform.c+self.transform.a*(cc+dc+.5)
            cy = self.transform.f+self.transform.e*(rr+dr+.5)
            _, corner_lat = self.inverse.transform(cx, cy)
            flags |= np.where(inside & ~np.isfinite(z), NODATA, 0).astype(np.uint8)
            flags |= np.where(inside & (np.asarray(corner_lat) > self.coverage_limit), OUTSIDE_COVERAGE, 0).astype(np.uint8)
            out += np.where(np.isfinite(z), z, 0)*weight
        return np.where(flags == 0, out, np.nan), flags
