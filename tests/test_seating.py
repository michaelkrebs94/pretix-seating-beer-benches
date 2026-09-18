from fastapi.testclient import TestClient

from app.main import app
from seating import SeatingConfig, create_seating


client = TestClient(app)


def test_default_layout_has_expected_table_and_seat_count():
    plan = create_seating(SeatingConfig(num_tables_x=2, num_tables_y=3, seats_per_table=8))
    zone = plan["zones"][0]

    assert len(zone["rows"]) == 6
    assert len(zone["areas"]) == 6
    assert sum(len(row["seats"]) for row in zone["rows"]) == 48
    assert len({area["uuid"] for area in zone["areas"]}) == 6


def test_generator_rejects_odd_seats_per_table():
    try:
        create_seating(SeatingConfig(seats_per_table=7))
    except ValueError as error:
        assert "even" in str(error)
    else:
        raise AssertionError("Expected invalid seat count to be rejected")


def test_api_generates_pretix_plan():
    response = client.post("/api/seating", json={"seats_per_table": 4, "num_tables_x": 2, "num_tables_y": 2})

    assert response.status_code == 200
    plan = response.json()
    assert plan["name"] == "Beer benches"
    assert len(plan["zones"][0]["rows"]) == 4
    assert response.headers["content-type"].startswith("application/json")


def test_api_rejects_odd_seat_count():
    response = client.post("/api/seating", json={"seats_per_table": 5})

    assert response.status_code == 422
