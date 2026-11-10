"""Stage 2: map the make and model strings of the 2023-2024 release onto the
vocabulary of the curated open data (2011-2022).

The open data write makes and models as codes of at most five characters
(TOYOT, COROL, CR-V). The release mixes those codes with full names (TOYOTA,
COROLLA), other abbreviations (SIE for SIERR) and misspellings. Rules, applied
in this order; the first that succeeds is recorded:

  make   exact | first five characters | punctuation removed | alias table
         (scripts/aliases_make.csv) | prefix of one curated make holding
         >= 95 % of the vehicles of all curated makes with that prefix
  model  (within the resolved make) exact | first five characters |
         punctuation removed | alias table (scripts/aliases_model.csv) |
         prefix (>= 3 characters) of one curated model holding >= 90 % of the
         vehicles of the make's curated models with that prefix | the longest
         curated model that begins the string, the rest being a trim or variant
         suffix (328XI -> 328; a one-character model only before digits, C250 -> C)

A string that no rule resolves stays unresolved; stage 3 then falls back on the
make alone, and failing that leaves the vehicle unassigned. Nothing is guessed
by string distance.

Outputs (derived/tables/):
  vocabulary_map.csv        every distinct (make_raw, model_raw) of the release
  vocabulary_coverage.csv   share of vehicles by year and rule
  vocabulary_review.csv     largest unresolved strings with candidate curated models
  vocabulary_codes_used_differently.csv   resolved codes withdrawn because the release uses them for other vehicles
  vocabulary_codes_reassigned.csv         withdrawn codes reassigned to the curated model whose vehicles they are
Run:  ~/.venvs/omd/bin/python scripts/vocabulary.py
"""
import re
from collections import defaultdict
from pathlib import Path

import duckdb
import pandas as pd

import paths

HERE = Path(__file__).resolve().parent
strip = lambda s: re.sub(r"[^A-Z0-9]", "", s)


def dominant(cands, share):
    """cands: {name: vehicles}. The name holding at least `share` of the total, else None."""
    if not cands:
        return None
    best = max(cands, key=cands.get)
    return best if cands[best] >= share * sum(cands.values()) else None


