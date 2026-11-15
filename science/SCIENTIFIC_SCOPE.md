# Scientific scope and interpretation

## Terrain model

Coordinates are spherical planetocentric latitude and east-positive longitude.
The DEM reference radius is 1,737,400 m. The local vertical is radial and local
north follows the geographic meridian. Azimuth increases clockwise from north.
The trial site is Connecting Ridge 001, latitude -89.466, longitude -136.949;
this is not CR01, which is a different entry in the source table.

The nominal observer surface elevation is 1946.9690908 m, plus a 2 m radial mast.
A point sample reproduces that value, but is not an independent elevation check.

For arc distance d and central angle theta=d/R, terrain radius rt=R+h, and
observer radius ro=R+ho, the terrain angle is atan2(rt*cos(theta)-ro,
rt*sin(theta)). The implementation uses a numerically stable equivalent for
the vertical component. Rays follow great circles. No planar curvature shortcut
is used. A ridge is a controlling sampled point, not a resolved physical feature
with a certified footprint.

Four neighboring pixel-center elevations define each bilinear sample. All four
must be in the raster, finite and within the declared southern coverage. Strict
stencils are checked even if a corner's numerical interpolation weight is zero.
Pixels beyond -80 degrees are rejected despite any stored numeric elevation.
The entire DEM band is loaded once; interpolation is batched, without repeated
file reads or dropped invalid samples.

The finite range and ray spacing leave potential unsampled terrain. Close-range
1 m or 0.25 m numerical evaluation never changes the 80 m data resolution. The
unobserved immediate surface around the mast requires higher-resolution data.
No unknown terrain outside the supported map is silently assumed absent.

## Ephemerides

DE421 translational SPK, DE421 lunar binary PCK, a compatible lunar frame kernel,
leap-second kernel and generic body radii are used together. `spkcpo` uses the
actual observer position relative to Moon center, explicit `MOON_ME_DE421`,
frame locus `OBSERVER`, and reception `CN+S`. The state includes observer motion;
Earth parallax is not computed from Moon center. ENU uses the same radial basis
as the horizon. Light time and aberration settings are recorded.

Horizons is a separate service implementation using DE441 in the retained raw
responses. Its lunar surface coordinates use the DE421 mean-Earth convention.
Differences include ephemeris generation and Horizons relativistic corrections;
a small residual alone does not isolate an individual correction's error.
Independent checks cover five epochs per target, not all times or locations.

## Disks and time sampling

Disk integration samples uniform projected apparent area with exact unit-sphere
directions. The analytic segment helper is explicitly a small-angle planar
approximation; the real experiment uses numerical finite disks. A periodic,
piecewise-linear skyline is used between sampled azimuths. Missing skyline
segments produce unknown area, never assumed visibility.

Sun radius is 695700 km from the loaded PCK. Earth is not treated as a point;
concentric circles based on minimum/maximum PCK radii enclose its projected
ellipsoid. Visible-fraction shape enclosures also account for denominator area:
inner visible fraction*(rmin/rmax)^2 and outer fraction*(rmax/rmin)^2, clipped to
[0,1], with exact full/zero enclosure limits when the outer disk allows it.
Numerical quadrature prevents interpreting these estimates as rigorous certified
bounds. They omit atmosphere and do not locate an Earth ground station.

Partial disks have quadrature error; coarse/fine diagnostics are reported.
Center aberration is used for limb directions. Differential limb light time,
relativistic bending and full observer-dependent ellipsoid limb orientation are
not modeled. The disk-area fraction is not power or communication availability.

The seven-day experiment is a date-defined diagnostic. Thirty-minute samples
support runs and transition brackets, not exact rise/set times or guaranteed
continuous visibility. Window edges and missing states censor intervals.
No statistical uncertainty distributions are assigned.
