from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel, Field, field_validator

from seating import SeatingConfig, create_seating

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="Beer Benches Seating", version="1.0.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")


class SeatingRequest(BaseModel):
    seats_per_table: int = Field(default=8, ge=2)
    num_tables_x: int = Field(default=8, ge=1)
    num_tables_y: int = Field(default=15, ge=1)
    gap_tables_x: list[int] = Field(default_factory=lambda: [20, 45])
    gap_tables_y: list[int] = Field(default_factory=lambda: [5, 5, 5, 45])
    gap_seats_x: int = Field(default=60, ge=0)
    gap_seats_y: int = Field(default=25, ge=0)
    seat_radius: int = Field(default=10, ge=0)
    table_name: str = Field(default="Tisch", min_length=1, max_length=80)
    seat_name: str = Field(default="Platz", min_length=1, max_length=80)
    margin: int = Field(default=40, ge=0)

    @field_validator("seats_per_table")
    @classmethod
    def seats_must_be_even(cls, value: int) -> int:
        if value % 2:
            raise ValueError("must be an even number")
        return value

    @field_validator("gap_tables_x", "gap_tables_y")
    @classmethod
    def gaps_must_not_be_empty_or_negative(cls, value: list[int]) -> list[int]:
        if not value or any(gap < 0 for gap in value):
            raise ValueError("must contain non-negative values")
        return value

    def as_config(self) -> SeatingConfig:
        return SeatingConfig(**self.model_dump())


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")


@app.post("/api/seating")
def generate_seating(payload: SeatingRequest) -> dict:
    try:
        return create_seating(payload.as_config())
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
