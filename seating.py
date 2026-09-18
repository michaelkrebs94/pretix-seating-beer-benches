"""Generate pretix-compatible seating plans for beer-bench layouts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from uuid import uuid4


@dataclass
class SeatingConfig:
    seats_per_table: int = 8
    num_tables_x: int = 8
    num_tables_y: int = 15
    gap_tables_x: list[int] = field(default_factory=lambda: [20, 45])
    gap_tables_y: list[int] = field(default_factory=lambda: [5, 5, 5, 45])
    gap_seats_x: int = 60
    gap_seats_y: int = 25
    seat_radius: int = 10
    table_name: str = "Tisch"
    seat_name: str = "Platz"
    margin: int = 40

    def validate(self) -> None:
        if self.seats_per_table < 2 or self.seats_per_table % 2:
            raise ValueError("Seats per table must be an even number of at least 2.")
        if self.num_tables_x < 1 or self.num_tables_y < 1:
            raise ValueError("The layout needs at least one table in each direction.")
        if not self.gap_tables_x or not self.gap_tables_y:
            raise ValueError("Table gap patterns cannot be empty.")
        if any(value < 0 for value in asdict(self).values() if isinstance(value, int)):
            raise ValueError("Numeric values cannot be negative.")


def create_seat(config: SeatingConfig, table: int, number: int) -> dict:
    is_even = number % 2 == 0
    return {
        "seat_number": str(number),
        "seat_guid": f"{config.table_name}{table}_{config.seat_name}{number}",
        "uuid": str(uuid4()),
        "position": {
            "x": config.gap_seats_x if is_even else 0,
            "y": (number - 1) // 2 * config.gap_seats_y,
        },
        "category": "",
        "radius": config.seat_radius,
    }


def get_table_position(config: SeatingConfig, table: int) -> dict:
    table_index = table - 1
    table_index_x = table_index % config.num_tables_x
    table_index_y = table_index // config.num_tables_x

    x = config.gap_seats_x * 2 * table_index_x + config.margin + config.seat_radius
    x += sum(config.gap_tables_x[i % len(config.gap_tables_x)] for i in range(table_index_x))

    y = config.gap_seats_y * table_index_y * config.seats_per_table / 2 + config.margin
    y += sum(config.gap_tables_y[i % len(config.gap_tables_y)] for i in range(table_index_y))
    y += config.seat_radius
    return {"x": x, "y": y}


def create_table(config: SeatingConfig, table: int) -> tuple[dict, dict]:
    position = get_table_position(config, table)
    seats = {
        "row_number": str(table),
        "row_number_position": "both",
        "uuid": str(uuid4()),
        "position": position,
        "seats": [create_seat(config, table, number) for number in range(1, config.seats_per_table + 1)],
    }
    rectangle = {
        "shape": "rectangle",
        "color": "#d7c29b",
        "border_color": "#6f4e37",
        "rotation": 0,
        "uuid": str(uuid4()),
        "position": {"x": position["x"], "y": position["y"] - config.seat_radius},
        "text": {"position": position, "color": "#333333", "text": str(table)},
        "rectangle": {
            "width": config.gap_seats_x,
            "height": config.gap_seats_y * (config.seats_per_table / 2 - 1) + config.seat_radius * 2,
        },
    }
    return seats, rectangle


def create_seating(config: SeatingConfig | None = None) -> dict:
    config = config or SeatingConfig()
    config.validate()
    rows, areas = [], []
    for table in range(1, config.num_tables_x * config.num_tables_y + 1):
        row, area = create_table(config, table)
        rows.append(row)
        areas.append(area)

    return {
        "name": "Beer benches",
        "categories": [],
        "zones": [{
            "name": "Main",
            "position": {"x": 0, "y": 0},
            "areas": areas,
            "uuid": str(uuid4()),
            "zone_id": "Main",
            "rows": rows,
        }],
        "size": {
            "width": max(row["position"]["x"] + seat["position"]["x"] for row in rows for seat in row["seats"])
            + config.seat_radius + config.margin * 2,
            "height": max(row["position"]["y"] + seat["position"]["y"] for row in rows for seat in row["seats"])
            + config.seat_radius + config.margin * 2,
        },
    }


if __name__ == "__main__":
    Path("seating.json").write_text(json.dumps(create_seating(), indent=2), encoding="utf-8")
