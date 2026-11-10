# SAAQ access request 03.06.34729 (vehicles in circulation, 2023 and 2024)

| Document | Date | File |
|---|---|---|
| Request to the SAAQ's person in charge of access to documents | August 26, 2025 | [`raw/request_2025-08-26.pdf`](raw/request_2025-08-26.pdf) |
| Acknowledgment (reply due September 18, 2025) | August 29, 2025 | [`raw/acknowledgment_2025-08-29.pdf`](raw/acknowledgment_2025-08-29.pdf) |
| Decision, with the excerpt of the Act and the invoice | September 17, 2025 | [`raw/decision_and_invoice_2025-09-17.pdf`](raw/decision_and_invoice_2025-09-17.pdf) |

**What was asked.** One row per registered vehicle for 2023 and 2024, « the same
columns as provided in the 2022 table », with a column added for the first three
characters of the postal code; vehicle colour could be left out; suppression,
if any, limited to combinations of make, model and FSA with fewer than five vehicles.

**What the decision says.** Documents sent on payment of $19.00 (USB key). « We
have, however, withheld some information or documents because : Some documents
contain personal information about another person, and you have not provided
that person's authorization (see section 53 of the Act enclosed). »

**What was received.** Two CSV files, one per year, seven columns: year (2023:
year and month, `202312`), make, model, model year, municipality name,
administrative region code, FSA. 7,169,989 rows for 2023 and 7,189,594 for 2024.
Not received: class, type, net mass, cylinders, displacement, axles, colour,
fuel, MRC. The files are not in this repository (350 MB each); their sizes and
SHA-256 are in [`../derived/tables/raw_manifest.csv`](../derived/tables/raw_manifest.csv).

**Notes on the copies.** The requester's e-mail address and telephone number
are blacked out (pages treated: the request, p. 1; the acknowledgment, p. 1; the
decision, pp. 1 and 3; those pages are images). Nothing else is changed. In the
SAAQ's two letters, the office's name in the header and one line of the text
display as unreadable characters in every PDF reader tried: the files were
received that way (a font is not embedded).
