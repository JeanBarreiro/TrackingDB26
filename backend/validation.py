"""Validation and JSON conversion shared by Trip and Location Ping handlers."""
from datetime import datetime, timezone
import math
import re
import sys

from fastapi import HTTPException

MAX_BIGINT = 2**63 - 1
RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?"
    r"(?:[Zz]|[+-]\d{2}:\d{2})$"
)


def record_id(value, name, status=404):
    if isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
        digits = value.lstrip("0") or "0"
        if len(digits) <= 19:
            value = int(digits)
    if type(value) is not int or not 0 < value <= MAX_BIGINT:
        raise HTTPException(status, f"{name} must be a positive integer.")
    return value


def body_id(value, name, status=400):
    if type(value) is not int:
        raise HTTPException(status, f"{name} must be a positive integer.")
    return record_id(value, name, status)


def nonnegative(value, name, status=400):
    if value is None:
        return None
    if not finite_number(value) or value < 0:
        raise HTTPException(status, f"{name} must be a non-negative number.")
    return value


def finite_number(value):
    return type(value) in (int, float) and -sys.float_info.max <= value <= sys.float_info.max


def timestamp(value, name, status=400):
    if not isinstance(value, str) or not RFC3339.fullmatch(value):
        raise HTTPException(status, f"{name} must be an RFC 3339 timestamp with a timezone.")
    if value[-1] not in "Zz" and (int(value[-5:-3]) > 23 or int(value[-2:]) > 59):
        raise HTTPException(status, f"{name} has an invalid timezone offset.")
    try:
        parsed = datetime.fromisoformat(value.replace("t", "T").replace("z", "+00:00").replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    except (ValueError, OverflowError):
        raise HTTPException(status, f"{name} is not a valid timestamp.") from None


def point(value, name, status=400, nullable=False):
    if value is None and nullable:
        return None
    if not isinstance(value, dict) or value.get("type") != "Point":
        raise HTTPException(status, f"{name} must be a GeoJSON Point.")
    coordinates = value.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) != 2:
        raise HTTPException(status, f"{name} needs longitude and latitude coordinates.")
    if not all(finite_number(v) for v in coordinates):
        raise HTTPException(status, f"{name} coordinates must be finite numbers.")
    longitude, latitude = coordinates
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        raise HTTPException(status, f"{name} coordinates must be within WGS84 bounds.")
    return {"type": "Point", "coordinates": coordinates}


def pagination(query, default_limit):
    result = []
    for name, default in (("limit", default_limit), ("offset", 0)):
        value = query.get(name, str(default))
        digits = value.lstrip("0") or "0"
        if (not re.fullmatch(r"[0-9]+", value) or len(digits) > 19
                or int(digits) > MAX_BIGINT):
            raise HTTPException(400, f"{name} must be a non-negative integer.")
        result.append(int(digits))
    return tuple(result)


def time_range(query):
    start = timestamp(query["from_ts"], "from_ts") if "from_ts" in query else None
    end = timestamp(query["to_ts"], "to_ts") if "to_ts" in query else None
    if start is not None and end is not None and end < start:
        raise HTTPException(400, "from_ts must not be later than to_ts.")
    return start, end


def bounding_box(value):
    if value is None:
        return None
    try:
        values = [float(part) for part in value.split(",")]
        if len(values) != 4 or not all(math.isfinite(number) for number in values):
            raise ValueError
        west, south, east, north = values
        if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
            raise ValueError
        return values
    except ValueError:
        raise HTTPException(400, "bbox must be minLon,minLat,maxLon,maxLat within WGS84 bounds.") from None


def serialize(row):
    if row is None:
        return None
    return {
        key: (value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
              if value.tzinfo is None else value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"))
        if isinstance(value, datetime) else value
        for key, value in row.items()
    }
