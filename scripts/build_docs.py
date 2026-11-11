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
\item Electric vehicles are under-counted, because the newest model years are missing from the reference. No electric count for 2023--2024 is given here.
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

\begin{frame}{Limits, and what is not yet done}
\begin{itemize}\setlength\itemsep{5pt}
\item Type and fuel for 2023--2024 are inferred; class cannot be. Electric and plug-in counts for 2023--2024 are not given.
\item By FSA there are two years, so no local trend.
\item Registrations count vehicles owned, not trips made or distance driven.
\item Not yet done: the remaining charts of the 2025 application checked against this pipeline; fleet mass and the Road Wear Index (2011--2022); scenarios for vehicle storage; driver's licences; the written note; the French versions.
\item Code, tables and figures: \texttt{github.com/OpenMobilityData/Quebec-vehicle-registrations}
\end{itemize}
\end{frame}
\end{document}
"""

DOCS.mkdir(exist_ok=True)
name = "vehicle_registrations_deck_en"
(DOCS / (name + ".tex")).write_text(DECK, encoding="utf-8")
for _ in range(2):
    r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", name + ".tex"], cwd=DOCS, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout[-2500:]); raise SystemExit("pdflatex failed")
for ext in (".aux", ".log", ".nav", ".snm", ".toc", ".out"):
    (DOCS / (name + ext)).unlink(missing_ok=True)
print(DOCS / (name + ".pdf"), TAG)
