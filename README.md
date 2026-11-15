# LUNA-READY

A bilingual, offline-capable lunar visibility observatory. Built with Vite,
React, TypeScript, Tailwind CSS, native SVG plots and Framer Motion.

**Real data is the default.** This app uses the executed, reconstructed
LUNA-READY v0.2.0 experiment at Connecting Ridge **001**, not CR01.
It never treats geometric visibility as actual power, radio-link availability
or landing safety. It makes no NASA endorsement or novelty claim.

## Run and build

```bash
npm ci
npm run dev
npm test
npm run build
npm run preview
```

`dist/` is a static website. Deploy its contents on any static host. `base: './'`
supports a repository subpath such as GitHub Pages.

**Direct offline use:** open `dist/offline.html` in a browser. All application
code, styles and required JSON are embedded; it needs no server, CDN, fonts or
external API. The ordinary hosted version also caches assets with a service
worker after its first successful load. External source links require internet.

- `?judge=1` starts the five-step tour and hides advanced preferences.
- English is the default; Arabic mirrors the layout while charts remain LTR.
- Light/dark theme and language preferences stay in local browser storage.
- Keyboard: use the time slider's arrow/Home/End keys, tour left/right arrows,
  and Escape to close dialogs. Dialogs contain keyboard focus.

## Scientific data

All scientific results are loaded through `loadSiteData(siteId)` in
`src/data.ts`. Zod validates the full file set before rendering. Components do
not fetch files. Missing files and malformed arrays return typed errors rather
than substitute data. No runtime calculation calls an external service.

```
public/data/sites.json
public/data/connecting-ridge-001/horizon.json
public/data/connecting-ridge-001/tracks.json
public/data/connecting-ridge-001/intervals.json
public/data/connecting-ridge-001/fragility.json
public/data/compare.json
public/data/validation.json
public/data/provenance.json
```

The contract follows the supplied brief, with explicit honesty extensions:

- `h_low_deg` and `h_high_deg` are empty when a matched terrain sensitivity
  envelope has not been computed. The UI says so; it does not fabricate a band.
- `disk_frac_low/high` are numerical shape-enclosure estimates for the Earth
  limb, not terrain confidence bounds. Midpoints are used for the central
  timeline curve; the inspector shows the available range.
- Unknown continuous-duration bounds are **null**, not zero. Metrics show
  visible sampled epochs and below-threshold sampled spans. Those are not
  guaranteed continuous durations. Window-edge runs are visibly censored.
- The final horizon uses an explicit nested distance grid. Its uniform step is
  **null**; 80 m pixel spacing is not a uniform radial step or effective terrain
  resolution. The exact custom distance array remains in `horizon.json`.
- A local flip margin changes **one sampled terrain point**. It does not assert
  that the entire Earth disk or whole-sky horizon flips at that perturbation.
- Only one real site is available; multi-site dominance remains unknown.
- Mast-height scenarios have different settings from the refined visibility
  run. Selecting an uncomputed mast height shows an explicit empty state.

### Replace or add real data

Add a site entry and its four site JSON files, preserving units, array lengths,
monotonic UTC times, finite values and provenance. Update comparison and
validation files only with executed results. Keep `is_synthetic:false` only for
actual, traceable data. Schema definitions are in `src/data.ts`.

The current export can be reproduced from the original scientific outputs:

```bash
python -m pip install -e 'science[test,science]'
python scripts/export_data.py /path/to/LUNA-READY/data/derived
```

The 181 MiB NASA DEM and binary NAIF kernels are not duplicated in this web
repository. The original research bundle contains the executed outputs and
kernels. Kernel sources/checksums are also preserved in
`science/data/kernels/manifest.json`. The science engine and experiment scripts
are under `science/`. Run those scripts **from `science/`** after supplying the
DEM and kernels. Consult `science/SCIENTIFIC_SCOPE.md`.

### Synthetic development fixtures

```bash
node scripts/generate-synthetic.mjs
```

Open `?synthetic=1` to load the separately generated `/data/synthetic/` fixtures.
Every synthetic mode—including malformed or mixed provenance—retains a
persistent red **SYNTHETIC PLACEHOLDER DATA - NOT NASA DATA** warning. No
synthetic site or result is promoted into the real catalog. Synthetic functions
are UI fixtures, not a scientific model. They are not used on the default page.

## Verification

`npm test` covers schema acceptance, typed missing/malformed failures,
finite-disk fraction bounds, provenance flags, source checksum preservation,
real model disagreement and null unknown durations. The displayed **32 passed**
refers to the earlier scientific Python suite; the web tests are a separate
suite. Raw scientific validation logs and Horizons responses are included in
`public/data/raw/`. Manual browser checks are documented in `QA.md`.

## Sources and limitations

- NASA LOLA DEM: https://pgda.gsfc.nasa.gov/products/90
- Site coordinates: Wueller et al. (2026), Table A1,
  https://doi.org/10.1029/2025JE009434
- NAIF topocentric geometry:
  https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/cspice/spkcpo_c.html
- JPL Horizons independent direction comparison:
  https://ssd.jpl.nasa.gov/horizons/manual.html

The interpolated 80 m terrain horizon is **provisional**. Its requested samples
are complete, but a continuous physical horizon has not been certified.
Independent real-terrain validation, effective-resolution/error layers, final
angular refinement, exact event times, and multiple matched sites remain open.

There is no backend, database, telemetry, tracking or required network API.
