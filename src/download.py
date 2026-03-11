#!/usr/bin/env python3
"""
Fetch the public Google Sheet as CSV and write data/menu.csv.

Env:
  SPREADSHEET_ID = <your sheet id>
"""

import os

import requests

from constants import MENU_CSV


def main():
    ssid = os.environ.get("SPREADSHEET_ID")
    if not ssid:
        raise RuntimeError("SPREADSHEET_ID env var is not set")

    url = f"https://docs.google.com/spreadsheets/d/{ssid}/export?format=csv&sheet=menu"
    response = requests.get(url)
    response.raise_for_status()
    MENU_CSV.parent.mkdir(parents=True, exist_ok=True)
    MENU_CSV.write_bytes(response.content)
    print(f"Fetched menu CSV → {MENU_CSV}")


if __name__ == "__main__":
    main()
