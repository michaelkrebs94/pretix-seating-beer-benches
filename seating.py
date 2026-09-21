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
    primary_numbering: str = "left-to-right"
    secondary_numbering: str = "top-to-bottom"

    def validate(self) -> None:
        if self.seats_per_table < 2 or self.seats_per_table % 2:
            raise ValueError("Seats per table must be an even number of at least 2.")
        if self.num_tables_x < 1 or self.num_tables_y < 1:
            raise ValueError("The layout needs at least one table in each direction.")
        if not self.gap_tables_x or not self.gap_tables_y:
            raise ValueError("Table gap patterns cannot be empty.")
        directions = {
            "left-to-right": "x",
            "right-to-left": "x",
            "top-to-bottom": "y",
            "bottom-to-top": "y",
        }
        if self.primary_numbering not in directions or self.secondary_numbering not in directions:
            raise ValueError("Table numbering directions are invalid.")
        if directions[self.primary_numbering] == directions[self.secondary_numbering]:
            raise ValueError("Primary and secondary table numbering directions must be perpendicular.")
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


def get_table_coordinates(config: SeatingConfig, table: int) -> tuple[int, int]:
    table_index = table - 1
    primary_is_horizontal = config.primary_numbering in {"left-to-right", "right-to-left"}
    primary_length = config.num_tables_x if primary_is_horizontal else config.num_tables_y
    primary_index = table_index % primary_length
    secondary_index = table_index // primary_length

    if primary_is_horizontal:
        table_index_x = primary_index if config.primary_numbering == "left-to-right" else config.num_tables_x - 1 - primary_index
        table_index_y = secondary_index if config.secondary_numbering == "top-to-bottom" else config.num_tables_y - 1 - secondary_index
    else:
        table_index_y = primary_index if config.primary_numbering == "top-to-bottom" else config.num_tables_y - 1 - primary_index
        table_index_x = secondary_index if config.secondary_numbering == "left-to-right" else config.num_tables_x - 1 - secondary_index
    return table_index_x, table_index_y


def get_table_position(config: SeatingConfig, table_index_x: int, table_index_y: int) -> dict:

    x = config.gap_seats_x * 2 * table_index_x + config.margin + config.seat_radius
    x += sum(config.gap_tables_x[i % len(config.gap_tables_x)] for i in range(table_index_x))

    y = config.gap_seats_y * table_index_y * config.seats_per_table / 2 + config.margin
    y += sum(config.gap_tables_y[i % len(config.gap_tables_y)] for i in range(table_index_y))
    y += config.seat_radius
    return {"x": x, "y": y}


def create_table(config: SeatingConfig, table: int) -> tuple[dict, dict]:
    table_index_x, table_index_y = get_table_coordinates(config, table)
    position = get_table_position(config, table_index_x, table_index_y)
    seats = {
        "row_number": str(table),
        # The table number is rendered on its bench area. Pretix otherwise
        # duplicates it as a row label at both row ends, visibly offset.
        "row_number_position": None,
        "uuid": str(uuid4()),
        "position": position,
        "seats": [create_seat(config, table, number) for number in range(1, config.seats_per_table + 1)],
    }
    table_position = {"x": position["x"], "y": position["y"] - config.seat_radius}
    table_width = config.gap_seats_x
    table_height = config.gap_seats_y * (config.seats_per_table / 2 - 1) + config.seat_radius * 2
    rectangle = {
        "shape": "rectangle",
        "color": "#d7c29b",
        "border_color": "#6f4e37",
        "rotation": 0,
        "uuid": str(uuid4()),
        "position": table_position,
        "text": {
            # Pretix interprets text positions relative to this rectangle.
            "position": {"x": table_width / 2, "y": table_height / 2},
            "color": "#333333",
            "text": str(table),
        },
        "rectangle": {"width": table_width, "height": table_height},
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
