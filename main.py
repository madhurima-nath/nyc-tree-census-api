import math
import os

import pandas as pd
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Security
from fastapi.security import APIKeyHeader

load_dotenv()

# tells FastAPI to look for this header and show an Authorize button in /docs
api_key_header = APIKeyHeader(name="x-api-key")


def verify_key(x_api_key: str = Security(api_key_header)):
    # block the request if the key is missing or doesn't match the one in .env
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Unauthorized")


# apply verify_key to every endpoint globally — no need to add it to each function
app = FastAPI(dependencies=[Depends(verify_key)])

# load the cleaned dataset once at startup — all requests query this in-memory DataFrame
df = pd.read_csv("data/trees_manhattan.csv", dtype=str).fillna("")


def haversine(lat1, lon1, lat2, lon2):
    # convert degrees to radians — required for Python's math trig functions
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6_371_000 * 2 * math.asin(math.sqrt(a))  # result in metres


@app.get("/trees")
def get_trees(
    health: str = Query(None, description="Filter by health: Good, Fair, Poor"),
    status: str = Query(None, description="Filter by status: Alive, Dead, Stump"),
    limit: int = Query(100, ge=1, le=1000, description="Number of rows to return"),
    offset: int = Query(0, ge=0, description="Number of rows to skip"),
):
    result = df

    if health:
        result = result[result["health"].str.lower() == health.lower()]
    if status:
        result = result[result["status"].str.lower() == status.lower()]

    result = result.iloc[offset : offset + limit]
    return result.to_dict(orient="records")


# /trees/near must be defined before /trees/{tree_id} — FastAPI matches routes top to bottom,
# and would otherwise treat the word "near" as a tree ID
@app.get("/trees/near")
def get_trees_near(
    lat: float = Query(..., description="Latitude of centre point"),
    lon: float = Query(..., description="Longitude of centre point"),
    radius_m: float = Query(200, ge=1, le=2000, description="Search radius in metres"),
):
    coords = df.copy()
    coords["latitude"] = coords["latitude"].astype(float)
    coords["longitude"] = coords["longitude"].astype(float)

    # compute distance from the given point to every tree in the dataset
    coords["distance_m"] = coords.apply(
        lambda row: haversine(lat, lon, row["latitude"], row["longitude"]), axis=1
    )

    nearby = coords[coords["distance_m"] <= radius_m].sort_values("distance_m")
    return nearby.to_dict(orient="records")


@app.get("/stressors/summary")
def get_stressor_summary():
    # keep only rows that have a problem listed
    has_problem = df[df["problems"] != ""]

    # split the comma-separated string into a list, then explode into one row per problem
    counts = (
        has_problem["problems"]
        .str.split(",")
        .explode()
        .str.strip()
        .value_counts()
        .to_dict()
    )
    return counts


@app.get("/trees/{tree_id}")
def get_tree(tree_id: str):
    match = df[df["tree_id"] == tree_id]
    if match.empty:
        raise HTTPException(status_code=404, detail="Tree not found")
    return match.iloc[0].to_dict()
