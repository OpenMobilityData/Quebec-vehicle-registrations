"""Stage 4b: 2021 Census counts by FSA, built from dissemination areas, and joined to the vehicles of
2023-2024.

Statistics Canada publishes a census profile by FSA; its site refused an automated download on
November 10, 2026, so the counts are built here from the profile by dissemination area (catalogue
98-401-X2021006, Québec), which was on hand. A dissemination area is shared among FSAs in
proportion to the postal codes of each FSA located inside it (postal-code points: Service Objects,
March 2024, used under licence, not redistributed); one with no postal code inside it goes to the
FSA whose polygon contains its representative point (DMTI Spatial, CanMap Postal Code Suite
v2024.3, used under licence, not redistributed). The shares count postal codes, not residents.
Counts are summed; rates and medians are not
carried over. Statistics Canada rounds each count of a dissemination area at random to a multiple of
five, so the sums differ a little from the agency's own FSA figures.

Outputs (derived/tables/): fsa_census_2021.csv, fsa_vehicles_census.csv
Run:  ~/.venvs/omd/bin/python scripts/census_fsa.py
"""
import os
from pathlib import Path

import duckdb
import geopandas as gpd
import pandas as pd

import paths

TP = Path(os.environ.get("THIRD_PARTY", Path.home() / "Terrebonne-data/third-party"))
DA_CSV = TP / "statcan-census-2021/98-401-X2021006_Quebec_DA/98-401-X2021006_English_CSV_data_Quebec.csv"
DA_SHP = TP / "statcan-census-2021/boundaries/lda_000a21a_e/lda_000a21a_e.shp"
PC_CSV = TP / "serviceobjects-2024-03/CanadianPostalCodes202403.csv"
FSA_SHP = TP / "canmap-v2024.3/CanMapPostalCodeSuitev2024.3/Shapefiles/ForwardSortationAreasRegion.shp"
CACHE = paths.PARQUET_DIR.parent / "census_da_extract.parquet"
CHAR = {1: "population", 4: "private_dwellings", 5: "households", 13: "pop_15_64", 24: "pop_65_plus",
        41: "dwellings_by_type_total", 42: "single_detached", 1414: "tenure_total", 1415: "owner", 1416: "renter",
        2603: "commuters", 2605: "commute_car_driver", 2606: "commute_car_passenger", 2607: "commute_transit",
        2608: "commute_walk", 2609: "commute_bicycle", 2610: "commute_other"}


def da_counts():
    if not CACHE.exists():
        ids = ",".join(f"'{i}'" for i in CHAR)
        duckdb.connect().execute(f"""
            COPY (SELECT ALT_GEO_CODE AS dauid, CAST(CHARACTERISTIC_ID AS INTEGER) AS id, TRY_CAST(C1_COUNT_TOTAL AS DOUBLE) AS v
                  FROM read_csv('{DA_CSV}', all_varchar=true, encoding='latin-1', header=true)
                  WHERE GEO_LEVEL = 'Dissemination area' AND CHARACTERISTIC_ID IN ({ids}))
            TO '{CACHE}' (FORMAT parquet)""")
    d = pd.read_parquet(CACHE)
    w = d.pivot(index="dauid", columns="id", values="v").rename(columns=CHAR)
    return w.reset_index()


