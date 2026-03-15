#!/usr/bin/env python3
"""
Generate invoice.html at the project root for local use.

Usage:
  uv run python src/generate_invoice.py [--output PATH]

Open the generated file in your browser, fill in customer details and items,
then use browser Print (Ctrl+P) to save as PDF.
"""

import argparse
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from constants import MENU_CSV, TEMPLATE_DIR
from generate_pdf import load_items, logo_data_uri

ROOT = Path(__file__).parent.parent.absolute()
LOGO_PATH = ROOT / "static" / "logo.jpg"
DEFAULT_OUTPUT = ROOT / "static" / "invoice.html"


def build_menu_data(items) -> list[dict]:
    result = []
    for item in items:
        sizes = []
        for i in (1, 2, 3):
            price = getattr(item, f"price_{i}")
            size = getattr(item, f"size_{i}")
            if price is not None and size:
                sizes.append({"size": size, "price": price})
        result.append({"name": item.name, "category": item.category, "sizes": sizes})
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output HTML path")
    args = ap.parse_args()

    items = load_items(MENU_CSV)
    menu_data = build_menu_data(items)
    logo_uri = logo_data_uri(LOGO_PATH)

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)
    tmpl = env.get_template("invoice.html")
    html = tmpl.render(menu_json=json.dumps(menu_data, ensure_ascii=False), logo_uri=logo_uri)

    out = Path(args.output)
    out.write_text(html, encoding="utf-8")
    print(f"Invoice written → {out}")
    print("Open in your browser, fill in the form, then Ctrl+P to save as PDF.")


if __name__ == "__main__":
    main()
