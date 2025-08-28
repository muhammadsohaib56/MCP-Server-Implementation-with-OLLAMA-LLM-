"""
MCP Unit Converter (Calculator / Unit Converter)
-----------------------------------------------
A beginner-friendly MCP server that exposes a single tool:

    convert(value: float, from_unit: str, to_unit: str, precision: int = 6)

It also exposes a resource:
    units://supported_units.json  -> returns the bundled supported_units.json file

Run (for local testing with MCP Inspector):
    npx -y @modelcontextprotocol/inspector stdio python server.py

Notes:
- We use the official MCP Python SDK (FastMCP APIs).
- For STDIO transport, DO NOT print to stdout; use logging (stderr) instead.
"""

from __future__ import annotations

from typing import TypedDict, Any
from pathlib import Path
import json
import logging
import re

from mcp.server import FastMCP

# ---------- Setup ----------

mcp = FastMCP("unit-converter")
HERE = Path(__file__).parent
UNITS_FILE = HERE / "supported_units.json"

logging.basicConfig(level=logging.INFO)  # logs go to stderr by default


# ---------- Data loading & indexing ----------

def load_units() -> dict[str, Any]:
    if not UNITS_FILE.exists():
        raise FileNotFoundError(f"supported_units.json not found at {UNITS_FILE}")
    with UNITS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _normalize(u: str) -> str:
    """Normalize a unit string for matching: lowercase, strip spaces, strip degree symbol, collapse plural 's'."""
    s = u.strip().lower()
    s = s.replace("°", "")
    s = s.replace("degrees", "").replace("degree", "")
    s = re.sub(r"\s+", "", s)
    # Remove trailing 's' for simple plurals (meters -> meter); keep units like 'lbs' commonly plural
    if s.endswith("s") and s not in {"lbs"}:
        s = s[:-1]
    return s


def build_index(units_doc: dict[str, Any]) -> tuple[dict[str, str], dict[str, str], dict[str, Any]]:
    """
    Returns:
      alias_to_primary: maps any alias (normalized) -> canonical unit key (e.g., 'meter' -> 'm')
      unit_to_category: maps canonical unit key -> category name
      categories: the original categories section
    """
    alias_to_primary: dict[str, str] = {}
    unit_to_category: dict[str, str] = {}

    categories = units_doc["categories"]
    for cat_name, cat in categories.items():
        if cat["kind"] == "ratio":
            for primary, meta in cat["units"].items():
                unit_to_category[primary] = cat_name
                alias_to_primary[_normalize(primary)] = primary
                for alias in meta.get("aliases", []):
                    alias_to_primary[_normalize(alias)] = primary
        else:
            # affine (e.g., temperature)
            for primary, meta in cat["units"].items():
                unit_to_category[primary] = cat_name
                alias_to_primary[_normalize(primary)] = primary
                for alias in meta.get("aliases", []):
                    alias_to_primary[_normalize(alias)] = primary

    return alias_to_primary, unit_to_category, categories


UNITS_DOC = load_units()
ALIAS_TO_PRIMARY, UNIT_TO_CATEGORY, CATEGORIES = build_index(UNITS_DOC)


def normalize_to_primary(user_unit: str) -> str | None:
    return ALIAS_TO_PRIMARY.get(_normalize(user_unit))


def get_category(primary_unit: str) -> str | None:
    return UNIT_TO_CATEGORY.get(primary_unit)


# ---------- Conversion helpers ----------

def convert_ratio(value: float, from_unit: str, to_unit: str, category: dict[str, Any]) -> float:
    # Ratios: we have a base unit and factors relative to base (unit -> factor_to_base)
    base = category["base"]
    units = category["units"]

    if from_unit not in units or to_unit not in units:
        raise ValueError("Unsupported unit for this category.")

    f_from = units[from_unit]["factor"]
    f_to = units[to_unit]["factor"]

    # Convert to base, then to target
    value_in_base = value * f_from
    result = value_in_base / f_to
    return result


def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    # Handle common temperature conversions explicitly
    f = from_unit.upper()
    t = to_unit.upper()
    if f == t:
        return float(value)

    if f == "C" and t == "K":
        return value + 273.15
    if f == "K" and t == "C":
        return value - 273.15
    if f == "C" and t == "F":
        return value * 9.0/5.0 + 32.0
    if f == "F" and t == "C":
        return (value - 32.0) * 5.0/9.0
    if f == "F" and t == "K":
        return (value + 459.67) * 5.0/9.0
    if f == "K" and t == "F":
        return value * 9.0/5.0 - 459.67

    raise ValueError(f"Unsupported temperature conversion: {from_unit} -> {to_unit}")


class ConversionResult(TypedDict):
    category: str
    input_value: float
    from_unit: str
    to_unit: str
    result: float
    precision: int


# ---------- Tools & Resources ----------

@mcp.tool()
def convert(value: float, from_unit: str, to_unit: str, precision: int = 6) -> ConversionResult:
    """Convert a numeric value between supported units.

    Args:
        value: The numeric value to convert.
        from_unit: Unit to convert FROM (aliases allowed, e.g., "meters", "centigrade").
        to_unit: Unit to convert TO (aliases allowed).
        precision: Number of decimals to round the result to (default 6, 0-12 allowed).

    Returns:
        A structured result with the converted value and metadata.

    Raises:
        ValueError if the units are unknown or incompatible.
    """
    if not isinstance(value, (int, float)):
        raise ValueError("value must be a number")

    precision = max(0, min(int(precision), 12))

    src = normalize_to_primary(from_unit)
    dst = normalize_to_primary(to_unit)
    if not src:
        raise ValueError(f"Unknown from_unit: '{from_unit}'")
    if not dst:
        raise ValueError(f"Unknown to_unit: '{to_unit}'")

    cat_from = get_category(src)
    cat_to = get_category(dst)
    if cat_from != cat_to or cat_from is None:
        raise ValueError(f"Incompatible units '{from_unit}' and '{to_unit}' (categories: {cat_from} vs {cat_to})")

    category_doc = CATEGORIES[cat_from]
    if category_doc["kind"] == "ratio":
        raw = convert_ratio(float(value), src, dst, category_doc)
    elif category_doc["kind"] == "affine" and cat_from == "temperature":
        raw = convert_temperature(float(value), src, dst)
    else:
        raise ValueError(f"Unsupported category kind: {category_doc['kind']}")

    rounded = round(raw, precision)
    logging.info("Converted %s %s -> %s %s (category=%s)", value, src, rounded, dst, cat_from)

    return ConversionResult(
        category=cat_from,
        input_value=float(value),
        from_unit=src,
        to_unit=dst,
        result=float(rounded),
        precision=precision,
    )


@mcp.resource("units://supported_units.json")
def supported_units() -> str:
    """Return the JSON document that describes supported unit categories and units."""
    with UNITS_FILE.open("r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    # Start the MCP server over STDIO
    mcp.run(transport="stdio")