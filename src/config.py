"""Shared bakery contact/payment config, read from data/config.toml."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).parent.parent.absolute()

with open(ROOT / "data" / "config.toml", "rb") as _f:
    _config = tomllib.load(_f)

INSTAGRAM_URL    = _config["instagram_url"]
INSTAGRAM_HANDLE = _config["instagram_handle"]
WHATSAPP_URL     = _config["whatsapp_url"]
WHATSAPP_NUMBER  = _config["whatsapp_number"]
UPI_ID           = _config["upi_id"]