def main():
    con = duckdb.connect()
    con.execute(f"CREATE VIEW v AS SELECT * FROM read_parquet('{paths.PARQUET_DIR}/vehicles_*.parquet')")
    canon = con.execute(
        "SELECT upper(make_raw) make, upper(coalesce(model_raw,'')) model, count(*) n, "
        "min(model_year) y0, max(model_year) y1 FROM v WHERE source='open' AND make_raw IS NOT NULL GROUP BY ALL").df()
    acc = con.execute(
        "SELECT upper(coalesce(make_raw,'')) make_raw, upper(coalesce(model_raw,'')) model_raw, "
        "sum((year=2023)::INT) n_2023, sum((year=2024)::INT) n_2024, "
        "min(model_year) y0, max(model_year) y1 FROM v WHERE source='access' GROUP BY ALL").df()

    makes = canon.groupby("make").n.sum().to_dict()
    makes_stripped = defaultdict(dict)
    for m, n in makes.items():
        makes_stripped[strip(m)][m] = n
    models = defaultdict(dict)                     # make -> {model: n}
    for r in canon.itertuples():
        models[r.make][r.model] = r.n
    models_stripped = {mk: defaultdict(dict) for mk in models}
    for mk, d in models.items():
        for md, n in d.items():
            models_stripped[mk][strip(md)][md] = n

    alias_make = pd.read_csv(HERE / "aliases_make.csv").set_index("make_raw").make.to_dict()
    for raw, target in alias_make.items():
        assert target in makes, f"alias target {target} is not a curated make"
        assert raw not in makes, f"{raw} is itself a curated make"
    am = HERE / "aliases_model.csv"
    alias_model = {}
    if am.exists():
        for r in pd.read_csv(am, dtype=str).itertuples():
            assert r.model in models[r.make], f"alias target {r.make} {r.model} is not a curated model"
            alias_model[(r.make, r.model_raw)] = r.model

    def resolve_make(raw):
        if raw in makes:
            return raw, "exact"
        if raw[:5] in makes:
            return raw[:5], "first five"
        s = strip(raw)
        for key in (s, s[:5]):
            if key in makes_stripped:
                return max(makes_stripped[key], key=makes_stripped[key].get), "punctuation"
        if raw in alias_make:
            return alias_make[raw], "alias"
        if len(s) >= 3:
            hit = dominant({m: n for m, n in makes.items() if strip(m).startswith(s)}, 0.95)
            if hit:
                return hit, "prefix"
        return None, "unresolved"

    def resolve_model(make, raw):
        d = models[make]
        s = strip(raw)
        ms = models_stripped[make]
        # The curated tables hold rare variants of their own codes (16 vehicles under HONDA CRV beside
        # 1.1 million under CR-V). Codes equal but for punctuation are one model: the commonest spelling.
        for key, rule in ((raw, "exact"), (raw[:5], "first five")):
            if key in d:
                best = max(ms[strip(key)], key=ms[strip(key)].get) if strip(key) in ms else key
                return best, rule if best == key else "punctuation"
        for key in (s, s[:5]):
            if key and key in ms:
                return max(ms[key], key=ms[key].get), "punctuation"
        if (make, raw) in alias_model:
            return alias_model[(make, raw)], "alias"
        if len(s) >= 3:
            hit = dominant({m: n for m, n in d.items() if strip(m).startswith(s)}, 0.90)
            if hit:
                return hit, "prefix"
        # a curated model followed by a trim or variant suffix (328XI -> 328, RAV4PRIME -> RAV4, C250 -> C)
        for k in range(len(s) - 1, 0, -1):
            if s[k - 1].isdigit() and s[k].isdigit() and k >= 2:
                continue                           # CX90 is not CX-9 with a suffix: the number differs
            if s[:k] in ms and (k >= 2 or s[k:].isdigit()):
                return max(ms[s[:k]], key=ms[s[:k]].get), "suffix removed"
        return None, "unresolved"

    out = []
    for r in acc.itertuples():
        mk, rm = resolve_make(r.make_raw)
        md, rd = (None, "no make")
        if mk is not None:
            md, rd = resolve_model(mk, r.model_raw)
        out.append((mk, rm, md, rd))
    acc[["make", "make_rule", "model", "model_rule"]] = pd.DataFrame(out, index=acc.index)
    # A code that means something else in the release. Vehicles of model year 2021 or earlier were all on
    # the road by the 2022 snapshot, so their number per code can hardly grow afterwards. A resolved code
    # whose 2023 count of such vehicles is more than twice its 2022 count, by more than 100 vehicles, is
    # not the same code (FORD VAN, CTV, DRW: 4,000 motorhome conversions in the open data, ordinary vans
    # in the release). Its model is withdrawn and stage 3 falls back on the make.
    old22 = con.execute("SELECT upper(make_raw) make, upper(coalesce(model_raw,'')) model, count(*) n22 FROM v "
                        "WHERE year=2022 AND model_year<=2021 GROUP BY ALL").df()
    old23 = con.execute("SELECT upper(coalesce(make_raw,'')) make_raw, upper(coalesce(model_raw,'')) model_raw, count(*) n23 "
                        "FROM v WHERE year=2023 AND model_year<=2021 GROUP BY ALL").df()
    t = acc.merge(old23, on=["make_raw", "model_raw"], how="left")
    g = t[t.model.notna()].groupby(["make", "model"]).n23.sum().reset_index().merge(old22, on=["make", "model"], how="left").fillna({"n22": 0})
    drift = g[(g.n23 > 2 * g.n22) & (g.n23 - g.n22 > 100)].sort_values("n23", ascending=False)
    drift.to_csv(paths.TABLES / "vocabulary_codes_used_differently.csv", index=False)
    print("codes withdrawn:", len(drift), "vehicles of model year <= 2021 in 2023:", int(drift.n23.sum()))
    print(drift.head(25).to_string(index=False))
    bad = set(zip(drift.make, drift.model))
    hit = pd.Series([(mk, md) in bad for mk, md in zip(acc.make, acc.model)], index=acc.index)
    withdrawn = acc.loc[hit, ["make", "model"]].copy()
    acc.loc[hit, "model_rule"] = "code used differently"
    acc.loc[hit, "model"] = None

    # Where did those vehicles go? The curators merged some codes (DODGE CARAV into GRAND, JEEP GRCHE into
    # GRAND, TESLA 3 into MODEL). A withdrawn code is reassigned to the curated model of the same make whose
    # 2022 vehicles of model year <= 2021 are missing from the release in the same numbers, model year by
    # model year: correlation of the two model-year profiles >= 0.9, and the code no larger than 1.5 times
    # what is missing. Otherwise it stays withdrawn.
    p22 = con.execute("SELECT upper(make_raw) make, upper(coalesce(model_raw,'')) model, model_year my, count(*) n FROM v "
                      "WHERE year=2022 AND model_year BETWEEN 1990 AND 2021 GROUP BY ALL").df()
    p23 = con.execute("SELECT upper(coalesce(make_raw,'')) make_raw, upper(coalesce(model_raw,'')) model_raw, model_year my, count(*) n "
                      "FROM v WHERE year=2023 AND model_year BETWEEN 1990 AND 2021 GROUP BY ALL").df()
    p23 = p23.merge(acc[["make_raw", "model_raw", "make", "model"]], on=["make_raw", "model_raw"])
    keep23 = p23[p23.model.notna()].groupby(["make", "model", "my"]).n.sum()
    have22 = p22.groupby(["make", "model", "my"]).n.sum()
    acc_w = acc.loc[hit, ["make_raw", "model_raw"]].assign(wmake=withdrawn.make.values, wmodel=withdrawn.model.values)
    wprof = p23.drop(columns=["make", "model"]).merge(acc_w, on=["make_raw", "model_raw"]).groupby(["wmake", "wmodel", "my"]).n.sum()
    years = list(range(1990, 2022))
    moved = []
    for (mk, wm), prof in wprof.groupby(level=[0, 1]):
        x = prof.droplevel([0, 1]).reindex(years, fill_value=0).astype(float)
        if mk not in have22.index.get_level_values(0):
            continue
        best = None
        for md, h in have22.loc[mk].groupby(level=0):
            if md == wm:
                continue
            miss = h.droplevel(0).reindex(years, fill_value=0).astype(float)
            if (mk, md) in keep23.index:
                miss = miss - keep23.loc[(mk, md)].reindex(years, fill_value=0)
            miss = miss.clip(lower=0)
            if miss.sum() < x.sum() / 1.5 or miss.std() == 0 or x.std() == 0:
                continue
            c = x.corr(miss)
            if c >= 0.9 and (best is None or c > best[1]):
                best = (md, c, miss.sum())
        if best:
            moved.append({"make": mk, "code_in_release": wm, "curated_model": best[0], "vehicles_2023": int(x.sum()),
                          "missing_from_curated_model": int(best[2]), "profile_correlation": round(best[1], 3)})
    moved = pd.DataFrame(moved).sort_values("vehicles_2023", ascending=False)
    moved.to_csv(paths.TABLES / "vocabulary_codes_reassigned.csv", index=False)
    print("codes reassigned by model-year profile:", len(moved), "vehicles:", int(moved.vehicles_2023.sum()))
    print(moved.head(30).to_string(index=False))
    to = {(r.make, r.code_in_release): r.curated_model for r in moved.itertuples()}
    for i, mk, wm in zip(acc_w.index, acc_w.wmake, acc_w.wmodel):
        if (mk, wm) in to:
            acc.loc[i, "model"] = to[(mk, wm)]
            acc.loc[i, "model_rule"] = "reassigned by model-year profile"
    acc["level"] = "unresolved"
    acc.loc[acc.make.notna(), "level"] = "make only"
    acc.loc[acc.model.notna(), "level"] = "make and model"
    acc.sort_values(["n_2024", "n_2023"], ascending=False)[
        ["make_raw", "model_raw", "make", "make_rule", "model", "model_rule", "level", "n_2023", "n_2024"]
    ].to_csv(paths.TABLES / "vocabulary_map.csv", index=False)
    acc[["make_raw", "model_raw", "make", "model", "level"]].to_parquet(paths.PARQUET_DIR.parent / "vocabulary_map.parquet")

    rows = []
    for y in (2023, 2024):
        col = f"n_{y}"
        tot = acc[col].sum()
        for (lvl, rm, rd), n in acc.groupby(["level", "make_rule", "model_rule"])[col].sum().items():
            rows.append({"year": y, "level": lvl, "make_rule": rm, "model_rule": rd,
                         "vehicles": int(n), "pct": round(100 * n / tot, 3)})
    cov = pd.DataFrame(rows).sort_values(["year", "vehicles"], ascending=[True, False])
    cov.to_csv(paths.TABLES / "vocabulary_coverage.csv", index=False)
    print(cov.groupby(["year", "level"]).agg(vehicles=("vehicles", "sum"), pct=("pct", "sum")).to_string())
    print(cov[cov.year == 2024].head(14).to_string(index=False))

    # review table: the largest strings resolved to a make but not a model
    rev = acc[(acc.level == "make only") & (acc.model_raw != "")].copy()
    rev["n"] = rev.n_2023 + rev.n_2024
    rev = rev.sort_values("n", ascending=False).head(150)
    def cands(r):
        d = models[r.make]
        first = strip(r.model_raw)[:1]
        c = sorted(((n, m) for m, n in d.items() if strip(m)[:1] == first), reverse=True)[:6]
        return " ".join(f"{m}({n})" for n, m in c)
    rev["curated_models_same_initial"] = [cands(r) for r in rev.itertuples()]
    rev[["make_raw", "model_raw", "make", "y0", "y1", "n", "curated_models_same_initial"]].to_csv(
        paths.TABLES / "vocabulary_review.csv", index=False)


if __name__ == "__main__":
    main()
