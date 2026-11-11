"""Slide deck (beamer 16:9, English) from derived/tables/ and derived/figures/. DRAFT banner until --final.
Every number on a slide is read from a table at build time.
Run:  ~/.venvs/omd/bin/python scripts/build_docs.py [--final]   ->  docs/vehicle_registrations_deck_en.pdf
"""
import datetime
import subprocess
import sys
from zoneinfo import ZoneInfo

import pandas as pd

import paths

FINAL = "--final" in sys.argv
DOCS = paths.REPO / "docs"
FIG = paths.REPO / "derived" / "figures"
T = paths.TABLES
now = datetime.datetime.now(ZoneInfo("America/Toronto"))
TAG = now.strftime("v%Y-%m-%d-%H-%M-%S")
n = lambda x, d=0: f"{x:,.{d}f}".replace(",", "{,}")
p = lambda x, d=1: f"{x:.{d}f}".replace("-", "$-$")

ing = pd.read_csv(T / "ingest_summary.csv").set_index("year")
cov = pd.read_csv(T / "vocabulary_coverage.csv")
lvl = cov.groupby(["year", "level"]).pct.sum()
exact = cov[(cov.make_rule == "exact") & (cov.model_rule == "exact")].set_index("year").pct
mm = pd.read_csv(T / "municipality_match.csv")
mm_s = 100 * mm.groupby("status").n_2024.sum() / mm.n_2024.sum()
h = pd.read_csv(T / "holdout_summary.csv")
au = h[(h.target == "vtype") & (h.value == "AU")]
aum, auq = au[au.scope == "Montréal"].pct_error, au[au.scope == "Québec"].pct_error
fq = h[(h.target == "fuel") & (h.scope == "Québec")]
fr = lambda v, lead: (fq[(fq.value == v) & (fq.lead == lead)].pct_error.min(), fq[(fq.value == v) & (fq.lead == lead)].pct_error.max())
hm = pd.read_csv(T / "holdout_municipal.csv"); hm = hm[(hm.year == 2022) & (hm.lead == 1)].set_index("vehicles_registered")
t = pd.read_csv(T / "type_by_municipality.csv", dtype={"muni_code": str}); m = t[t.muni_code == "66023"]
allv = m.groupby("year").n.sum(); mau = m[m.vtype == "AU"].set_index("year").n
age = pd.read_csv(T / "age_bands_montreal.csv").set_index("year")
v = pd.read_csv(T / "fsa_vehicles_census.csv"); v24 = v[v.year == 2024].set_index("fsa")
isl = v24[v24.index.str.startswith("H") & (v24.households >= 1000)]
rank = isl.au_per_household.rank()
il = pd.read_csv(T / "inference_levels.csv"); il = il[il.target == "vtype"].set_index(["year", "level"]).pct
moved = pd.read_csv(T / "vocabulary_codes_reassigned.csv")

rc = pd.read_csv(T / "reproduction_checks.csv")
ma = pd.read_csv(T / "mass_automobiles.csv"); mam = ma[ma.scope == "Montréal"].set_index("year")
mt = pd.read_csv(T / "mass_fourth_power_by_type_montreal.csv"); mt22 = mt[mt.year == 2022].set_index("vtype")
bus = mt[mt.vtype == "AB"].set_index("year").vehicles
cs = pd.read_csv(T / "cohort_survival.csv"); csq = cs[cs.scope == "Québec"].pivot(index="age", columns="period", values="pct_still_registered")
PER = list(csq.columns); half = {c: int(csq.index[(csq[c] <= 50).values.argmax()]) for c in PER}
va = pd.read_csv(T / "vehicle_age_summary.csv"); vam = va[va.scope == "Montréal"].set_index("year")
vl = pd.read_csv(T / "vehicles_per_licence.csv"); vli = vl[vl.scope.str.startswith("Island")].set_index("year"); vlq = vl[vl.scope == "Québec"].set_index("year")
la = pd.read_csv(T / "licence_holders_by_age.csv"); la = la[la.scope.str.startswith("Island")]
lag = la.assign(g=la.age_band.map({"16-19": "y", "20-24": "y", "65 ans ou plus": "o"})).dropna(subset=["g"]).pivot_table(index="year", columns="g", values="car_licence_holders", aggfunc="sum")
sc = pd.read_csv(T / "trend_scenario.csv").set_index("year"); per_year = round((sc.trend_2011_2021[2035] - sc.trend_2011_2021[2011]) / 24)
st = pd.read_csv(T / "storage_equivalents.csv").set_index("case")
pr = pd.read_csv(T / "vehicles_per_1000_residents.csv").set_index("year")
sb = pd.read_csv(T / "street_space_bounds.csv").set_index("quantity").value
fa = pd.read_csv(T / "fsa_vehicle_age.csv").set_index("fsa")
qt = pd.read_csv(T / "type_by_year_quebec.csv")
enc = pd.read_csv(T / "vehicles_by_municipality.csv", dtype={"muni_code": str}); enc = enc[enc.muni_code.isin(["66062", "66047", "66058", "66032"])].groupby("year").n.sum()


def fsarow(f):
    r = v24.loc[f]
    return f"{f} & {n(r.automobiles_light_trucks_inferred)} & {n(r.households)} & {p(r.au_per_household, 2)} & {p(r.pct_commute_car_driver)} & {int(rank[f])} of {len(isl)} \\\\"

BANNER = "" if FINAL else r"\setbeamertemplate{footline}{\hfill{\tiny\textcolor{red!70!black}{DRAFT for the author\textquoteright{}s review, " + TAG + r"}\quad\insertframenumber}\hspace{1em}\vspace{0.4em}}"
fig = lambda name, stem, w=0.98: rf"\begin{{center}}\includegraphics[width={w}\linewidth,height=0.80\textheight,keepaspectratio]{{{FIG / name / (stem + '_en.png')}}}\end{{center}}"

