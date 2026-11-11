# Québec vehicle registrations, 2011–2024

A reproducible pipeline that joins two sources of vehicle-registration records
for Québec, one row per registered vehicle, and the tables computed from them.

**Status: work in progress (November 10, 2026).** The ingestion, the vocabulary
matching, the municipality link and the inference of vehicle type and fuel are
built and measured; four figures and a draft slide deck exist. The results are
under review; the written note is not yet started.

## Sources

| Years | Source | Columns | Licence or basis |
|---|---|---|---|
| 2011–2022 | SAAQ, open data « [Véhicules en circulation](https://www.donneesquebec.ca/recherche/dataset/vehicules-en-circulation) » (Données Québec) | class, type, make, model, model year, net mass, cylinders, displacement, axles, colour, fuel (from 2017), region, MRC, municipality code | CC BY 4.0 |
| 2023–2024 | SAAQ, files released under the Act respecting access to documents held by public bodies (file 03.06.34729, decision of September 17, 2025) | year, make, model, model year, municipality name, region code, first three characters of the postal code (FSA) | released under the Act |

- The open-data files used are those on the portal on November 10, 2026. The
  SAAQ replaced them on December 18, 2023; the dataset's note reads « Les
  données ont été révisées pour respecter les nouvelles dispositions de la loi
  25 protégeant la vie privée des Québécois ». The portal holds no year after 2022.
- The raw files are not in this repository (0.7 to 0.9 GB each).
  `derived/tables/raw_manifest.csv` gives each file's size and SHA-256, and the
  download address of each open-data file.
- Census: Statistics Canada, 2021 Census profile by dissemination area
  (catalogue 98-401-X2021006). Postal-code points and FSA polygons used to share
  dissemination areas among FSAs: Service Objects (March 2024) and DMTI Spatial,
  CanMap Postal Code Suite v2024.3, both under licence and not redistributed.
- Municipality codes and names: Institut de la statistique du Québec, « Banque
  de données des codes géographiques », image of July 31, 2025 (CC BY 4.0).

## What the two sources share

Make, model and model year, and the municipality. The 2023–2024 files carry no
class, type, fuel or mass; the 2011–2022 files carry no FSA. Any type or fuel
figure for 2023–2024 in this repository is **inferred** and labelled so; any
figure by FSA exists for 2023 and 2024 only.

## Pipeline

Run with a Python that has `duckdb`, `pyarrow` and `pandas`, in this order.
`scripts/paths.py` says where the large files are expected.

| Step | Script | What it does | Tables written (`derived/tables/`) |
|---|---|---|---|
| 1 | `scripts/ingest.py` | The 14 yearly files to one Parquet file per year, one schema; nothing inferred; counts checked | `raw_manifest`, `ingest_summary`, `ingest_checks` |
| 2 | `scripts/vocabulary.py` | The make and model strings of 2023–2024 mapped by stated rules onto the codes of the open data | `vocabulary_map`, `vocabulary_coverage`, `vocabulary_review` |
| 3 | `scripts/geography.py` | Municipality names of 2023–2024 linked to the codes of 2011–2022 | `municipalities`, `municipality_match` |
| 4 | `scripts/infer.py` | Type and fuel for 2023–2024 as expected counts; the same method applied to each published year and compared with what was published | `holdout_summary`, `holdout_levels`, `holdout_municipal`, `type_by_municipality`, `fuel_by_municipality`, `type_by_fsa`, `fuel_by_fsa`, `inference_levels` |
| 5 | `scripts/census_fsa.py` | 2021 Census counts by FSA, built from dissemination areas shared among FSAs by postal codes; joined to the vehicles of 2023–2024 | `fsa_census_2021`, `fsa_vehicles_census` |

## Measurements so far

- **Ingestion.** Row counts: 7,058,605 (2022), 7,169,989 (2023), 7,189,594
  (2024). All vehicles in the municipality of Montréal: 817,880 (2022), 832,054
  (2023), 831,205 (2024). Ten counts are checked at each run (`ingest_checks.csv`).
- **Vocabulary.** The open data hold 418 make codes; the release holds more
  than 7,000 make strings. Written as released, 87.4 % (2023) and 82.0 % (2024)
  of vehicles match a make and model of the open data. After the rules: 97.1 %
  and 96.8 % at make and model, 2.4 % and 2.7 % at make only, 0.4 % and 0.5 %
  unresolved. No string is matched by similarity.
- **Municipalities.** 98.3 % of the vehicles of 2023–2024 are linked to a
  municipality code; 0.7 % carry a name shared by two municipalities of the same
  region; 1.0 % carry no municipality.
- **Type, measured on published years.** Inferring each year 2012–2022 from the
  years before it (21 tests), the count of automobiles and light trucks in
  Montréal comes out 0.05 % to 0.13 % above the published count, and for Québec
  between 0.14 % below and 0.05 % above. For 2022, the median error by
  municipality is 0.6 % under 1,000 registered vehicles and 0.1 % from 10,000.
- **Fuel, measured on published years.** Gasoline is within 0.5 %. Electric
  vehicles are under-counted: by 4 % to 8 % one year ahead and 12 % to 19 % two
  years ahead (2018–2022), because the newest model years are not in the
  reference. Plug-in hybrids range from 44 % under to 11 % over.
- **These tests use the curated strings of the open data.** They do not measure
  the effect of the unedited strings of 2023–2024. Two effects were found and
  handled in the vocabulary step: rare variants inside the open data's own
  codes (16 vehicles under HONDA `CRV` beside 1.1 million under `CR-V`), and
  codes the release uses for other vehicles than the open data do (DODGE
  `CARAV`, merged into `GRAND` by the curators; FORD `VAN`). The second kind is
  detected from vehicles of model year 2021 or earlier, whose number per code
  cannot grow after 2022, and reassigned by model-year profile
  (`vocabulary_codes_used_differently.csv`, `vocabulary_codes_reassigned.csv`).
  Check: motorhomes in Montréal, 723 published for 2022, 747 inferred for 2023.

## Figures so far (`derived/figures/<type>/`, script beside its PNG and SVG, English and French)

| Figure | What it shows |
|---|---|
| [`montreal-automobiles`](derived/figures/montreal-automobiles/montreal_automobiles_en.png) | Municipality of Montréal, 2011–2024: all vehicles, and automobiles and light trucks (published to 2022, inferred for 2023–2024) |
| [`holdout-error`](derived/figures/holdout-error/holdout_error_en.png) | The inference applied to each published year, against the published count |
| [`age-bands`](derived/figures/age-bands/age_bands_en.png) | Municipality of Montréal by vehicle age, 2011–2024 (nothing inferred) |
| [`fsa-households`](derived/figures/fsa-households/fsa_households_en.png) | Automobiles and light trucks per household by FSA (postal codes in H), 2024, against the share of commuters who drive (2021 Census) |

## Documents (`docs/`)

- [`vehicle_registrations_deck_en.pdf`](docs/vehicle_registrations_deck_en.pdf): slide deck, English, **draft under the author's review**; built by `scripts/build_docs.py`, every number read from the tables at build time.

## Layout

- `scripts/`: the pipeline; `aliases_make.csv` and `aliases_model.csv` are the
  only hand-written mappings, each with its basis.
- `derived/tables/`: the tables above (CSV).
- `access-request-03.06.34729/`: the request and the SAAQ's decision (to come).

## Author

Rick Hoge, PhD. Commits are co-authored with Claude (Anthropic), which wrote the
code under the author's direction.
