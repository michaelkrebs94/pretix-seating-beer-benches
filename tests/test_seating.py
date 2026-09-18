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


def test_table_numbering_can_run_right_to_left_then_top_to_bottom():
    plan = create_seating(SeatingConfig(
        num_tables_x=2,
        num_tables_y=2,
        primary_numbering="right-to-left",
        secondary_numbering="top-to-bottom",
    ))
    positions = [row["position"] for row in plan["zones"][0]["rows"]]

    assert positions[0]["x"] > positions[1]["x"]
    assert positions[0]["y"] == positions[1]["y"]
    assert positions[2]["y"] > positions[0]["y"]


def test_table_numbering_can_run_top_to_bottom_then_right_to_left():
    plan = create_seating(SeatingConfig(
        num_tables_x=2,
        num_tables_y=2,
        primary_numbering="top-to-bottom",
        secondary_numbering="right-to-left",
    ))
    positions = [row["position"] for row in plan["zones"][0]["rows"]]

    assert positions[0]["y"] < positions[1]["y"]
    assert positions[2]["x"] < positions[0]["x"]


def test_api_rejects_parallel_table_numbering_directions():
    response = client.post("/api/seating", json={
        "primary_numbering": "left-to-right",
        "secondary_numbering": "right-to-left",
    })

    assert response.status_code == 422
