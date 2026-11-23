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
  complete only in some boroughs: the share forbidden there is applied to the others (an assumption).
  Also deducted (added November 15, 2026): 3 m on each side of every fire hydrant, on the hydrant's side of the
  street (Highway Safety Code, art. 386 par. 2, read on LégisQuébec November 15, 2026; City file « Bornes
  d'incendie », CC BY 4.0, downloaded November 15, 2026, hydrants marked EXISTANT), and a zone of 20 m at every
  STM bus stop, on the stop's side (the length is an assumption, 15 and 30 m given as a range; STM file
  « stm_arrets_sig », downloaded November 15, 2026, metro stations and entrances left out). A metre already inside
  an end clearance or an all-time prohibition is not deducted twice. Not deducted: restrictions by hour, day or
  permit, and driveways (each takes about one place at the curb and gives at least one private place, which the
  bound does not count: the two partly offset; the garages of large apartment buildings are the larger omission). Vehicles at 5.0 to 6.0 m each;
  central value 5.37 m (since November 23, 2026; 5.5 m before): the length at which, on rue de Terrebonne, the count of places net of
  driveway entrances (4 m each, the median length of the curb cuts measured on the City's 2015 LiDAR) and fire hydrants equals the
  consultant's count on the block faces where the street as built and the design retained in the 2023 study place the parking on the
  same side (EXP 2023, Annexe C); see the corridor note. Here no driveway is deducted, so the bound stays an upper one.

  Whole vehicles (added November 16, 2026): the legal curb is not one continuous strip. Each uninterrupted stretch
  (between an end clearance, an all-time prohibition, a hydrant clearance or a bus-stop zone and the next) holds a
  whole number of vehicles, and what is left over is lost. Where the sign inventory is complete the count is made
  stretch by stretch (a stretch governed by a sign without an arrow counts for half its length); elsewhere the
  ratio of that count to the plain division, found in the boroughs with a complete inventory, is applied.

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
HYDRANTS = TP / "montreal-opendata/bornes-incendie-2026-11-15/aqu_borneincendie_p.csv"
STOPS = TP / "stm-artm/stm_sig-2026-11-15/stm_arrets_sig.shp"
HYDRANT_CLEAR = 3.0  # metres on each side of a hydrant (Highway Safety Code, art. 386 par. 2)
BUS_ZONE = 20.0      # metres of curb taken by a bus stop (assumption); BUS_RANGE gives the sensitivity
BUS_RANGE = (15.0, 30.0)
CLASSES = {"motorway": "autoroute", "motorway_link": "autoroute ramp", "trunk": "expressway", "trunk_link": "expressway ramp",
           "primary": "primary", "primary_link": "primary", "secondary": "secondary", "secondary_link": "secondary",
           "tertiary": "tertiary", "tertiary_link": "tertiary", "residential": "residential", "unclassified": "other local",
           "living_street": "other local"}
OUT = ("autoroute", "pont", "tunnel", "voie", "ruelle")
END = 5.0            # metres kept clear at each end of a block face
DENSE = 8.0          # poles per km of curb above which a borough's inventory is taken as complete
CAR_CENTRAL = 5.37   # metres per parked vehicle, central value: the length at which, on rue de Terrebonne, the count of places net of
                     # driveway entrances (4 m each, the median length of the curb cuts measured on the City's 2015 LiDAR) and fire
                     # hydrants equals the consultant's count on the block faces where the street as built and the design retained in
                     # the 2023 study place the parking on the same side (EXP 2023, Annexe C); see the corridor note
                     # (Terrebonne-open-sources, 2026-terrebonne-corridor-vehicles-and-curb). Before November 23, 2026: 5.5 m.
CAR_BEFORE = 5.5     # the central value until November 23, 2026: kept in the table beside the new one
CAR_LENGTHS = (5.0, CAR_CENTRAL, CAR_BEFORE, 6.0)   # 5.0 and 6.0 m are the bounds of the band


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
        out, both, one, st = {}, 0, 0, {}
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
            out[(trc, side)] = tot; st[(trc, side)] = (ts, w)
        return out, both / max(1, both + one), st

    o1, s1, st1 = banned(True); o2, s2, st2 = banned(False)
    ban_len, score, other, stretches = (o1, s1, s2, st1) if s1 >= s2 else (o2, s2, s1, st2)
    faces["banned"] = [min(ban_len.get((t, sd), 0.0), n_) for t, sd, n_ in zip(faces.ID_TRC, faces.side, faces.net)]
    faces["poles"] = [len(groups[(t, sd)]) if (t, sd) in groups else 0 for t, sd in zip(faces.ID_TRC, faces.side)]

    # hydrants and bus stops: a point is given to the nearest street segment and to the side it stands on
    def place(pts, maxd):
        q = gpd.sjoin_nearest(pts, g[["ID_TRC", "L", "geometry"]], max_distance=maxd, distance_col="d")
        q = q[~q.index.duplicated()]
        ln = g.geometry.loc[q.index_right].values
        q["t"] = line_locate_point(ln, q.geometry.values)
        a_ = gpd.GeoSeries(ln, crs=32188).interpolate(np.clip(q.t.values - 1, 0, None)).values
        b_ = gpd.GeoSeries(ln, crs=32188).interpolate(np.clip(q.t.values + 1, None, q.L.values)).values
        ax_, ay_, bx_, by_ = [np.array(v) for v in ([p.x for p in a_], [p.y for p in a_], [p.x for p in b_], [p.y for p in b_])]
        cr = (bx_ - ax_) * (q.geometry.y.values - ay_) - (by_ - ay_) * (q.geometry.x.values - ax_)
        q["side"] = np.where(cr > 0, "L", "R")
        return q.groupby(["ID_TRC", "side"]).t.apply(list).to_dict(), len(pts), len(q)

    h = pd.read_csv(HYDRANTS, low_memory=False); h = h[h.STATUT_ACTIF == "EXISTANT"]
    hyd, n_h, n_hm = place(gpd.GeoDataFrame(h[["ID_BI"]], geometry=gpd.points_from_xy(h.COORDONNEE_SPATIALE_X, h.COORDONNEE_SPATIALE_Y), crs=32188), 20)
    b = gpd.read_file(STOPS).to_crs(32188); b = b[(b.loc_type == 0) & ~b.stop_url.fillna("").str.contains("/metro/")]
    bus, n_b, n_bm = place(b[["stop_id", "geometry"]].reset_index(drop=True), 20)

    def uncovered(key, L, ivs, use_w):
        """Length of the intervals (merged) that lies clear of the END zones and outside the all-time prohibitions."""
        ivs = sorted((max(a_, END), min(b_, L - END)) for a_, b_ in ivs); m = []
        for a_, b_ in ivs:
            if b_ <= a_: continue
            if m and a_ <= m[-1][1]: m[-1][1] = max(m[-1][1], b_)
            else: m.append([a_, b_])
        ts, w = stretches.get(key, ([0.0, L], np.zeros(1))) if use_w else ([0.0, L], np.zeros(1))
        return sum((1 - w[k]) * max(0.0, min(b_, ts[k + 1]) - max(a_, ts[k])) for a_, b_ in m for k in range(len(ts) - 1))

    def extras(half_bus):
        eh, eb = [], []
        for t, sd, L, bo in zip(faces.ID_TRC, faces.side, faces.L, faces.borough):
            k = (t, sd); hi = [(x - HYDRANT_CLEAR, x + HYDRANT_CLEAR) for x in hyd.get(k, [])]
            bi = [(x - half_bus, x + half_bus) for x in bus.get(k, [])]
            if not hi and not bi: eh.append(0.0); eb.append(0.0); continue
            uw = complete.get(bo, False)
            a_ = uncovered(k, L, hi, uw); eh.append(a_); eb.append(uncovered(k, L, hi + bi, uw) - a_)
        return np.array(eh), np.array(eb)

    ppk = faces.groupby("borough").apply(lambda x: x.poles.sum() / (x.L.sum() / 1000), include_groups=False)
    complete = (ppk >= DENSE).to_dict()
    faces["hydrant"], faces["bus"] = extras(BUS_ZONE / 2)
    bus_alt = {z: extras(z / 2)[1] for z in BUS_RANGE}
    for z, v in bus_alt.items(): faces[f"bus_{z:g}"] = v

    def pieces(key, L, bo):
        """Lengths of the uninterrupted legal stretches of a block face."""
        blk = sorted([(x - HYDRANT_CLEAR, x + HYDRANT_CLEAR) for x in hyd.get(key, [])] + [(x - BUS_ZONE / 2, x + BUS_ZONE / 2) for x in bus.get(key, [])])
        ts, w = stretches.get(key, ([0.0, L], np.zeros(1))) if complete.get(bo, False) else ([0.0, L], np.zeros(1))
        out, acc = [], 0.0                                   # acc: legal length accumulated since the last interruption
        for i in range(len(ts) - 1):                         # a sign pole is not an interruption: adjacent legal stretches join
            lo, hi = max(ts[i], END), min(ts[i + 1], L - END)
            if hi <= lo: continue
            if w[i] >= 1:
                if acc > 0: out.append(acc); acc = 0.0
                continue
            cur = lo
            for a_, b_ in blk:
                if b_ <= cur or a_ >= hi: continue
                if a_ > cur: acc += (a_ - cur) * (1 - w[i])
                if acc > 0: out.append(acc); acc = 0.0
                cur = max(cur, b_)
            if cur < hi: acc += (hi - cur) * (1 - w[i])
        if acc > 0: out.append(acc)
        return out

    CARS = CAR_LENGTHS
    pc = [pieces((t, sd), L, bo) for t, sd, L, bo in zip(faces.ID_TRC, faces.side, faces.L, faces.borough)]
    faces["piece_m"] = [sum(v) for v in pc]; faces["n_pieces"] = [len(v) for v in pc]
    for c in CARS: faces[f"whole_{c}"] = [sum(int(x // c) for x in v) for v in pc]
    bt = faces.groupby("borough").agg(piece_km=("piece_m", lambda x: x.sum() / 1000), n_pieces=("n_pieces", "sum"),
                                      **{f"whole_{c}": (f"whole_{c}", "sum") for c in CARS}, hydrant_km=("hydrant", lambda x: x.sum() / 1000), bus_km=("bus", lambda x: x.sum() / 1000),
                                      **{f"bus_{z:g}_km": (f"bus_{z:g}", lambda x: x.sum() / 1000) for z in BUS_RANGE},curb_km=("L", lambda x: x.sum() / 1000), net_km=("net", lambda x: x.sum() / 1000),
                                      banned_km=("banned", lambda x: x.sum() / 1000), poles=("poles", "sum"))
    bt["poles_per_km"] = bt.poles / bt.curb_km
    bt["inventory"] = np.where(bt.poles_per_km >= DENSE, "complete", "partial")
    share = bt[bt.inventory == "complete"].banned_km.sum() / bt[bt.inventory == "complete"].net_km.sum()
    bt["pct_banned_of_net"] = np.where(bt.inventory == "complete", 100 * bt.banned_km / bt.net_km, np.nan)
    bt["legal_before_km"] = np.where(bt.inventory == "complete", bt.net_km - bt.banned_km, bt.net_km * (1 - share))
    f = np.where(bt.inventory == "complete", 1.0, 1 - share)      # where the inventory is partial, the extra metres are assumed to be forbidden in the same share
    for c in ["hydrant_km", "bus_km"] + [f"bus_{z:g}_km" for z in BUS_RANGE]: bt[c] = bt[c] * f
    bt["legal_km"] = bt.legal_before_km - bt.hydrant_km - bt.bus_km
    bt.round(2).sort_values("curb_km", ascending=False).to_csv(paths.TABLES / "street_curb_by_borough.csv")
    cm = bt.inventory == "complete"
    ratio = {c: bt[cm][f"whole_{c}"].sum() / (1000 * bt[cm].legal_km.sum() / c) for c in CARS}
    whole = {c: bt[cm][f"whole_{c}"].sum() + ratio[c] * 1000 * bt[~cm].legal_km.sum() / c for c in CARS}
    check = bt[cm].piece_km.sum() / bt[cm].legal_km.sum()
    fk = set(zip(faces.ID_TRC, faces.side))
    x = dict(whole=whole, ratio=ratio, check=check, n_pieces=int(bt[cm].n_pieces.sum()), legal_complete=bt[cm].legal_km.sum(), before=bt.legal_before_km.sum(), hydrant=bt.hydrant_km.sum(), bus=bt.bus_km.sum(), n_h=n_hm, n_b=n_bm, n_h_all=n_h, n_b_all=n_b,
             n_h_faces=sum(len(v) for k, v in hyd.items() if k in fk), n_b_faces=sum(len(v) for k, v in bus.items() if k in fk),
             **{f"bus_{z:g}": bt[f"bus_{z:g}_km"].sum() for z in BUS_RANGE})
    return faces.L.sum() / 1000, faces.net.sum() / 1000, bt.legal_km.sum(), 100 * share, bt, score, other, x


def main():
    city = gpd.read_file(LIMITS); city = city[city.TYPE == "Arrondissement"].to_crs(32188).dissolve()
    lane_km, way_km, pct_tag, t = driving(city)
    curb_km, net_km, legal_km, share, bt, score, other, x = parking()
    ty = pd.read_csv(paths.TABLES / "type_by_municipality.csv", dtype={"muni_code": str})
    au = ty[(ty.muni_code == "66023") & (ty.vtype == "AU")].set_index("year").n
    R = lambda q, v, a="": {"quantity": q, "value": round(v, 1) if abs(v) < 1000 else round(v), "assumption": a}
    rows = [R("travel lanes in the municipality of Montréal (km)", lane_km, "OpenStreetMap lane counts, autoroutes included; service ways and ways closed to motor vehicles left out"),
            R("share of those lane-kilometres with a lane count in OpenStreetMap (%)", pct_tag, "the rest take the median of their class and direction"),
            R("length of those ways (km)", way_km, "each carriageway of a divided road is a separate way"),
            R("curb, both sides (km)", curb_km, "géobase; autoroutes, bridges, tunnels, ramps and back lanes left out"),
            R("curb after 5 m kept clear at each end of each block face (km)", net_km, "assumption for intersections"),
            R("share of that curb where stopping or parking is forbidden at all times, boroughs with a complete sign inventory (%)", share, "applied to the other boroughs"),
            R("legal curb before the hydrant and bus-stop deductions (km)", x["before"], "the figure used until November 15, 2026"),
            R("hydrants on a curb of the municipality (number)", x["n_h_faces"], "City file, hydrants marked EXISTANT, within 20 m of a street segment"),
            R("curb deducted for hydrants (km)", x["hydrant"], "3 m on each side (Highway Safety Code, art. 386 par. 2); metres already forbidden not counted twice"),
            R("STM bus stops on a curb of the municipality (number)", x["n_b_faces"], "STM file, metro stations and entrances left out, within 20 m of a street segment"),
            R("curb deducted for bus stops at 20 m each (km)", x["bus"], "the length of a stop zone is an assumption; metres already forbidden or within a hydrant clearance not counted twice"),
            R("the same at 15 m each (km)", x["bus_15"], "sensitivity"), R("the same at 30 m each (km)", x["bus_30"], "sensitivity"),
            R("legal curb (km)", legal_km, "driveways and hourly or permit restrictions not deducted")]
    rows += [R("uninterrupted legal stretches, boroughs with a complete sign inventory (number)", x["n_pieces"], f"mean length {1000 * x['legal_complete'] / x['n_pieces']:.1f} m"),
             R("their total length as a share of the legal curb of those boroughs (%)", 100 * x["check"], "check of the stretch-by-stretch count: 100 expected")]
    rows += [R(f"parking bound by plain division: vehicles at {L} m each", 1000 * legal_km / L, "the figure used until November 16, 2026") for L in CAR_LENGTHS]
    rows += [R(f"whole vehicles as a share of the plain division at {L} m (%)", 100 * x["ratio"][L], "boroughs with a complete sign inventory; applied to the others") for L in CAR_LENGTHS]
    rows += [R(f"parking bound: vehicles at {L} m each", x["whole"][L], "whole vehicles in each uninterrupted stretch of legal curb" + ("; the central length until November 23, 2026" if L == CAR_BEFORE else "; the central length (see CAR_CENTRAL in the script)" if L == CAR_CENTRAL else "")) for L in CAR_LENGTHS]
    rows += [R(f"driving bound: vehicles at {L} m each", 1000 * lane_km / L, "every travel lane full, nose to tail") for L in (6.0, 7.0, 8.0)]
    rows += [R("automobiles and light trucks registered, 2024 (inferred)", au[2024], "type inferred"),
             R(f"the same as a share of the parking bound at {CAR_CENTRAL} m (%)", 100 * au[2024] / x["whole"][CAR_CENTRAL], "the central length since November 23, 2026"),
             R(f"the same as a share of the parking bound at {CAR_BEFORE} m (%)", 100 * au[2024] / x["whole"][CAR_BEFORE], "the central length until November 23, 2026"),
             R("the same as a share of the parking bound at 5.0 m (%)", 100 * au[2024] / x["whole"][5.0], "lower end of the band"),
             R("the same as a share of the parking bound at 6.0 m (%)", 100 * au[2024] / x["whole"][6.0], "upper end of the band"),
             R("the same as a share of the driving bound at 7.0 m (%)", 100 * au[2024] / (1000 * lane_km / 7.0)),
             R("arrow coding check: stretches marked from both ends, chosen coding (%)", 100 * score, f"the other coding gives {100 * other:.1f} %")]
    d = pd.DataFrame(rows); d.to_csv(paths.TABLES / "street_space_bounds.csv", index=False)
    pd.set_option("display.width", 230); pd.set_option("display.max_colwidth", 110)
    print(d[["quantity", "value"]].to_string(index=False)); print(t.to_string())
    print(bt[["curb_km", "poles_per_km", "inventory", "pct_banned_of_net"]].round(1).sort_values("curb_km", ascending=False).to_string())


if __name__ == "__main__":
    main()
