import os
import json
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

# the base URL of the running REST API
API_BASE = "http://127.0.0.1:8000"

# the API key is read from .env and sent in every request header
HEADERS = {"x-api-key": os.getenv("API_KEY")}

# create the MCP server — the name identifies it to the connecting agent
mcp = FastMCP("nyc-tree-census")


@mcp.tool()
def find_trees_near_location(lat: float, lon: float, radius_m: float = 200) -> str:
    """
    Find NYC street trees within a given radius of a location.
    Returns species, health status, distance in metres, and any recorded problems.
    Use this when asked about trees near an address or coordinates.
    """
    response = requests.get(
        f"{API_BASE}/trees/near",
        params={"lat": lat, "lon": lon, "radius_m": radius_m},
        headers=HEADERS,
    )
    trees = response.json()

    if not trees:
        return f"No trees found within {radius_m}m of ({lat}, {lon})."

    # format each tree as a readable line
    lines = [
        f"- {t['spc_common']} | health: {t['health']} | {t['distance_m']:.1f}m away"
        + (f" | problems: {t['problems']}" if t["problems"] else "")
        for t in trees
    ]
    return f"Found {len(trees)} tree(s) within {radius_m}m:\n" + "\n".join(lines)


@mcp.tool()
def get_tree_health_summary() -> str:
    """
    Get a summary of stressor counts across all Manhattan street trees.
    Returns how many trees have each type of recorded problem (e.g. Stones, WiresRope).
    Use this when asked about the overall health or common problems of NYC trees.
    """
    response = requests.get(f"{API_BASE}/stressors/summary", headers=HEADERS)
    data = response.json()

    lines = [f"- {stressor}: {count:,} trees" for stressor, count in data.items()]
    return "Stressor counts across Manhattan trees:\n" + "\n".join(lines)


@mcp.tool()
def get_stressor_flags(tree_id: str) -> str:
    """
    Get the recorded stressor flags for a specific tree by its ID.
    Returns species, health, status, and any problems recorded for that tree.
    Use this when asked about the condition of a specific tree.
    """
    response = requests.get(f"{API_BASE}/trees/{tree_id}", headers=HEADERS)

    if response.status_code == 404:
        return f"No tree found with ID {tree_id}."

    t = response.json()
    return (
        f"Tree {tree_id}: {t['spc_common']} | "
        f"status: {t['status']} | "
        f"health: {t['health']} | "
        f"problems: {t['problems'] if t['problems'] else 'none'}"
    )


if __name__ == "__main__":
    # run the MCP server — listens on stdio for connections from an agent
    mcp.run()
