"""Stage 8: two physical bounds for the municipality of Montréal, from the length of its streets.

Source: Ville de Montréal, géobase (street segments, open data, file of October 14, 2026; CC BY 4.0). Segments of
type autoroute, pont, tunnel, voie (ramps and service lanes) and ruelle are left out. A segment's two sides are
counted separately and only the sides inside the municipality of Montréal are kept.

  curb bound      every metre of both curbs of every street used for parking, at 5.0 to 6.0 m per vehicle. No
                  deduction is made for intersections, driveways, hydrants, bus stops or signs, so the number of
                  vehicles that can really be parked on the street is lower, by an amount not measured here.
  standstill bound  every vehicle on the roadway at the same moment, nose to tail, at 6.0 to 8.0 m per vehicle.
                  The géobase gives no number of lanes: one lane is counted for a one-way segment and two for a
                  two-way segment, which understates the wider streets. Traffic stops flowing long before this.

Both are bounds under stated assumptions, not measurements of parking or of congestion. The spacing figures are
assumptions given as ranges. Vehicles kept off the street (garages, driveways, lots) are not in either bound.

Output: derived/tables/street_space_bounds.csv
Run:  ~/.venvs/omd/bin/python scripts/street_space.py
"""
import os
from pathlib import Path

import geopandas as gpd
import pandas as pd

import paths

GEOBASE = Path(os.environ.get("THIRD_PARTY", Path.home() / "Terrebonne-data/third-party")) / "montreal-opendata/geobase_2026-10-14.json"
OUT = ("autoroute", "pont", "tunnel", "voie", "ruelle")


def main():
    g = gpd.read_file(GEOBASE).to_crs(32188)
    g["m"] = g.geometry.length
    g = g[~g.TYP_VOIE.isin(OUT)]
    sides = (g.LIM_GCH == "Montréal").astype(int) + (g.LIM_DRT == "Montréal").astype(int)
    curb_m = (g.m * sides).sum()
    inside = g[sides > 0]
    centre_m = (inside.m * sides[sides > 0] / 2).sum()
    lanes_m = (inside.m * sides[sides > 0] / 2 * inside.SENS_CIR.map(lambda s: 2 if s == 0 else 1)).sum()
    t = pd.read_csv(paths.TABLES / "type_by_municipality.csv", dtype={"muni_code": str})
    au = t[(t.muni_code == "66023") & (t.vtype == "AU")].set_index("year").n
    rows = [{"quantity": "street centreline in the municipality of Montréal (km)", "value": round(centre_m / 1000), "assumption": "géobase of October 14, 2026; autoroutes, bridges, tunnels, ramps and lanes left out"},
            {"quantity": "curb, both sides (km)", "value": round(curb_m / 1000), "assumption": "each side inside the municipality"},
            {"quantity": "lanes, at least (km)", "value": round(lanes_m / 1000), "assumption": "one lane for a one-way segment, two for a two-way segment"}]
    for L in (5.0, 5.5, 6.0):
        rows.append({"quantity": f"curb bound: vehicles at {L} m each", "value": round(curb_m / L), "assumption": "every metre of curb, no deduction"})
    for L in (6.0, 7.0, 8.0):
        rows.append({"quantity": f"standstill bound: vehicles at {L} m each", "value": round(lanes_m / L), "assumption": "every lane full, nose to tail"})
    rows.append({"quantity": "automobiles and light trucks registered, 2024 (inferred)", "value": round(au[2024]), "assumption": "type inferred"})
    rows.append({"quantity": "the same as a share of the curb bound at 5.5 m (%)", "value": round(100 * au[2024] / (curb_m / 5.5), 1), "assumption": ""})
    rows.append({"quantity": "the same as a share of the standstill bound at 7.0 m (%)", "value": round(100 * au[2024] / (lanes_m / 7.0), 1), "assumption": ""})
    d = pd.DataFrame(rows); d.to_csv(paths.TABLES / "street_space_bounds.csv", index=False)
    pd.set_option("display.width", 200); pd.set_option("display.max_colwidth", 90); print(d.to_string(index=False))
    print(inside.groupby("CLASSE").m.sum().div(1000).round(0).to_dict(), "segments", len(inside))


if __name__ == "__main__":
    main()