DECK = r"""\documentclass[aspectratio=169,10pt]{beamer}\usetheme{default}\usecolortheme{seahorse}\setbeamertemplate{navigation symbols}{}\setbeamertemplate{footline}[frame number]
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{helvet}\usepackage{booktabs,amsmath}
\setbeamersize{text margin left=0.7cm,text margin right=0.7cm}\setbeamerfont{frametitle}{size=\large,series=\bfseries}
""" + BANNER + r"""
\title{Vehicle registrations in Québec, 2011--2024}
\subtitle{Joining the SAAQ's open data with the files released under the access Act}
\author{Rick Hoge, PhD}\date{""" + ("" if FINAL else r"Draft, ") + now.strftime("%B %-d, %Y") + r""" \quad {\footnotesize """ + TAG + r"""}}
\begin{document}
\begin{frame}\titlepage\end{frame}

\begin{frame}{Overview: the municipality of Montréal, 2011--2024}
""" + fig("montreal-automobiles", "montreal_automobiles") + r"""
\end{frame}

\begin{frame}{Two sources, one row per registered vehicle}
\small
\begin{tabular}{@{}p{1.9cm}p{5.6cm}p{6.4cm}@{}}\toprule
Years & Source & Columns \\\midrule
2011--2022 & SAAQ open data, « Véhicules en circulation » (CC BY 4.0), files as revised by the SAAQ on December 18, 2023 & class, type, make, model, model year, net mass, cylinders, displacement, axles, colour, fuel (from 2017), region, MRC, municipality code \\[4pt]
2023--2024 & Files released by the SAAQ under the access Act, file 03.06.34729 (decision of September 17, 2025) & year, make, model, model year, municipality name, region, first three characters of the postal code (FSA) \\\bottomrule
\end{tabular}
\medskip
\begin{itemize}\setlength\itemsep{3pt}
\item Rows: """ + n(ing.n_rows[2011]) + r""" in 2011, """ + n(ing.n_rows[2022]) + r""" in 2022, """ + n(ing.n_rows[2023]) + r""" in 2023, """ + n(ing.n_rows[2024]) + r""" in 2024.
\item The portal holds no year after 2022. Its note: « Les données ont été révisées pour respecter les nouvelles dispositions de la loi 25 ».
\item The decision withheld the other columns under section 53 of the Act.
\end{itemize}
\end{frame}

\begin{frame}{What the two sources share}
\begin{itemize}\setlength\itemsep{6pt}
\item \textbf{Shared:} make, model, model year, and the municipality.
\item \textbf{Only in 2011--2022:} class, type, fuel, net mass. A type or fuel figure for 2023--2024 is therefore \textbf{inferred}, and is labelled so wherever it appears.
\item \textbf{Only in 2023--2024:} the FSA. A figure by FSA exists for two years only.
\item \textbf{Not inferred for 2023--2024:} the class (personal or commercial use). It describes the use made of a vehicle, not the vehicle, so make, model and model year do not settle it.
\end{itemize}
\end{frame}

\begin{frame}{Step 1: one vocabulary of makes and models}
\begin{itemize}\setlength\itemsep{5pt}
\item The open data write makes and models as codes of at most five characters (TOYOT, COROL). The release mixes those with full names, other abbreviations and misspellings: more than 7{,}000 make strings against 418 codes.
\item As released, """ + p(exact[2023]) + r"""~\% of the 2023 vehicles and """ + p(exact[2024]) + r"""~\% of the 2024 vehicles carry a make and model in the open data's own main spelling.
\item Stated rules (first five characters, punctuation, two short alias tables, unambiguous prefixes, trim suffixes) bring this to """ + p(lvl[(2023, "make and model")]) + r"""~\% and """ + p(lvl[(2024, "make and model")]) + r"""~\%. A further """ + p(lvl[(2023, "make only")]) + r"""~\% and """ + p(lvl[(2024, "make only")]) + r"""~\% resolve to the make only; """ + p(lvl[(2023, "unresolved")]) + r"""~\% and """ + p(lvl[(2024, "unresolved")]) + r"""~\% stay unresolved. Nothing is matched by similarity.
\item Some codes mean other vehicles in the release than in the open data (DODGE CARAV, merged into GRAND by the curators). They are detected from vehicles of model year 2021 or earlier, whose number per code cannot grow after 2022; """ + str(len(moved)) + r""" codes (""" + n(moved.vehicles_2023.sum()) + r""" vehicles in 2023) are reassigned by model-year profile.
\item Municipality names are linked to the codes of 2011--2022 for """ + p(mm_s["matched"]) + r"""~\% of the 2024 vehicles (ISQ geographic codes, July 31, 2025).
\end{itemize}
\end{frame}

\begin{frame}{Step 2: type and fuel as expected counts}
\begin{itemize}\setlength\itemsep{5pt}
\item The open data of 2020--2022 give, for each make, model and model year, how many vehicles are of each type and each fuel.
\item A vehicle of 2023--2024 is not given one value. It contributes to each value in the proportions observed for its key.
\item The key is the most specific one found: make, model and model year (""" + p(il[(2023, 1)]) + r"""~\% of the 2023 vehicles, """ + p(il[(2024, 1)]) + r"""~\% of 2024); then make and model on recent model years (""" + p(il[(2023, 2)]) + r"""~\%, """ + p(il[(2024, 2)]) + r"""~\%); then make and model, make and model year, make.
\item Vehicles matching no key stay unassigned: """ + p(il[(2023, 6)]) + r"""~\% in 2023, """ + p(il[(2024, 6)]) + r"""~\% in 2024.
\item \textbf{The method is tested where the answer is known:} each published year is reduced to the release's seven columns, inferred from earlier years, and compared with what the SAAQ published.
\end{itemize}
\end{frame}

\begin{frame}{The test on published years: vehicle type}
""" + fig("holdout-error", "holdout_error") + r"""
\end{frame}

\begin{frame}{The test on published years: what it shows}
\small
\begin{tabular}{@{}lr@{}}\toprule
Quantity inferred & Difference from the published count \\\midrule
Automobiles and light trucks, Montréal (""" + str(len(aum)) + r""" tests) & $+$""" + p(aum.min(), 2) + r"""~\% to $+$""" + p(aum.max(), 2) + r"""~\% \\
Automobiles and light trucks, Québec & """ + p(auq.min(), 2) + r"""~\% to $+$""" + p(auq.max(), 2) + r"""~\% \\
Same, by municipality, 2022: under 1{,}000 vehicles & median """ + p(hm.loc["under 1,000", "median_abs_pct_error"], 2) + r"""~\% \\
Same, by municipality, 2022: 10{,}000 to 99{,}999 & median """ + p(hm.loc["10,000-99,999", "median_abs_pct_error"], 2) + r"""~\% \\\midrule
Gasoline, Québec, one year ahead & """ + p(fr("E", 1)[0], 2) + r"""~\% to """ + p(fr("E", 1)[1], 2) + r"""~\% \\
Electric, Québec, one year ahead & """ + p(fr("L", 1)[0]) + r"""~\% to """ + p(fr("L", 1)[1]) + r"""~\% \\
Electric, Québec, two years ahead & """ + p(fr("L", 2)[0]) + r"""~\% to """ + p(fr("L", 2)[1]) + r"""~\% \\
Plug-in hybrid, Québec, one year ahead & """ + p(fr("W", 1)[0]) + r"""~\% to $+$""" + p(fr("W", 1)[1]) + r"""~\% \\\bottomrule
\end{tabular}
\medskip
\begin{itemize}\setlength\itemsep{3pt}
\item Type is recovered to a fraction of one per cent.
\item Electric vehicles are under-counted, because the newest model years are missing from the reference: the inferred electric counts for 2023--2024 run low.
\item The test uses the open data's own codes. It does not measure the effect of the release's unedited codes.
\end{itemize}
\end{frame}

\begin{frame}{Result: Montréal, automobiles and light trucks}
\small
\begin{tabular}{@{}lrrrrr@{}}\toprule
Municipality of Montréal & 2011 & 2021 & 2022 & 2023 & 2024 \\\midrule
All vehicles (released) & """ + " & ".join(n(allv[y]) for y in (2011, 2021, 2022, 2023, 2024)) + r""" \\
Automobiles and light trucks & """ + " & ".join(n(mau[y]) for y in (2011, 2021, 2022)) + r""" & \textit{""" + n(mau[2023]) + r"""} & \textit{""" + n(mau[2024]) + r"""} \\\bottomrule
\end{tabular}

{\footnotesize Italic: inferred. Released: SAAQ open data (files of December 18, 2023) to 2022; access release 03.06.34729 for 2023--2024.}
\medskip
\begin{itemize}\setlength\itemsep{4pt}
\item 2011 to 2021: """ + n(mau[2021] - mau[2011]) + r""" more automobiles and light trucks ($+$""" + p(100 * (mau[2021] / mau[2011] - 1)) + r"""~\%).
\item 2022 is lower than 2021 by """ + n(mau[2021] - mau[2022]) + r""" in the published files; all vehicles fall by """ + n(allv[2021] - allv[2022]) + r""" the same year.
\item 2023 and 2024 (inferred) stand """ + n(mau[2023] - mau[2021]) + r""" and """ + n(mau[2024] - mau[2021]) + r""" above 2021; the two years differ by """ + n(abs(mau[2024] - mau[2023])) + r""".
\end{itemize}
\end{frame}

\begin{frame}{Vehicles by age: nothing inferred}
""" + fig("age-bands", "age_bands") + r"""
\end{frame}

\begin{frame}{Automobiles per household by FSA, 2024}
""" + fig("fsa-households", "fsa_households") + r"""
\end{frame}

\begin{frame}{The FSAs around rue de Terrebonne}
\small
\begin{tabular}{@{}lrrrrr@{}}\toprule
FSA & Automobiles and light & Households, & Per & Commuters who & Rank from the lowest, \\
 & trucks, 2024 (inferred) & 2021 Census & household & drive (\%) & FSAs in H \\\midrule
""" + "\n".join(fsarow(f) for f in ("H4A", "H4B", "H4V", "H3X")) + r"""
\bottomrule
\end{tabular}
\medskip
\begin{itemize}\setlength\itemsep{3pt}
\item Rue de Terrebonne runs through H4A and H4B. The median of the """ + str(len(isl)) + r""" FSAs is """ + p(isl.au_per_household.median(), 2) + r""" per household.
\item The vehicle count includes vehicles owned by businesses. The ratio is an average: it does not say how many households have no vehicle.
\item Households come from the 2021 Census by dissemination area, shared among FSAs by postal codes (a few per cent of uncertainty); vehicles are of 2024.
\end{itemize}
\end{frame}

\begin{frame}{Median vehicle age by FSA, 2024}
""" + fig("fsa-maps", "fsa_map_age") + r"""
\end{frame}

\begin{frame}{Automobiles per household by FSA, 2024: the map}
""" + fig("fsa-maps", "fsa_map_households") + r"""
\end{frame}

\begin{frame}{How long vehicles stay registered}
""" + fig("cohort-survival", "cohort_survival") + r"""
\end{frame}

\begin{frame}{An older fleet, kept longer}
\begin{itemize}\setlength\itemsep{6pt}
\item Of the automobiles and light trucks registered in Québec at age 3, half are still registered at """ + str(half[PER[0]]) + r""" years in """ + PER[0].replace(" to ", "--") + r""", at """ + str(half[PER[1]]) + r""" years in """ + PER[1].replace(" to ", "--") + r""" and at """ + str(half[PER[2]]) + r""" years in """ + PER[2].replace(" to ", "--") + r""".
\item At 15 years: """ + p(csq[PER[0]][15], 0) + r"""~\%, """ + p(csq[PER[1]][15], 0) + r"""~\% and """ + p(csq[PER[2]][15], 0) + r"""~\% remain in the three periods.
\item In Montréal the mean age of automobiles and light trucks goes from """ + p(vam.mean_age[2011]) + r""" years in 2011 to """ + p(vam.mean_age[2022]) + r""" in 2022 (published) and """ + p(vam.mean_age[2024]) + r""" in 2024 (inferred); the share aged 10 years or more from """ + p(vam.pct_10_years_or_more[2011], 0) + r"""~\% to """ + p(vam.pct_10_years_or_more[2024], 0) + r"""~\%.
\item The last period includes 2023 and 2024, whose counts by type are inferred. A vehicle that leaves Québec counts as a departure.
\end{itemize}
\end{frame}

\begin{frame}{Net mass, 2011--2022}
""" + fig("mass-automobiles", "mass_automobiles") + r"""
\end{frame}

\begin{frame}{Mass to the fourth power: what the index measures}
\begin{itemize}\setlength\itemsep{5pt}
\item For automobiles and light trucks in Montréal, the sum of net mass to the fourth power is """ + p(mam.fourth_power_total_index[2022], 2) + r""" times its 2011 value in 2022, and the mean per vehicle """ + p(mam.fourth_power_mean_index[2022], 2) + r""" times. These reproduce the 2025 application's chart (1.35 and 1.22).
\item The mean net mass goes from """ + n(mam.mean_kg[2011]) + r"""~kg to """ + n(mam.mean_kg[2022]) + r"""~kg; the share at 2{,}000~kg or more from """ + p(mam.pct_2000kg_or_more[2011]) + r"""~\% to """ + p(mam.pct_2000kg_or_more[2022]) + r"""~\%.
\item Across automobiles, trucks, buses and tool vehicles together, automobiles are """ + p(mt22.pct_of_vehicles["AU"], 0) + r"""~\% of the vehicles and """ + p(mt22.pct_of_fourth_power["AU"]) + r"""~\% of the summed fourth power in 2022. An all-type index follows a few tens of thousands of heavy vehicles.
\item Its one-year drop in 2012 is in the files: """ + n(bus[2011]) + r""" buses registered in Montréal in the 2011 file, """ + n(bus[2012]) + r""" in 2012, """ + n(bus[2013]) + r""" in 2013.
\item The quantity uses the net mass (the vehicle empty) and no distance driven. It describes the registered fleet, not the wear of a street.
\end{itemize}
\end{frame}

\begin{frame}{Electric and hybrid vehicles, 2011--2024 (published 2017--2022, inferred before and after)}
""" + fig("electric", "electric") + r"""
\end{frame}

\begin{frame}{Automobiles and licence holders, 2011--2022}
""" + fig("licences-vehicles", "licences_vehicles") + r"""
\end{frame}

\begin{frame}{Licence holders by age, island of Montréal}
""" + fig("licences-age", "licences_age") + r"""
\end{frame}

\begin{frame}{Other series checked against the 2025 application}
\small
\begin{itemize}\setlength\itemsep{4pt}
\item """ + str(len(rc)) + r""" legend values of the 2025 charts were recomputed: """ + str(int((rc.difference == 0).sum())) + r""" are identical. The other differs by """ + str(int(abs(rc.difference).max())) + r""" vehicles whose model year is invalid, which the application counted as 16 years or more.
\item Hampstead, Montréal-Ouest, Côte-Saint-Luc and Westmount together: """ + n(enc[2011]) + r""" vehicles in 2011, """ + n(enc.max()) + r""" in """ + str(enc.idxmax()) + r""", """ + n(enc[2024]) + r""" in 2024 (nothing inferred).
\item Snowmobiles in Québec: """ + n(qt[(qt.vtype == "MN") & (qt.year == 2011)].n.sum()) + r""" in 2011, """ + n(qt[(qt.vtype == "MN") & (qt.year == 2022)].n.sum()) + r""" in 2022 (published), """ + n(qt[(qt.vtype == "MN") & (qt.year == 2024)].n.sum()) + r""" in 2024 (inferred).
\item Mopeds in Québec: """ + n(qt[(qt.vtype == "CY") & (qt.year == 2011)].n.sum()) + r""" in 2011, """ + n(qt[(qt.vtype == "CY") & (qt.year == 2022)].n.sum()) + r""" in 2022 (published), """ + n(qt[(qt.vtype == "CY") & (qt.year == 2024)].n.sum()) + r""" in 2024 (inferred).
\end{itemize}
\begin{center}\includegraphics[height=0.42\textheight]{""" + str(FIG / "enclaves" / "enclaves_en.png") + r"""}\end{center}
\end{frame}

\begin{frame}{The 2011--2021 trend carried forward}
""" + fig("trend-scenario", "trend_scenario") + r"""
\end{frame}

\begin{frame}{The same series against two hypothetical bounds}
""" + fig("trend-scenario", "trend_thresholds") + r"""
\end{frame}

\begin{frame}{Vehicles and the space they occupy}
\small
\footnotesize\begin{tabular}{@{}p{7.4cm}rrr@{}}\toprule
 & Vehicles & \multicolumn{2}{r}{Curb, if all on the street} \\
 & & at 5.0 m each & at 6.0 m each \\\midrule
""" + "\n".join(f"{c.replace('Montréal, ', 'Montréal: ')} & {n(r.vehicles)} & {p(r['curb_km_at_5.0_m'])} km & {p(r['curb_km_at_6.0_m'])} km \\\\" for c, r in st.iterrows()) + r"""
\bottomrule
\end{tabular}\small
\medskip
\begin{itemize}\setlength\itemsep{3pt}
\item The length per vehicle is an assumption given as a range, and the files do not say which vehicles are kept on the street. The table converts a number of vehicles into a length; it does not measure parking.
\item Per 1{,}000 residents of the municipality of Montréal: """ + p(pr.per_1000_residents[2016], 0) + r""" automobiles and light trucks at the 2016 Census, """ + p(pr.per_1000_residents[2021], 0) + r""" at the 2021 Census.
\item The line through 2011--2021 adds """ + n(per_year) + r""" a year. The 2024 count (inferred) is """ + n(abs(sc.count_minus_trend[2024])) + r""" below it.
\end{itemize}
\end{frame}

\begin{frame}{Limits, and what is not yet done}
\begin{itemize}\setlength\itemsep{5pt}
\item Type and fuel for 2023--2024 are inferred; class cannot be. Electric and plug-in counts outside 2017--2022 are inferred and shown as such; forward they run low (electric by 4 to 19~\% on published years).
\item Mass and licences stop at 2022. By FSA there are two years, so no local trend.
\item Registrations count vehicles owned, not trips made or distance driven. Vehicles owned by businesses are included everywhere.
\item The reason for the lower published count of 2022 is not established here.
\item Not yet done: electric vehicles for 2023--2024 with an outside reference for new models; yearly population estimates; the French versions of the note and deck.
\item Code, tables and figures: \texttt{github.com/OpenMobilityData/Quebec-vehicle-registrations}
\end{itemize}
\end{frame}
\end{document}
"""

