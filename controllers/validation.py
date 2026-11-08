
"""Request and business-rule validation for Phase II."""

import json
import math
import re
from datetime import datetime, timezone

from fastapi import HTTPException


def bad(message):
    raise HTTPException(
        status_code=400,
        detail=message
    )


def parse_pagination(limit, offset):
    try:
        limit_value = int(limit)
        offset_value = int(offset)
    except (TypeError, ValueError):
        bad("limit and offset must be non-negative integers")

    if not (0 <= limit_value <= 2**63 - 1 and 0 <= offset_value <= 2**63 - 1):
        bad("limit and offset must be non-negative integers")

    return limit_value, offset_value


def parse_bbox(value):
    if value is None:
        return None

    try:
        values = [
            float(v.strip()) for v in value.split(",")
        ]
    except (TypeError, ValueError):
        bad("bbox must be minLon,minLat,maxLon,maxLat")

    if len(values) != 4 or not all(
        math.isfinite(x) for x in values
    ):
        bad("bbox must contain four finite numbers")

    min_lon, min_lat, max_lon, max_lat = values

    if not (
        -180 <= min_lon < max_lon <= 180
        and -90 <= min_lat < max_lat <= 90
    ):
        bad("Invalid WGS84 bbox or reversed bounds")

    return values


def validate_number(value, label, status=400):
    try:
        valid = type(value) in (int, float) and math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    if not valid:
        raise HTTPException(status, f"{label} must be a non-negative number")


def validate_coordinates(pos):
    if not isinstance(pos, (tuple, list)) or len(pos) < 2:
        bad("Each coordinate must contain longitude and latitude")

    lon, lat = pos[:2]

    if (
        type(lon) not in (float, int)
        or type(lat) not in (float, int)
        or not -180 <= lon <= 180
        or not -90 <= lat <= 90
    ):
        bad("Coordinates must be within EPSG:4326 ranges")


def validate_geom(geom, expected):
    if not isinstance(geom, dict) or geom.get("type") != expected:
        bad(f"geom must be a GeoJSON {expected}")

    coords = geom.get("coordinates")

    if not isinstance(coords, list) or not coords:
        bad("geom must have coordinates")

    if expected == "Point":
        if len(coords) != 2:
            bad("Point requires longitude and latitude")
        validate_coordinates(coords)
        geom = {"type": "Point", "coordinates": coords}

    elif expected == "LineString":
        if len(coords) < 2:
            bad("LineString requires at least two positions")

        for pos in coords:
            validate_coordinates(pos)

    elif expected == "Polygon":
        for ring in coords:
            if not isinstance(ring, list) or len(ring) < 4:
                bad("Polygon rings require at least four points")

            if ring[0] != ring[-1]:
                bad("Polygon ring must be closed")

            for pos in ring:
                validate_coordinates(pos)

    return json.dumps(geom)


def validate_payload(payload, kind, update=False):
    if not isinstance(payload, dict):
        bad("Body must be a JSON object")

    if kind == "parking":
        fields = {"name", "geom", "capacity"}
    else:
        fields = {
            "name",
            "geom",
            "speed_limit_kph",
            "is_oneway",
            "direction"
        }

    if not set(payload).issubset(fields):
        bad("Unknown fields in request")

    if update and not payload:
        bad("At least one updatable field is required")

    if not update and (
        "name" not in payload or "geom" not in payload
    ):
        bad("name and geom are required")

    if "name" in payload:
        if (
            not isinstance(payload["name"], str)
            or not payload["name"].strip()
        ):
            bad("name must be non-empty")

    if "geom" in payload:
        expected = "Polygon" if kind == "parking" else "LineString"
        validate_geom(payload["geom"], expected)

    if "capacity" in payload:
        validate_number(payload["capacity"], "capacity")

        if type(payload["capacity"]) is not int:
            bad("capacity must be an integer")

    if "speed_limit_kph" in payload:
        validate_number(
            payload["speed_limit_kph"],
            "speed_limit_kph"
        )

    if "is_oneway" in payload:
        if type(payload["is_oneway"]) is not bool:
            bad("is_oneway must be boolean")

    if "direction" in payload:
        if payload["direction"] not in ("both", "forward"):
            bad("direction must be 'both' or 'forward'")

    return payload


def parse_id(value, label, status=400):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise HTTPException(status, f"{label} must be a positive integer")

    if number <= 0:
        raise HTTPException(status, f"{label} must be a positive integer")

    return number


def parse_speed(value, label):
    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        bad(f"{label} must be numeric")

    if not math.isfinite(number) or number < 0:
        bad(f"{label} must be non-negative")

    return number


def check_speed_bounds(low, high):
    if (
        low is not None
        and high is not None
        and low > high
    ):
        bad("min_speed_kph cannot exceed max_speed_kph")


def parse_timestamp(value, label, status=400):
    pattern = r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})"
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise HTTPException(status, f"{label} must be an RFC 3339 timestamp with a timezone")
    if value[-1] not in "Zz" and (int(value[-5:-3]) > 23 or int(value[-2:]) > 59):
        raise HTTPException(status, f"{label} has an invalid timezone offset")
    try:
        parsed = datetime.fromisoformat(value.upper().replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    except (ValueError, OverflowError):
        raise HTTPException(status, f"{label} is not a valid timestamp") from None


def parse_time_range(from_ts, to_ts):
    start = parse_timestamp(from_ts, "from_ts") if from_ts is not None else None
    end = parse_timestamp(to_ts, "to_ts") if to_ts is not None else None
    if start is not None and end is not None and start > end:
        bad("from_ts must not be later than to_ts")
    return start, end