def main():
    w = da_counts()
    da = gpd.read_file(DA_SHP, columns=["DAUID", "PRUID"], where="PRUID = '24'")
    fsa = gpd.read_file(FSA_SHP)
    col = [c for c in fsa.columns if c.upper() in ("FSA", "CFSAUID", "POSTALCODE")][0]
    fsa = fsa[[col, "geometry"]].rename(columns={col: "fsa"}).to_crs(da.crs)
    # 1. shares from postal codes: each postal code is a point; a dissemination area belongs to each FSA
    #    in proportion to the postal codes of that FSA found inside it
    pc = pd.read_csv(PC_CSV, dtype=str, on_bad_lines="skip", encoding="latin-1")
    pc = pc[pc.PROVINCE_ABBR == "QC"]
    pcg = gpd.GeoDataFrame({"fsa": pc.PostalCode.str[:3].values},
                           geometry=gpd.points_from_xy(pc.Longitude.astype(float), pc.Latitude.astype(float)),
                           crs="EPSG:4326").to_crs(da.crs)
    hit = gpd.sjoin(pcg, da[["DAUID", "geometry"]], predicate="within", how="inner")
    sh = hit.groupby(["DAUID", "fsa"]).size().rename("k").reset_index()
    sh["share"] = sh.k / sh.groupby("DAUID").k.transform("sum")
    # 2. a dissemination area with no postal code inside it: the FSA polygon containing its representative point
    rest = da[~da.DAUID.isin(sh.DAUID)]
    pts = rest.set_geometry(rest.representative_point())
    j = gpd.sjoin(pts, fsa, predicate="within", how="left")[["DAUID", "fsa"]].drop_duplicates("DAUID").assign(share=1.0)
    sh = pd.concat([sh[["DAUID", "fsa", "share"]], j[j.fsa.notna()]], ignore_index=True)
    m = w.merge(sh, left_on="dauid", right_on="DAUID", how="left")
    print(f"dissemination areas: {len(w):,}; shared out by postal codes: {hit.DAUID.nunique():,}; by polygon: {j.fsa.notna().sum():,}; "
          f"population placed: {(m.population * m.share).sum():,.0f} of {w.population.sum():,.0f}")
    vals = list(CHAR.values())
    m[vals] = m[vals].multiply(m.share, axis=0)
    g = m[m.fsa.notna()].groupby("fsa")
    c = g[vals].sum(min_count=1)
    c.insert(0, "dissemination_areas", g.size())
    c["pop_15_plus"] = c.pop_15_64 + c.pop_65_plus
    c = c.drop(columns=["dwellings_by_type_total", "tenure_total"]).round(0).astype("Int64")
    c.to_csv(paths.TABLES / "fsa_census_2021.csv")

    t = pd.read_csv(paths.TABLES / "type_by_fsa.csv")
    tot = t.groupby(["year", "fsa"]).n.sum().rename("vehicles_all_types")
    au = t[t.vtype == "AU"].groupby(["year", "fsa"]).n.sum().rename("automobiles_light_trucks_inferred")
    v = pd.concat([tot, au], axis=1).reset_index().merge(c.reset_index(), on="fsa", how="left")
    v["au_per_household"] = (v.automobiles_light_trucks_inferred / v.households).round(3)
    v["au_per_100_residents_15_plus"] = (100 * v.automobiles_light_trucks_inferred / v.pop_15_plus).round(1)
    v["pct_commute_car_driver"] = (100 * v.commute_car_driver / v.commuters).round(1)
    v["pct_commute_transit_walk_bicycle"] = (100 * (v.commute_transit + v.commute_walk + v.commute_bicycle) / v.commuters).round(1)
    v["pct_renter"] = (100 * v.renter / (v.owner + v.renter)).round(1)
    v.round({"vehicles_all_types": 0, "automobiles_light_trucks_inferred": 0}).to_csv(
        paths.TABLES / "fsa_vehicles_census.csv", index=False)
    pd.set_option("display.width", 250)
    show = ["year", "fsa", "automobiles_light_trucks_inferred", "households", "population", "au_per_household",
            "au_per_100_residents_15_plus", "pct_commute_car_driver", "pct_commute_transit_walk_bicycle", "pct_renter"]
    print(v[v.fsa.isin(["H4A", "H4B", "H3X", "H4V", "H3W", "H3S"])][show].to_string(index=False))
    isl = v[(v.year == 2024) & v.fsa.str.startswith("H", na=False) & (v.households >= 1000)]
    print("FSAs beginning with H, 1,000 households or more:", len(isl), "; AU per household quartiles:",
          isl.au_per_household.quantile([0.1, 0.25, 0.5, 0.75, 0.9]).round(2).tolist())
    print("FSA of the release with no census match:", int(v[(v.year == 2024) & v.households.isna()].vehicles_all_types.sum()), "vehicles")


if __name__ == "__main__":
    main()
