"""Stage 6: how long automobiles and light trucks stay registered.

Each model year is a cohort. Between two yearly files the cohort's count changes: the ratio is its
retention at that age (age = year of the first file minus model year). Retention is taken from age 3,
when a model year is fully on the road, and chained into the share of the vehicles present at age 3 that
are still registered at each later age. Québec as a whole is used, so that a move between municipalities
is not counted as a departure; a vehicle that leaves Québec or arrives used from elsewhere is.

2011-2022 are published counts. 2023 and 2024 are inferred counts (type from make, model, model year),
so the steps 2022->2023 and 2023->2024 carry the inference's error (under 0.2 % on published years).

Outputs (derived/tables/): cohort_retention.csv, cohort_survival.csv, vehicle_age_summary.csv
Run:  ~/.venvs/omd/bin/python scripts/cohorts.py
"""
import numpy as np
import pandas as pd

import paths

PERIODS = {"2011 to 2016": range(2011, 2016), "2016 to 2021": range(2016, 2021), "2021 to 2024": range(2021, 2024)}
A0, A1 = 3, 25


def main():
    t = pd.read_csv(paths.TABLES / "type_by_model_year.csv")
    out_r, out_s, out_a = [], [], []
    for scope in ("Québec", "Montréal"):
        d = t[(t.scope == scope) & (t.vtype == "AU")]
        w = d.pivot_table(index="model_year", columns="year", values="n", aggfunc="sum").fillna(0)
        for y in w.columns:                                   # age summary
            ages = (y - w.index.values).clip(min=0); n = w[y].values
            o = np.argsort(ages); c = np.cumsum(n[o]) / n.sum()
            out_a.append({"scope": scope, "year": y, "vehicles": round(n.sum()), "mean_age": round((ages * n).sum() / n.sum(), 2),
                          "median_age": int(ages[o][np.searchsorted(c, 0.5)]), "pct_10_years_or_more": round(100 * n[ages >= 10].sum() / n.sum(), 2),
                          "basis": "released" if y <= 2022 else "inferred"})
        for name, years in PERIODS.items():
            s = 1.0
            for a in range(A0, A1 + 1):
                start = sum(w.at[y - a, y] for y in years if (y - a) in w.index)
                end = sum(w.at[y - a, y + 1] for y in years if (y - a) in w.index)
                out_s.append({"scope": scope, "period": name, "age": a, "pct_still_registered": round(100 * s, 2)})
                r = end / start
                out_r.append({"scope": scope, "period": name, "age_at_start": a, "vehicles_at_start": round(start), "retention": round(r, 4)})
                s *= r
    pd.DataFrame(out_r).to_csv(paths.TABLES / "cohort_retention.csv", index=False)
    S = pd.DataFrame(out_s); S.to_csv(paths.TABLES / "cohort_survival.csv", index=False)
    A = pd.DataFrame(out_a); A.to_csv(paths.TABLES / "vehicle_age_summary.csv", index=False)
    q = S[S.scope == "Québec"].pivot(index="age", columns="period", values="pct_still_registered")
    print(q.loc[[5, 8, 10, 12, 15, 18, 20, 25]].to_string())
    for c in q.columns:
        print(c, "age at which half remain:", int(q.index[(q[c] <= 50).values.argmax()]) if (q[c] <= 50).any() else "beyond 25")
    print(A[A.year.isin([2011, 2016, 2021, 2022, 2023, 2024])].to_string(index=False))


if __name__ == "__main__":
    main()
