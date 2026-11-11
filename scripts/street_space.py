"""Stage 8: two physical bounds for the municipality of Montréal: where its automobiles could stand on the street.

DRIVING BOUND: every travel lane full, nose to tail.
  Network and lane counts: OpenStreetMap (© OpenStreetMap contributors, ODbL; Geofabrik extract of November 11, 2026),
  ways tagged motorway, trunk, primary, secondary, tertiary (and their links), residential, unclassified and
  living_street, inside the municipality; ways closed to motor vehicles (access=no/private, motor_vehicle=no) and
  service ways (lanes of parking lots, driveways, back lanes) left out. Lanes: the `lanes` tag (travel lanes, both
  directions for a two-way way); where the tag is missing, the median of the tagged ways of the same class and
  direction. Vehicles at 6.0 to 8.0 m each (an assumption).

PARKING BOUND: every legal metre of curb used for parking.
  Curb: Ville de Montréal, géobase of October 14, 2026 (CC BY 4.0), both sides of every street inside the
  municipality; autoroutes, bridges, tunnels, ramps and back lanes left out. Deducted: 5 m at each end of each
  block face (an assumption for the clearance at intersections), and the stretches where the City's sign inventory
  (« Signalisation - stationnement », file of October 23, 2026, CC BY 4.0) shows stopping or parking forbidden at
  all times (« \\A EN TOUT TEMPS », « \\P EN TOUT TEMPS »). A sign governs the stretch from its pole to the next
  pole in the direction of its arrow (half the stretch on each side when it has no arrow). The inventory is
  complete only in some boroughs: the share forbidden there is applied to the others (an assumption). Not deducted:
  driveways, hydrants, bus stops, and restrictions by hour, day or permit. Vehicles at 5.0 to 6.0 m each.

Both are bounds under stated assumptions, not measurements of parking or of congestion: vehicles kept off the street
are in neither, the registered vehicles are never all on the road at once, vehicles from elsewhere are not counted,
and traffic stops flowing well before every lane is full.

Outputs (derived/tables/): street_space_bounds.csv, street_lanes_by_class.csv, street_curb_by_borough.csv
Run:  ~/.venvs/omd/bin/python scripts/street_space.py
"""
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import line_locate_point

import paths

TP = Path(os.environ.get("THIRD_PARTY", Path.home() / "Terrebonne-data/third-party"))
GEOBASE = TP / "montreal-opendata/geobase_2026-10-14.json"
SIGNS = TP / "montreal-opendata/signalisation-2026-10-23/signalisation_stationnement.csv"
LIMITS = TP / "montreal-opendata/limadmin/limadmin.json"
OSM = TP / "osm/quebec-geofabrik-2026-11-11/montreal_highways.gpkg"
CLASSES = {"motorway": "autoroute", "motorway_link": "autoroute ramp", "trunk": "expressway", "trunk_link": "expressway ramp",
           "primary": "primary", "primary_link": "primary", "secondary": "secondary", "secondary_link": "secondary",
           "tertiary": "tertiary", "tertiary_link": "tertiary", "residential": "residential", "unclassified": "other local",
           "living_street": "other local"}
OUT = ("autoroute", "pont", "tunnel", "voie", "ruelle")
END = 5.0            # metres kept clear at each end of a block face
DENSE = 8.0          # poles per km of curb above which a borough's inventory is taken as complete


def driving(city):
    g = gpd.read_file(OSM)
    g = g[g.highway.isin(CLASSES) & ~g.access.isin(["no", "private"]) & (g.motor_vehicle != "no")].to_crs(32188)
    g = gpd.clip(g, city)
    g["km"] = g.geometry.length / 1000
    g["cls"] = g.highway.map(CLASSES)
    g["oneway"] = g.oneway.isin(["yes", "-1", "1", "true"]) | g.highway.isin(["motorway", "motorway_link"])
    g["lanes_tag"] = pd.to_numeric(g.lanes, errors="coerce")
    med = g[g.lanes_tag.notna()].groupby(["highway", "oneway"]).lanes_tag.median()
    fb = pd.Series([med.get((h, o), 1 if o else 2) for h, o in zip(g.highway, g.oneway)], index=g.index)
    g["lanes_n"] = g.lanes_tag.fillna(fb)
    g["lane_km"] = g.km * g.lanes_n
    t = g.groupby("cls").apply(lambda x: pd.Series({
        "km_of_way": round(x.km.sum(), 1), "lane_km": round(x.lane_km.sum(), 1), "mean_lanes": round(x.lane_km.sum() / x.km.sum(), 2),
        "pct_lane_km_from_tag": round(100 * x[x.lanes_tag.notna()].lane_km.sum() / x.lane_km.sum(), 1)}), include_groups=False)
    t = t.sort_values("lane_km", ascending=False)
    t.to_csv(paths.TABLES / "street_lanes_by_class.csv")
    return g.lane_km.sum(), g.km.sum(), 100 * g[g.lanes_tag.notna()].lane_km.sum() / g.lane_km.sum(), t


