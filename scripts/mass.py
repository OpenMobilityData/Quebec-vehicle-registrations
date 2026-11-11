"""Net mass of the fleet, 2011-2022 (the 2023-2024 files carry no mass).

Outputs (derived/tables/):
  mass_automobiles.csv        automobiles and light trucks (type AU), Québec and Montréal: distribution of net
                              mass by year, share at 2,000 kg or more, and the sum and mean of mass to the fourth
                              power as indices (2011 = 1)
  mass_fourth_power_by_type_montreal.csv   every type: vehicles, mean mass, share of the summed fourth power
The fourth power of mass is the quantity behind the « Road Wear Index » of the 2025 SAAQAnalyzer charts. It uses
the net mass (the vehicle empty) and no distance driven: it describes the composition of the registered fleet.
Run:  ~/.venvs/omd/bin/python scripts/mass.py
"""
import duckdb
import pandas as pd

import paths


def main():
    con = duckdb.connect()
    con.execute(f"CREATE VIEW v AS SELECT * FROM read_parquet('{paths.PARQUET_DIR}/vehicles_*.parquet') WHERE source='open'")
    parts = []
    for scope, cond in (("Québec", "true"), ("Montréal", "muni_code='66023'")):
        parts.append(con.execute(f"""
            SELECT year, '{scope}' AS scope, count(*) AS vehicles, round(100.0 * count(net_mass_kg) / count(*), 2) AS pct_with_mass,
                   round(avg(net_mass_kg), 1) AS mean_kg, round(quantile_cont(net_mass_kg, 0.10)) AS p10_kg,
                   round(median(net_mass_kg)) AS median_kg, round(quantile_cont(net_mass_kg, 0.90)) AS p90_kg,
                   round(100.0 * count(*) FILTER (WHERE net_mass_kg >= 2000) / count(net_mass_kg), 2) AS pct_2000kg_or_more,
                   sum(power(net_mass_kg::DOUBLE, 4)) AS m4, avg(power(net_mass_kg::DOUBLE, 4)) AS m4_mean
            FROM v WHERE vtype='AU' AND {cond} GROUP BY ALL ORDER BY year""").df())
    a = pd.concat(parts)
    for col, out in (("m4", "fourth_power_total_index"), ("m4_mean", "fourth_power_mean_index")):
        a[out] = (a[col] / a.groupby("scope")[col].transform("first")).round(4)
    a.drop(columns=["m4", "m4_mean"]).to_csv(paths.TABLES / "mass_automobiles.csv", index=False)
    b = con.execute("""
        SELECT year, vtype, count(*) AS vehicles, round(avg(net_mass_kg)) AS mean_kg, sum(power(net_mass_kg::DOUBLE, 4)) AS m4
        FROM v WHERE muni_code='66023' AND vtype IN ('AU','CA','AB','VO') GROUP BY ALL ORDER BY ALL""").df()
    b["pct_of_fourth_power"] = (100 * b.m4 / b.groupby("year").m4.transform("sum")).round(2)
    b["pct_of_vehicles"] = (100 * b.vehicles / b.groupby("year").vehicles.transform("sum")).round(2)
    b.drop(columns="m4").to_csv(paths.TABLES / "mass_fourth_power_by_type_montreal.csv", index=False)
    m = a[a.scope == "Montréal"].set_index("year")
    # the 2025 chart: total 1.35 and mean 1.22 in 2022 against 2011, automobiles and light trucks, Montréal
    print(m.loc[[2011, 2016, 2021, 2022]].to_string())
    print(b[b.year.isin([2011, 2012, 2013, 2022])].to_string(index=False))


if __name__ == "__main__":
    main()
