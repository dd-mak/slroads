# Sierra Leone Road Network · #31DayOSMChallenge

Interactive web map of every OpenStreetMap road in Sierra Leone (MapLibre GL JS, static site).
Speed limits · street lighting · surface · track grade · railway overlay · dark mode · GeoJSON/CSV download.

## How data loads
1. **Saved snapshot (default).** The page reads `data/*.geojson` from this repo. Fast, no OSM server needed. The sidebar shows the snapshot date.
2. **Reload live.** The button *Reload live from OpenStreetMap* fetches the newest data from Overpass in the browser.
3. **Fallback.** If `data/` is empty or missing, the page loads live from OSM automatically.

## Keep the snapshot fresh
- **Automatic:** `.github/workflows/update-data.yml` runs monthly, downloads the data and commits it.
- **Manual:** repo → *Actions* → *Update road data* → *Run workflow* (no local Python needed). The first run creates `data/`.
- **Local:** `python scripts/build_data.py`, then commit `data/`.

## Deploy
Settings → Pages → Deploy from branch → `main` / root.

Data © OpenStreetMap contributors (ODbL). Basemap © CARTO.