def parking():
    g = gpd.read_file(GEOBASE).to_crs(32188)
    g = g[~g.TYP_VOIE.isin(OUT)].reset_index(drop=True)
    g["L"] = g.geometry.length
    faces = []
    for side, lim, arr in (("L", "LIM_GCH", "ARR_GCH"), ("R", "LIM_DRT", "ARR_DRT")):
        f = g[g[lim] == "Montréal"][["ID_TRC", "L", arr]].rename(columns={arr: "borough"}); f["side"] = side; faces.append(f)
    faces = pd.concat(faces, ignore_index=True)
    faces["net"] = (faces.L - 2 * END).clip(lower=0)

    s = pd.read_csv(SIGNS, dtype=str)
    s = s[(s.DESCRIPTION_REP == "Réel") & s.PAS_SUR_RUE.isna() & (s.DESCRIPTION_CAT == "STATIONNEMENT")]
    s["ban"] = s.DESCRIPTION_RPA.str.strip().isin(["\\A EN TOUT TEMPS", "\\P EN TOUT TEMPS"])
    poles = s.groupby("POTEAU_ID_POT").agg(x=("X", "first"), y=("Y", "first")).astype(float).reset_index()
    pg = gpd.GeoDataFrame(poles, geometry=gpd.points_from_xy(poles.x, poles.y), crs=32188)
    j = gpd.sjoin_nearest(pg, g[["ID_TRC", "L", "geometry"]], max_distance=20, distance_col="d").drop_duplicates("POTEAU_ID_POT")
    line = g.geometry.loc[j.index_right].values
    j["t"] = line_locate_point(line, j.geometry.values)
    a = gpd.GeoSeries(line, crs=32188).interpolate(np.clip(j.t.values - 1, 0, None)).values
    b = gpd.GeoSeries(line, crs=32188).interpolate(np.clip(j.t.values + 1, None, j.L.values)).values
    ax, ay, bx, by = [np.array(v) for v in ([p.x for p in a], [p.y for p in a], [p.x for p in b], [p.y for p in b])]
    cross = (bx - ax) * (j.geometry.y.values - ay) - (by - ay) * (j.geometry.x.values - ax)
    j["side"] = np.where(cross > 0, "L", "R")
    pol = j.set_index("POTEAU_ID_POT")[["ID_TRC", "L", "t", "side"]]
    bans = s[s.ban & s.POTEAU_ID_POT.isin(pol.index)][["POTEAU_ID_POT", "FLECHE_PAN"]].copy()
    bans["arrow"] = pd.to_numeric(bans.FLECHE_PAN, errors="coerce").fillna(0).astype(int)

    # per block face: the poles in order; each stretch between neighbours (and the ends)
    groups = {k: v.sort_values("t") for k, v in pol.reset_index().groupby(["ID_TRC", "side"])}
    banmap = bans.groupby("POTEAU_ID_POT").arrow.apply(list).to_dict()

    def banned(code2_forward_on_right):
        """Banned length per face (clear of the END zones), and the agreement score of the arrow coding."""
        out, both, one = {}, 0, 0
        for (trc, side), v in groups.items():
            L = v.L.iloc[0]; ts = [0.0] + list(v.t) + [L]; ids = [None] + list(v.POTEAU_ID_POT) + [None]
            n = len(ts) - 1; w = np.zeros(n); marks = np.zeros(n, dtype=int)
            for i in range(1, len(ids) - 1):
                for ar in banmap.get(ids[i], []):
                    if ar in (2, 3):
                        fwd = (ar == 2) == (code2_forward_on_right == (side == "R"))
                        k = i if fwd else i - 1
                        w[k] = 1; marks[k] += 1
                    elif ar == 0:
                        w[i - 1] = max(w[i - 1], 0.5); w[i] = max(w[i], 0.5)
                    else:                                   # double arrow and other codes: both stretches
                        w[i - 1] = 1; w[i] = 1
            inner = marks[1:-1]; both += int((inner >= 2).sum()); one += int((inner == 1).sum())
            tot = 0.0
            for k in range(n):
                if w[k]:
                    lo, hi = max(ts[k], END), min(ts[k + 1], L - END)
                    tot += w[k] * max(0.0, hi - lo)
            out[(trc, side)] = tot
        return out, both / max(1, both + one)

    o1, s1 = banned(True); o2, s2 = banned(False)
    ban_len, score, other = (o1, s1, s2) if s1 >= s2 else (o2, s2, s1)
    faces["banned"] = [min(ban_len.get((t, sd), 0.0), n_) for t, sd, n_ in zip(faces.ID_TRC, faces.side, faces.net)]
    faces["poles"] = [len(groups[(t, sd)]) if (t, sd) in groups else 0 for t, sd in zip(faces.ID_TRC, faces.side)]
    bt = faces.groupby("borough").agg(curb_km=("L", lambda x: x.sum() / 1000), net_km=("net", lambda x: x.sum() / 1000),
                                      banned_km=("banned", lambda x: x.sum() / 1000), poles=("poles", "sum"))
    bt["poles_per_km"] = bt.poles / bt.curb_km
    bt["inventory"] = np.where(bt.poles_per_km >= DENSE, "complete", "partial")
    share = bt[bt.inventory == "complete"].banned_km.sum() / bt[bt.inventory == "complete"].net_km.sum()
    bt["pct_banned_of_net"] = np.where(bt.inventory == "complete", 100 * bt.banned_km / bt.net_km, np.nan)
    bt["legal_km"] = np.where(bt.inventory == "complete", bt.net_km - bt.banned_km, bt.net_km * (1 - share))
    bt.round(2).sort_values("curb_km", ascending=False).to_csv(paths.TABLES / "street_curb_by_borough.csv")
    return faces.L.sum() / 1000, faces.net.sum() / 1000, bt.legal_km.sum(), 100 * share, bt, score, other, g.L.sum() / 1000