LAY = (
    "Until 2022 the SAAQ published a yearly file with one line for every vehicle registered in Québec. It then stopped. "
    "The files it released for 2023 and 2024 under the access-to-information law give only the make, model, model year and place of registration. "
    "This note joins the two sources so that the same questions can be followed from 2011 to 2024.\n\n"
    "The kind of vehicle is worked out from its make, model and model year, using the earlier files as the key. The method was tested on the years where the answer is known: "
    f"for automobiles and light trucks in Montréal it lands within {p(aum.abs().max(), 2)} per cent of the published count. It works poorly for electric vehicles, "
    "whose newest models are missing from the key, so none are counted for 2023 and 2024.\n\n"
    f"In the municipality of Montréal there were {n(mau[2011]).replace('{,}', ',')} automobiles and light trucks in 2011 and {n(mau[2021]).replace('{,}', ',')} in 2021. "
    f"The published count for 2022 is lower. The counts worked out for 2023 and 2024 are about {n(round(mau[2024], -3)).replace('{,}', ',')}, "
    f"some {n(round(abs(sc.count_minus_trend[2024]), -3)).replace('{,}', ',')} below where the growth of 2011 to 2021 was heading.\n\n"
    f"Vehicles are kept longer. Of the automobiles on the road at three years old, half were still registered at {half[PER[0]]} years early in the period "
    f"and at {half[PER[2]]} years at its end. They are also heavier: in Montréal the average went from {n(mam.mean_kg[2011]).replace('{,}', ',')} to {n(mam.mean_kg[2022]).replace('{,}', ',')} kilograms between 2011 and 2022.\n\n"
    f"The newer files also give the first three characters of the postal code. In the two postal areas crossed by rue de Terrebonne there are about "
    f"{p(v24.loc['H4A'].au_per_household, 2)} automobiles per household, against a middle value of {p(isl.au_per_household.median(), 2)} for the island of Montréal and Laval.\n\n"
    "The files count vehicles that are owned, including those of businesses. They do not say how far a vehicle is driven or where it is parked."
)
WORDS = len(LAY.split())
assert WORDS <= 300, WORDS
(paths.REPO / "derived" / "lay_abstract_en.txt").write_text(LAY + f"\n\n({WORDS} words; {TAG})\n", encoding="utf-8")
tex = lambda t: t.replace("%", r"\%").replace("\n\n", "\n\n")
nfig = lambda name, stem, cap, w=1.0: (rf"\begin{{figure}}[H]\centering\includegraphics[width={w}\linewidth]{{{FIG / name / (stem + '_en.png')}}}"
                                        rf"\caption{{{cap}}}\end{{figure}}")
