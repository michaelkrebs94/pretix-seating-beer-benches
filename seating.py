import json
from uuid import uuid4


class Config:
    seats_per_table: int = 8 # Number of seats per table
    num_tables_x: int = 8 # Number of tables next to each other
    num_tables_y: int = 15 # Number of tables in a row
    gap_tables_x: int = [20, 45] # Gaps between tables in x direction, alternating through the list
    gap_tables_y: int = [5,5,5,45] # Gaps between tables in y direction, alternating through the list
    gap_seats_x: int = 60 # Gap between seats in x direction (even and odd seats) in a bench
    gap_seats_y: int = 25 # Gap between seats in y direction in a bench
    seat_radius: int = 10 # Radius of the seat (pretix property)
    table_name = "Tisch" # Name of the table for building the guid
    seat_name = "Platz" # Name of the seat for building the guid
    margin: int = 40 # Margin around the seating plan
config = Config()

def create_seat(table: int, num: int) -> dict:
    is_even = num % 2 == 0
    x_seat = config.gap_seats_x if is_even else 0
    y_seat = (num - 1) // 2 * config.gap_seats_y
    guid = f"{config.table_name}{table}_{config.seat_name}{num}"
    uuid = str(uuid4())
    return {
        "seat_number": str(num),
        "seat_guid": guid,
        "uuid": uuid,
        "position": {
            "x": x_seat,
            "y": y_seat
        },
        "category": "",
        "radius": config.seat_radius
    }

def get_table_position(table: int) -> dict:
    table_index = table - 1
    table_index_x = table_index % config.num_tables_x
    table_index_y = table_index // config.num_tables_x

    x = config.gap_seats_x * 2 * table_index_x + config.margin
    for i in range(table_index_x):
        x += config.gap_tables_x[i % len(config.gap_tables_x)]
    x += config.seat_radius

    y = config.gap_seats_y * table_index_y * config.seats_per_table / 2 + config.margin
    for i in range(table_index_y):
        y += config.gap_tables_y[i % len(config.gap_tables_y)]
    y += config.seat_radius

    return {
        "x": x,
        "y": y
    }

def create_table(table: int) -> tuple[dict, dict]:
    position = get_table_position(table)
    uuid = str(uuid4())
    seats = {
        "row_number": str(table),
        "row_number_position": "both",
        "uuid": uuid,
        "position": position,
        "seats": [create_seat(table, i) for i in range(1, config.seats_per_table + 1)]
    }
    rectangle = {
        "shape": "rectangle",
        "color": "#cccccc",
        "border_color": "#000000",
        "rotation": 0,
        "uuid": "5fab97bc-e024-418c-8406-bcfeb8c8a17a",
        "position": {
        "x": position["x"],
        "y": position["y"] - config.seat_radius
        },
        "text": {
        "position": {
            "x": position["x"],
            "y": position["y"]
        },
        "color": "#333333",
        "text": ""
        },
        "rectangle": {
        "width": config.gap_seats_x,
        "height": config.gap_seats_y * (config.seats_per_table / 2 - 1) + config.seat_radius * 2
        }
    }
    return seats, rectangle

def create_seating() -> dict:
    rows = []
    areas = []
    for i in range(1, config.num_tables_x * config.num_tables_y + 1):
        seats, rectangle = create_table(i)
        rows.append(seats)
        areas.append(rectangle)
    
    return {
        "name": "Seating",
        "categories": [],
        "zones": [
            {
                "name": "Main",
                "position": {
                    "x": 0,
                    "y": 0
                },
                "areas": areas,
                "uuid": str(uuid4()),
                "zone_id": "Main",
                "rows": rows
            }
        ],
        "size": {
            "width": max([table["position"]["x"] + seat["position"]["x"] for table in rows for seat in table["seats"]]) + config.seat_radius + config.margin * 2,
            "height": max([table["position"]["y"] + seat["position"]["y"] for table in rows for seat in table["seats"]]) + config.seat_radius + config.margin * 2
        }
    }

json.dump(create_seating(), open("seating.json", "w"), indent=4)