def main():
    city = gpd.read_file(LIMITS); city = city[city.TYPE == "Arrondissement"].to_crs(32188).dissolve()
    lane_km, way_km, pct_tag, t = driving(city)
    curb_km, net_km, legal_km, share, bt, score, other, _ = parking()
    ty = pd.read_csv(paths.TABLES / "type_by_municipality.csv", dtype={"muni_code": str})
    au = ty[(ty.muni_code == "66023") & (ty.vtype == "AU")].set_index("year").n
    R = lambda q, v, a="": {"quantity": q, "value": round(v, 1) if abs(v) < 1000 else round(v), "assumption": a}
    rows = [R("travel lanes in the municipality of Montréal (km)", lane_km, "OpenStreetMap lane counts, autoroutes included; service ways and ways closed to motor vehicles left out"),
            R("share of those lane-kilometres with a lane count in OpenStreetMap (%)", pct_tag, "the rest take the median of their class and direction"),
            R("length of those ways (km)", way_km, "each carriageway of a divided road is a separate way"),
            R("curb, both sides (km)", curb_km, "géobase; autoroutes, bridges, tunnels, ramps and back lanes left out"),
            R("curb after 5 m kept clear at each end of each block face (km)", net_km, "assumption for intersections"),
            R("share of that curb where stopping or parking is forbidden at all times, boroughs with a complete sign inventory (%)", share, "applied to the other boroughs"),
            R("legal curb (km)", legal_km, "driveways, hydrants, bus stops and hourly or permit restrictions not deducted")]
    rows += [R(f"parking bound: vehicles at {L} m each", 1000 * legal_km / L, "every legal metre of curb") for L in (5.0, 5.5, 6.0)]
    rows += [R(f"driving bound: vehicles at {L} m each", 1000 * lane_km / L, "every travel lane full, nose to tail") for L in (6.0, 7.0, 8.0)]
    rows += [R("automobiles and light trucks registered, 2024 (inferred)", au[2024], "type inferred"),
             R("the same as a share of the parking bound at 5.5 m (%)", 100 * au[2024] / (1000 * legal_km / 5.5)),
             R("the same as a share of the driving bound at 7.0 m (%)", 100 * au[2024] / (1000 * lane_km / 7.0)),
             R("arrow coding check: stretches marked from both ends, chosen coding (%)", 100 * score, f"the other coding gives {100 * other:.1f} %")]
    d = pd.DataFrame(rows); d.to_csv(paths.TABLES / "street_space_bounds.csv", index=False)
    pd.set_option("display.width", 230); pd.set_option("display.max_colwidth", 110)
    print(d[["quantity", "value"]].to_string(index=False)); print(t.to_string())
    print(bt[["curb_km", "poles_per_km", "inventory", "pct_banned_of_net"]].round(1).sort_values("curb_km", ascending=False).to_string())


if __name__ == "__main__":
    main()
