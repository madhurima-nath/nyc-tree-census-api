import os
import pandas as pd
from sodapy import Socrata
from dotenv import load_dotenv

load_dotenv()

DOMAIN = "data.cityofnewyork.us"
DATASET_ID = "uvpi-gqnh"
FIELDS = "tree_id,spc_common,tree_dbh,status,health,latitude,longitude,problems"
OUTPUT_PATH = "data/trees_manhattan.csv"


def fetch():
    client = Socrata(DOMAIN, os.getenv("NYC_APP_TOKEN"))
    results = client.get(
        DATASET_ID,
        boroname="Manhattan",
        select=FIELDS,
        limit=70000,
    )
    return pd.DataFrame.from_records(results)


def clean(df):
    df = df.dropna(subset=["tree_id", "latitude", "longitude"])
    df["health"] = df["health"].str.strip().str.title()
    df["status"] = df["status"].str.strip().str.title()
    df["spc_common"] = df["spc_common"].str.strip().str.lower()
    return df


if __name__ == "__main__":
    print("Fetching Manhattan trees from Socrata...")
    df = fetch()
    print(f"Fetched {len(df)} rows")

    df = clean(df)
    print(f"After cleaning: {len(df)} rows")

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved to {OUTPUT_PATH}")
