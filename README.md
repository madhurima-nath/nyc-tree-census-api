# NYC Street Tree Census API

A REST API over the [NYC 2015 Street Tree Census](https://data.cityofnewyork.us/Environment/2015-Street-Tree-Census-Tree-Data/uvpi-gqnh) dataset, built with FastAPI and pandas. The Manhattan subset covers 65,423 trees.

The project also includes a data ingestion pipeline, a pytest test suite, and an MCP server that exposes the API as tools for AI agents.

---

## Writeup

This project is documented in two Medium posts:

- [Part 1: How I Built a REST API from Scratch](https://medium.com/@m.nath/how-i-built-a-rest-api-from-scratch-8cd79688c2e7)
- [Part 2: How I Secured and Tested My REST API](https://medium.com/@m.nath/how-i-secured-and-tested-my-rest-api-d117810df347)

---

## Endpoints

All endpoints require an API key in the `x-api-key` request header.

| Method | Path                 | Description                                                            |
| ------ | -------------------- | ---------------------------------------------------------------------- |
| `GET`  | `/trees`             | List trees with optional filters for health, status, limit, and offset |
| `GET`  | `/trees/{tree_id}`   | Retrieve a single tree by its census ID                                |
| `GET`  | `/trees/near`        | Find trees within a given radius of a lat/lon point                    |
| `GET`  | `/stressors/summary` | Count of each recorded stressor across all trees                       |

> **Note:** `/trees/near` is declared before `/trees/{tree_id}` in `main.py`. FastAPI matches routes top to bottom, so if `/trees/{tree_id}` came first, a request to `/trees/near` would be interpreted as a lookup for a tree with ID `"near"`. Keep this ordering if you add new routes under `/trees`.

Interactive documentation is available at `/docs` once the server is running.

Each tree record contains: `tree_id`, `spc_common` (species), `tree_dbh` (trunk diameter in inches), `status`, `health`, `latitude`, `longitude`, and `problems` (comma-separated stressor flags, or empty if none).

**Example requests**

```
# list trees in good health, first 5 results
curl -H "x-api-key: your_key" "http://127.0.0.1:8000/trees?health=Good&limit=5"

# trees within 300 metres of the Empire State Building
curl -H "x-api-key: your_key" "http://127.0.0.1:8000/trees/near?lat=40.7484&lon=-73.9857&radius_m=300"

# retrieve a specific tree by ID
curl -H "x-api-key: your_key" "http://127.0.0.1:8000/trees/190422"

# stressor counts across all trees
curl -H "x-api-key: your_key" "http://127.0.0.1:8000/stressors/summary"
```

---

## Setup

Requires Python 3.11.

```
git clone https://github.com/madhurima-nath/nyc-tree-census-api.git
cd nyc-tree-census-api
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file at the project root:

```
NYC_APP_TOKEN=your_socrata_app_token
API_KEY=your_api_key
```

- `NYC_APP_TOKEN` is a free Socrata app token from [data.cityofnewyork.us](https://data.cityofnewyork.us). It is only needed to run the ingestion pipeline.
- `API_KEY` can be any string. Generate one with:

```
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

The `.env` file is excluded from version control. A pre-cleaned CSV is included in `data/`, so the ingestion pipeline does not need to run before starting the API.

---

## Running the API

```
.venv/bin/uvicorn main:app --reload
```

The API starts at `http://127.0.0.1:8000`.

---

## Data ingestion

To pull fresh data from the NYC Open Data portal:

```
.venv/bin/python pipeline/ingest.py
```

This fetches all Manhattan trees from the Socrata Open Data API and writes them to `data/trees_manhattan.csv`.

---

## Tests

```
.venv/bin/pytest tests/test_main.py -v
```

17 tests covering all four endpoints:

| Group                        | Tests                                                                                                                 |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Authentication (2)           | missing key → `401`, incorrect key → `401`                                                                            |
| `GET /trees` (6)             | list returned, default limit 100, `limit=5` returns 5 records, `health` filter, `status` filter, `limit=9999` → `422` |
| `GET /trees/{tree_id}` (2)   | valid ID → `200`, unknown ID → `404`                                                                                  |
| `GET /trees/near` (4)        | list returned, all results within radius, ordered by distance nearest first, missing `lat` → `422`                    |
| `GET /stressors/summary` (3) | dict returned, all values integers, Stones is the most common stressor                                                |

---

## MCP server

The `mcp_server/server.py` file exposes three read-only tools for use by AI agents via the [Model Context Protocol](https://modelcontextprotocol.io):

- `find_trees_near_location` — trees within a radius of given coordinates
- `get_tree_health_summary` — stressor counts across all trees
- `get_stressor_flags` — condition of a specific tree by ID

The REST API must be running before starting the MCP server. The MCP server reads the same `API_KEY` from `.env` and attaches it to its own requests to the REST API, so it authenticates the same way any other client would.

```
.venv/bin/python mcp_server/server.py
```

The server communicates over stdio (standard input/output).

---

## Data source

NYC Parks Department via NYC Open Data. Dataset: [2015 Street Tree Census](https://data.cityofnewyork.us/Environment/2015-Street-Tree-Census-Tree-Data/uvpi-gqnh).

## Licence

MIT
