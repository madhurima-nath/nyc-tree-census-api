import os

# set the test API key before importing main — load_dotenv() won't override this
os.environ["API_KEY"] = "test-key"

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
HEADERS = {"x-api-key": "test-key"}


# --- auth ---

def test_missing_key_is_rejected():
    response = client.get("/trees")
    assert response.status_code == 401


def test_wrong_key_is_rejected():
    response = client.get("/trees", headers={"x-api-key": "wrong-key"})
    assert response.status_code == 401


# --- GET /trees ---

def test_get_trees_returns_list():
    response = client.get("/trees", headers=HEADERS)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_trees_default_limit_is_100():
    response = client.get("/trees", headers=HEADERS)
    assert len(response.json()) == 100


def test_get_trees_limit():
    response = client.get("/trees?limit=5", headers=HEADERS)
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_get_trees_health_filter():
    response = client.get("/trees?health=Good&limit=50", headers=HEADERS)
    assert response.status_code == 200
    assert all(tree["health"] == "Good" for tree in response.json())


def test_get_trees_status_filter():
    response = client.get("/trees?status=Alive&limit=50", headers=HEADERS)
    assert response.status_code == 200
    assert all(tree["status"] == "Alive" for tree in response.json())


def test_get_trees_limit_above_max_is_rejected():
    response = client.get("/trees?limit=9999", headers=HEADERS)
    assert response.status_code == 422


# --- GET /trees/{tree_id} ---

def test_get_tree_valid_id():
    # get a real tree_id from the dataset first
    tree_id = client.get("/trees?limit=1", headers=HEADERS).json()[0]["tree_id"]
    response = client.get(f"/trees/{tree_id}", headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["tree_id"] == tree_id


def test_get_tree_invalid_id():
    response = client.get("/trees/999999999", headers=HEADERS)
    assert response.status_code == 404


# --- GET /trees/near ---

def test_get_trees_near_returns_list():
    response = client.get("/trees/near?lat=40.748&lon=-73.985&radius_m=200", headers=HEADERS)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_trees_near_all_within_radius():
    response = client.get("/trees/near?lat=40.748&lon=-73.985&radius_m=200", headers=HEADERS)
    assert all(tree["distance_m"] <= 200 for tree in response.json())


def test_get_trees_near_sorted_by_distance():
    response = client.get("/trees/near?lat=40.748&lon=-73.985&radius_m=200", headers=HEADERS)
    distances = [tree["distance_m"] for tree in response.json()]
    assert distances == sorted(distances)


def test_get_trees_near_missing_lat_is_rejected():
    response = client.get("/trees/near?lon=-73.985&radius_m=200", headers=HEADERS)
    assert response.status_code == 422


# --- GET /stressors/summary ---

def test_stressors_summary_returns_dict():
    response = client.get("/stressors/summary", headers=HEADERS)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_stressors_summary_values_are_integers():
    response = client.get("/stressors/summary", headers=HEADERS)
    assert all(isinstance(v, int) for v in response.json().values())


def test_stressors_summary_stones_is_most_common():
    response = client.get("/stressors/summary", headers=HEADERS)
    data = response.json()
    most_common = max(data, key=data.get)
    assert most_common == "Stones"