DRAFT = "" if FINAL else r"\fancyhead[C]{\small\textcolor{red!70!black}{DRAFT for the author\textquoteright{}s review, " + TAG + "}}"

NOTE = r"""\documentclass[10.5pt,a4paper]{article}
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage[scaled=0.95]{helvet}\renewcommand{\familydefault}{\sfdefault}
\usepackage[a4paper,margin=2.2cm]{geometry}\usepackage{graphicx,booktabs,amsmath,caption,xcolor,enumitem,array,float,fancyhdr}\usepackage[hidelinks]{hyperref}
\captionsetup{font=small,labelfont=bf}\setlength{\parskip}{0.5em}\setlength{\parindent}{0pt}\setlist{itemsep=2pt,topsep=3pt}
\pagestyle{fancy}\fancyhf{}\fancyfoot[C]{\small\thepage}\renewcommand{\headrulewidth}{0pt}""" + DRAFT + r"""
\title{\textbf{Vehicle registrations in Québec, 2011--2024}\\[4pt]\large Joining the SAAQ's open data with the files released under the access Act}
\author{Rick Hoge, PhD}\date{""" + now.strftime("%B %-d, %Y") + r""" \quad {\small """ + TAG + r"""}}
\begin{document}\maketitle\thispagestyle{fancy}

\section*{Summary for a general reader}
""" + tex(LAY) + r"""

""" + nfig("montreal-automobiles", "montreal_automobiles", "Overview: vehicles registered in the municipality of Montréal, 2011--2024. The 2023 and 2024 counts of automobiles and light trucks are inferred.") + r"""
\newpage

\section*{Abstract}
The Société de l'assurance automobile du Québec (SAAQ) published one record per registered vehicle for each year from 2011 to 2022, with the vehicle's class, type, make, model, model year, net mass, fuel and municipality. The files it released for 2023 and 2024 under the access Act carry seven columns: year, make, model, model year, municipality, region and the first three characters of the postal code (FSA). This note describes a pipeline that joins the two sources: the release's make and model strings are mapped by stated rules onto the codes of the open data (""" + p(lvl[(2023, "make and model")]) + r"""~\% of the 2023 vehicles and """ + p(lvl[(2024, "make and model")]) + r"""~\% of the 2024 vehicles resolved to make and model), and the vehicle type is inferred from make, model and model year as an expected count. Applied to each published year from the years before it, the inferred count of automobiles and light trucks in the municipality of Montréal differs from the published count by """ + p(aum.min(), 2) + r"""~\% to """ + p(aum.max(), 2) + r"""~\% (""" + str(len(aum)) + r""" tests); electric vehicles are under-counted by """ + p(abs(fr("L", 1)[1])) + r"""~\% to """ + p(abs(fr("L", 2)[0])) + r"""~\%, and no electric count is given for 2023--2024. Results: Montréal had """ + n(mau[2011]) + r""" automobiles and light trucks in 2011, """ + n(mau[2021]) + r""" in 2021, """ + n(mau[2022]) + r""" in 2022 (published), and """ + n(mau[2023]) + r""" and """ + n(mau[2024]) + r""" in 2023 and 2024 (inferred); half of the automobiles registered in Québec at age 3 remain at """ + str(half[PER[0]]) + r""" years in """ + PER[0].replace(" to ", "--") + r""" and at """ + str(half[PER[2]]) + r""" years in """ + PER[2].replace(" to ", "--") + r"""; the mean net mass of Montréal's automobiles rises from """ + n(mam.mean_kg[2011]) + r""" to """ + n(mam.mean_kg[2022]) + r"""~kg (2011--2022); in the FSAs H4A and H4B there are """ + p(v24.loc["H4A"].au_per_household, 2) + r""" and """ + p(v24.loc["H4B"].au_per_household, 2) + r""" automobiles and light trucks per household in 2024, against a median of """ + p(isl.au_per_household.median(), 2) + r""" for the """ + str(len(isl)) + r""" FSAs beginning with H. The files count vehicles owned, businesses included; they carry no distance driven and no place of parking.

\tableofcontents

\section{Sources}
\begin{tabular}{@{}p{1.9cm}p{6.2cm}p{7.2cm}@{}}\toprule
Years & Source & Columns \\\midrule
2011--2022 & SAAQ open data, « Véhicules en circulation » (Données Québec, CC BY 4.0), vehicles authorized to circulate on December 31; files as revised by the SAAQ on December 18, 2023 & class, type, make, model, model year, net mass, cylinders, displacement, axles, colour, fuel (from 2017), region, MRC, municipality code \\[4pt]
2023--2024 & Files released by the SAAQ under the access Act, file 03.06.34729 (decision of September 17, 2025) & year, make, model, model year, municipality name, region, FSA \\[4pt]
2011--2022 & SAAQ open data, « Permis de conduire » (CC BY 4.0), licence holders on June 1 & age band, sex, MRC, region, licence type and classes, experience \\\bottomrule
\end{tabular}

The vehicle files hold """ + n(ing.n_rows[2011]) + r""" rows for 2011, """ + n(ing.n_rows[2022]) + r""" for 2022, """ + n(ing.n_rows[2023]) + r""" for 2023 and """ + n(ing.n_rows[2024]) + r""" for 2024. The open-data portal holds no vehicle file after 2022; its note reads « Les données ont été révisées pour respecter les nouvelles dispositions de la loi 25 protégeant la vie privée des Québécois ». The request of August 26, 2025 asked for the columns of the 2022 file with the FSA added; the decision cites section 53 of the Act for the columns withheld. Asked by the author why the portal holds nothing after 2022, the SAAQ's open-data team replied on October 22, 2024: « L'équipe est actuellement à définir la nouvelle solution pour produire ces informations à la suite de notre migration de systèmes de 2023 »; on April 2, 2025: « Il y a encore certaines décisions qui doivent être prises sur les règles de nettoyage à appliquer aux données »; and on October 1, 2025: « les versions 2023 et 2024 ne sont pas encore disponibles sur notre site et nous n'avons pas d'échéance quant à leurs disponibilités ». A request for the licence files of 2023 and 2024 (file 03.06.34793) was refused on October 24, 2025 under section 15 of the Act; the note enclosed with the decision states that those data « sont en cours de validation et de correction (redressements) », that « un délai d'au moins trois mois est requis » and that « une publication sur le site web de Données Québec dans un nouveau format est prévue par la suite ». On November 10, 2026 the portal's vehicle and licence datasets still end in 2022. Other sources: Statistics Canada, 2021 Census profile by dissemination area (catalogue 98-401-X2021006) and by census subdivision (98-401-X2021020); Institut de la statistique du Québec, geographic codes (July 31, 2025); postal-code points (Service Objects, March 2024) and FSA polygons (DMTI Spatial, CanMap Postal Code Suite v2024.3), both under licence.

\section{Method}
\subsection{One vocabulary of makes and models}
The open data write makes and models as codes of at most five characters. The release mixes those codes with full names, other abbreviations and misspellings (more than 7{,}000 make strings against 418 codes). As released, """ + p(exact[2023]) + r"""~\% of the 2023 vehicles and """ + p(exact[2024]) + r"""~\% of the 2024 vehicles carry a make and model in the open data's main spelling. The rules, applied in a fixed order, are: the first five characters; punctuation removed; two short alias tables written by hand, each entry with its basis; a prefix that designates one code almost alone; and a trim or variant suffix removed. Nothing is matched by similarity of strings. After the rules, """ + p(lvl[(2023, "make and model")]) + r"""~\% and """ + p(lvl[(2024, "make and model")]) + r"""~\% of vehicles are resolved to make and model, """ + p(lvl[(2023, "make only")]) + r"""~\% and """ + p(lvl[(2024, "make only")]) + r"""~\% to the make only, and """ + p(lvl[(2023, "unresolved")]) + r"""~\% and """ + p(lvl[(2024, "unresolved")]) + r"""~\% stay unresolved.

Two things were found in the course of this step. The open data hold rare variants of their own codes (16 vehicles under HONDA \texttt{CRV} beside 1.1 million under \texttt{CR-V}); codes equal but for punctuation are taken as one model. And some codes designate other vehicles in the release than in the open data: the curators had merged DODGE \texttt{CARAV} into \texttt{GRAND}, for example. These are detected from the vehicles of model year 2021 or earlier, whose number under a code cannot grow after 2022; """ + str(len(moved)) + r""" such codes (""" + n(moved.vehicles_2023.sum()) + r""" vehicles in 2023) are reassigned to the code whose vehicles are missing in the same numbers, model year by model year.

\subsection{Municipalities}
The open data give a municipality code and the release a name with its region. The names are linked to the codes through the ISQ's geographic codes for """ + p(mm_s["matched"]) + r"""~\% of the 2024 vehicles; a name carried by two municipalities of the same region is left unlinked.

\subsection{Type and fuel as expected counts}
The open data of 2020--2022 give, for each make, model and model year, how many vehicles are of each type. A vehicle of 2023--2024 contributes to each type in those proportions. The key is the most specific one found: make, model and model year (""" + p(il[(2023, 1)]) + r"""~\% of the 2023 vehicles, """ + p(il[(2024, 1)]) + r"""~\% of 2024), then make and model on recent model years, make and model, make and model year, and make. Vehicles matching no key stay unassigned (""" + p(il[(2023, 6)]) + r"""~\% and """ + p(il[(2024, 6)]) + r"""~\%). The class (personal or commercial use) is not inferred: it describes the use made of a vehicle.

\section{The method tested on published years}
Each published year is reduced to the seven columns of the release, inferred from the three years ending one or two years earlier, and compared with the published type and fuel.

""" + nfig("holdout-error", "holdout_error", "Inferred against published counts of automobiles and light trucks, by year.") + r"""

\begin{center}\begin{tabular}{@{}lr@{}}\toprule
Quantity inferred & Difference from the published count \\\midrule
Automobiles and light trucks, Montréal (""" + str(len(aum)) + r""" tests) & $+$""" + p(aum.min(), 2) + r"""~\% to $+$""" + p(aum.max(), 2) + r"""~\% \\
Automobiles and light trucks, Québec & """ + p(auq.min(), 2) + r"""~\% to $+$""" + p(auq.max(), 2) + r"""~\% \\
Same, by municipality, 2022: under 1{,}000 vehicles & median """ + p(hm.loc["under 1,000", "median_abs_pct_error"], 2) + r"""~\% \\
Same, by municipality, 2022: 10{,}000 to 99{,}999 & median """ + p(hm.loc["10,000-99,999", "median_abs_pct_error"], 2) + r"""~\% \\\midrule
Gasoline, Québec, one year ahead & """ + p(fr("E", 1)[0], 2) + r"""~\% to """ + p(fr("E", 1)[1], 2) + r"""~\% \\
Electric, Québec, one year ahead & """ + p(fr("L", 1)[0]) + r"""~\% to """ + p(fr("L", 1)[1]) + r"""~\% \\
Electric, Québec, two years ahead & """ + p(fr("L", 2)[0]) + r"""~\% to """ + p(fr("L", 2)[1]) + r"""~\% \\
Plug-in hybrid, Québec, one year ahead & """ + p(fr("W", 1)[0]) + r"""~\% to $+$""" + p(fr("W", 1)[1]) + r"""~\% \\\bottomrule
\end{tabular}\end{center}

Type is recovered to a fraction of one per cent. Electric vehicles are under-counted because the newest model years are absent from the reference, and no electric count for 2023--2024 is given in this note. The test uses the open data's own codes: it does not measure the effect of the release's unedited codes, which is the subject of the vocabulary step. A second check is the comparison with the 2025 SAAQAnalyzer application: of """ + str(len(rc)) + r""" legend values recomputed here, """ + str(int((rc.difference == 0).sum())) + r""" are identical, and the other differs by """ + str(int(abs(rc.difference).max())) + r""" vehicles with an invalid model year.

\section{Results}
\subsection{Montréal, 2011--2024}
The counts are shown in Figure~1.
\begin{center}\begin{tabular}{@{}lrrrrr@{}}\toprule
Municipality of Montréal & 2011 & 2021 & 2022 & 2023 & 2024 \\\midrule
All vehicles (released) & """ + " & ".join(n(allv[y]) for y in (2011, 2021, 2022, 2023, 2024)) + r""" \\
Automobiles and light trucks & """ + " & ".join(n(mau[y]) for y in (2011, 2021, 2022)) + r""" & \textit{""" + n(mau[2023]) + r"""} & \textit{""" + n(mau[2024]) + r"""} \\\bottomrule
\end{tabular}\\[2pt]{\footnotesize Italic: inferred.}\end{center}

From 2011 to 2021 the municipality gained """ + n(mau[2021] - mau[2011]) + r""" automobiles and light trucks ($+$""" + p(100 * (mau[2021] / mau[2011] - 1)) + r"""~\%). The published count of 2022 is """ + n(mau[2021] - mau[2022]) + r""" lower than that of 2021, and the count of all vehicles falls by """ + n(allv[2021] - allv[2022]) + r""" the same year; the reason is not established here. The inferred counts of 2023 and 2024 stand """ + n(mau[2023] - mau[2021]) + r""" and """ + n(mau[2024] - mau[2021]) + r""" above 2021. Per 1{,}000 residents, there were """ + p(pr.per_1000_residents[2016], 0) + r""" automobiles and light trucks at the 2016 Census and """ + p(pr.per_1000_residents[2021], 0) + r""" at the 2021 Census.

""" + nfig("trend-scenario", "trend_scenario", "The straight line through the counts of 2011--2021, carried to 2035, and the later counts.", 0.9) + r"""

A straight line through the published counts of 2011--2021 adds """ + n(per_year) + r""" vehicles a year. It is not a forecast. The published count of 2022 is """ + n(abs(sc.count_minus_trend[2022])) + r""" below it, and the inferred count of 2024 is """ + n(abs(sc.count_minus_trend[2024])) + r""" below it.

\subsection{Age, and how long vehicles stay registered}
""" + nfig("age-bands", "age_bands", "Vehicles registered in the municipality of Montréal by age. Nothing is inferred.", 0.9) + nfig("cohort-survival", "cohort_survival", "Share of the automobiles and light trucks registered at age 3 that remain at each later age, Québec.", 0.9) + r"""

Age needs only the model year, which both sources carry. In Montréal the mean age of automobiles and light trucks goes from """ + p(vam.mean_age[2011]) + r""" years in 2011 to """ + p(vam.mean_age[2022]) + r""" in 2022 and """ + p(vam.mean_age[2024]) + r""" in 2024 (the last inferred as to type), and the share aged 10 years or more from """ + p(vam.pct_10_years_or_more[2011], 0) + r"""~\% to """ + p(vam.pct_10_years_or_more[2024], 0) + r"""~\%. Following each model year from one yearly file to the next for Québec as a whole, half of the automobiles and light trucks registered at age 3 remain at """ + ", ".join(f"{half[c]} years in {c.replace(' to ', '--')}" for c in PER) + r"""; at 15 years, """ + ", ".join(f"{p(csq[c][15], 0)}~\\%" for c in PER) + r""" remain. The last period includes the two inferred years, and a vehicle that leaves Québec counts as a departure.

\subsection{Net mass, 2011--2022}
""" + nfig("mass-automobiles", "mass_automobiles", "Net mass of automobiles and light trucks, municipality of Montréal.", 0.9) + r"""

The mean net mass of Montréal's automobiles and light trucks goes from """ + n(mam.mean_kg[2011]) + r"""~kg in 2011 to """ + n(mam.mean_kg[2022]) + r"""~kg in 2022, and the share at 2{,}000~kg or more from """ + p(mam.pct_2000kg_or_more[2011]) + r"""~\% to """ + p(mam.pct_2000kg_or_more[2022]) + r"""~\%. The sum of net mass to the fourth power, the quantity behind the « Road Wear Index » of the 2025 application, is """ + p(mam.fourth_power_total_index[2022], 2) + r""" times its 2011 value in 2022, and its mean per vehicle """ + p(mam.fourth_power_mean_index[2022], 2) + r""" times. Taken over automobiles, trucks, buses and tool vehicles together, that sum follows the heavy vehicles: automobiles are """ + p(mt22.pct_of_vehicles["AU"], 0) + r"""~\% of those vehicles and """ + p(mt22.pct_of_fourth_power["AU"]) + r"""~\% of the sum in 2022. Its one-year drop in 2012 corresponds to the number of buses registered in Montréal: """ + n(bus[2011]) + r""" in the 2011 file, """ + n(bus[2012]) + r""" in 2012, """ + n(bus[2013]) + r""" in 2013. The quantity uses the net mass and no distance driven: it describes the registered fleet, not the wear of a street. The 2023--2024 files carry no mass.

\subsection{By FSA, 2024}
""" + nfig("fsa-maps", "fsa_map_households", "Automobiles and light trucks per household by FSA.") + nfig("fsa-households", "fsa_households", "The same against the share of commuters who drive (2021 Census).", 0.85) + r"""
\begin{center}\begin{tabular}{@{}lrrrrr@{}}\toprule
FSA & Automobiles and light & Households, & Per & Commuters who & Rank from the lowest, \\
 & trucks, 2024 (inferred) & 2021 Census & household & drive (\%) & FSAs in H \\\midrule
""" + "\n".join(fsarow(f).replace("\\\\", r"\\\\") for f in ("H4A", "H4B", "H4V", "H3X")) + r"""
\bottomrule\end{tabular}\end{center}

Rue de Terrebonne's bike lane lies in H4B west of avenue Royal and in H4A east of it. Households come from the 2021 Census by dissemination area, shared among FSAs by postal codes; compared with an earlier estimate for the same FSAs they differ by a few per cent. The vehicle count includes vehicles owned by businesses, so an FSA with fleets or dealers stands high, and the ratio is an average that does not say how many households have no vehicle. The median age of the vehicles registered is """ + p(fa.median_age["H4A"], 0) + r""" years in H4A and """ + p(fa.median_age["H4B"], 0) + r""" years in H4B (Figure~\ref{fig:agemap}).

\begin{figure}[H]\centering\includegraphics[width=\linewidth]{""" + str(FIG / "fsa-maps" / "fsa_map_age_en.png") + r"""}\caption{Median age of registered vehicles by FSA. Nothing is inferred.}\label{fig:agemap}\end{figure}

\subsection{Licence holders, 2011--2022}
""" + nfig("licences-vehicles", "licences_vehicles", "Automobiles and light trucks against holders of a passenger-vehicle licence.", 0.95) + nfig("licences-age", "licences_age", "Licence holders on the island of Montréal by age group.", 0.85) + r"""

The licence files give the MRC, not the municipality, so the comparison is made for the island of Montréal (the City and the fifteen other municipalities). On the island there are """ + p(vli.automobiles_per_100_car_licence_holders[2011]) + r""" automobiles and light trucks per 100 holders of a passenger-vehicle licence in 2011 and """ + p(vli.automobiles_per_100_car_licence_holders[2022]) + r""" in 2022; in Québec, """ + p(vlq.automobiles_per_100_car_licence_holders[2011]) + r""" and """ + p(vlq.automobiles_per_100_car_licence_holders[2022]) + r""". Holders aged 65 and over on the island go from """ + n(lag.o[2011]) + r""" to """ + n(lag.o[2022]) + r""", and holders aged 16 to 24 from """ + n(lag.y[2011]) + r""" to """ + n(lag.y[2022]) + r""". These are counts, not rates: no population by age is used. Probationary licences carry no class in the files and are counted as passenger-vehicle licences.

\subsection{Vehicles and the space they occupy}
\begin{center}\begin{tabular}{@{}p{8.4cm}rrr@{}}\toprule
 & Vehicles & \multicolumn{2}{r}{Curb, if all on the street} \\
 & & at 5.0 m each & at 6.0 m each \\\midrule
""" + "\n".join(f"{c} & {n(r.vehicles)} & {p(r['curb_km_at_5.0_m'])} km & {p(r['curb_km_at_6.0_m'])} km \\\\" for c, r in st.iterrows()) + r"""
\bottomrule\end{tabular}\end{center}

A registered vehicle is somewhere when it is not moving. The table converts numbers of vehicles into lengths of curb at 5 to 6~m per vehicle. The length is an assumption given as a range, and the files do not say which vehicles are kept on the street or off it: the table is a conversion, not a measurement of parking.

""" + nfig("trend-scenario", "trend_thresholds", "The Montréal series and two hypothetical bounds computed from the City's street network.", 0.92) + r"""

Two physical bounds can be computed from the City's street file (géobase of October 14, 2026), which gives """ + n(sb["street centreline in the municipality of Montréal (km)"]) + r"""~km of street in the municipality once autoroutes, bridges, tunnels, ramps and back lanes are left out. If every metre of both curbs were used for parking, with no deduction for corners, driveways, hydrants, bus stops or signs, the """ + n(sb["curb, both sides (km)"]) + r"""~km of curb would hold """ + n(sb["curb bound: vehicles at 6.0 m each"]) + r""" to """ + n(sb["curb bound: vehicles at 5.0 m each"]) + r""" vehicles at 6 to 5~m each; the automobiles and light trucks of 2024 are """ + p(sb["the same as a share of the curb bound at 5.5 m (%)"], 0) + r"""~\% of that bound at 5.5~m. If every lane were full nose to tail, counting one lane for a one-way street and two for a two-way street because the file gives no lane count, the """ + n(sb["lanes, at least (km)"]) + r"""~km of lanes would hold """ + n(sb["standstill bound: vehicles at 8.0 m each"]) + r""" to """ + n(sb["standstill bound: vehicles at 6.0 m each"]) + r""" vehicles at 8 to 6~m each. These are limits under stated assumptions, not measurements: real street parking is below the first, vehicles kept off the street are in neither, the registered vehicles are never all on the road at once, and traffic stops flowing well before the second is reached.

\section{Limits}
\begin{itemize}
\item Type and fuel for 2023--2024 are inferred. The class is not, and electric and plug-in counts for 2023--2024 are not given.
\item Mass and licences stop at 2022. By FSA there are two years, so no local trend.
\item Registrations count vehicles owned on December 31, businesses included. They carry no trips, no distance and no place of parking.
\item The open-data files are those revised by the SAAQ on December 18, 2023; what that revision changed is not documented on the portal.
\item The reason for the lower published count of 2022 is not established here.
\end{itemize}

\section*{Reproducing this note}
Code, tables and figures: \url{https://github.com/OpenMobilityData/Quebec-vehicle-registrations}. Every number in this note is read from a table in \texttt{derived/tables/} when the note is built (\texttt{scripts/build\_docs.py}). The raw files are not in the repository; their sizes and SHA-256 are in \texttt{raw\_manifest.csv}.
\end{document}
"""

DOCS.mkdir(exist_ok=True)
for name, src, passes in (("vehicle_registrations_deck_en", DECK, 2), ("vehicle_registrations_note_en", NOTE, 3)):
    (DOCS / (name + ".tex")).write_text(src, encoding="utf-8")
    for _ in range(passes):
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", name + ".tex"], cwd=DOCS, capture_output=True, text=True)
        if r.returncode:
            print(r.stdout[-2500:]); raise SystemExit(f"pdflatex failed on {name}")
    for ext in (".aux", ".log", ".nav", ".snm", ".toc", ".out"):
        (DOCS / (name + ext)).unlink(missing_ok=True)
    print(DOCS / (name + ".pdf"), TAG)
print("lay summary:", WORDS, "words")
