"""Where the large files live. Nothing here is in the repository.

Defaults are the owner's RAID; override with the environment variables
SAAQ_OPEN_DIR, SAAQ_ACCESS_DIR and SAAQ_PARQUET_DIR.
"""
import os
from pathlib import Path

_RAID = Path("/Volumes/Pegasus32 R8/SAAQ")
OPEN_DIR = Path(os.environ.get("SAAQ_OPEN_DIR", _RAID / "Vehicle_Registration"))
ACCESS_DIR = Path(os.environ.get("SAAQ_ACCESS_DIR", _RAID / "SAAQ_Data/Vehicles/Vehicle_Registration"))
PARQUET_DIR = Path(os.environ.get("SAAQ_PARQUET_DIR", _RAID / "pipeline/parquet"))
REPO = Path(__file__).resolve().parent.parent
TABLES = REPO / "derived" / "tables"

OPEN_YEARS = range(2011, 2023)
ACCESS_YEARS = (2023, 2024)
OPEN_URL = "https://dq-prd-bucket1.s3.ca-central-1.amazonaws.com/saaq/Vehicule_En_Circulation_{year}.csv"


def open_csv(year):
    return OPEN_DIR / f"Vehicule_En_Circulation_{year}.csv"


def access_csv(year):
    return ACCESS_DIR / f"Vehicule_En_Circulation_{year}_nonstandard.csv"


def parquet(year):
    return PARQUET_DIR / f"vehicles_{year}.parquet"
