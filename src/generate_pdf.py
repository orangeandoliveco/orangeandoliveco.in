#!/usr/bin/env python3
"""
Generate static/menu.pdf from data/menu.csv using Playwright (HTML → PDF).

Usage:
  uv run python src/generate_pdf.py [--output PATH]
"""

import argparse
import base64
import csv
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright
from pydantic import BaseModel, Field, ValidationError, field_validator

from constants import CATEGORIES, MENU_CSV, TEMPLATE_DIR

ROOT = Path(__file__).parent.parent.absolute()
LOGO_PATH = ROOT / "static" / "logo.jpg"
DEFAULT_OUTPUT = ROOT / "static" / "menu.pdf"


class PriceSize(BaseModel):
    price: int
    size: str


class MenuItem(BaseModel):
    name: str
    category: str
    description: str
    price_1: int
    size_1: str
    price_2: Optional[int] = None
    size_2: Optional[str] = None
    price_3: Optional[int] = None
    size_3: Optional[str] = None
    testimonials: list[str] = Field(default_factory=list)

    @field_validator("price_1", "price_2", "price_3", mode="before")
    @classmethod
    def validate_price(cls, v):
        if v is None or v == "":
            return None
        value = str(v).replace("₹", "").replace(",", "").strip()
        if not value.isdigit():
            raise ValueError(f"Invalid price format: {v}")
        return int(value)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in CATEGORIES:
            raise ValueError(
                f"Invalid category: '{v}'. Must be one of: {', '.join(CATEGORIES)}"
            )
        return v

    @field_validator("testimonials", mode="before")
    @classmethod
    def split_testimonials(cls, v) -> list[str]:
        if isinstance(v, str):
            return [t.strip() for t in v.split("|") if t.strip()]
        return v

    def price_sizes(self) -> list[PriceSize]:
        """Return all non-empty price/size pairs."""
        pairs = []
        for i in (1, 2, 3):
            p = getattr(self, f"price_{i}")
            s = getattr(self, f"size_{i}")
            if p is not None and s:
                pairs.append(PriceSize(price=p, size=s))
        return pairs


def load_items(csv_path: Path, ignore_errors: bool = False) -> list[MenuItem]:
    items = []
    errors = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("show", "").lower()[:1] != "y":
                continue
            try:
                item = MenuItem(
                    **{k: v for k, v in row.items() if k in MenuItem.model_fields}
                )
                items.append(item)
            except ValidationError as e:
                errors.append(f"Validation error for '{row.get('name')}': {e}")

    if errors:
        for err in errors:
            print(f"❌ {err}", file=sys.stderr)
        if not ignore_errors:
            sys.exit(1)

    return items


def group_by_category(items: list[MenuItem]) -> list[tuple[str, list[MenuItem]]]:
    grouped: dict[str, list[MenuItem]] = defaultdict(list)
    for item in items:
        grouped[item.category].append(item)
    return [(cat, grouped[cat]) for cat in CATEGORIES if grouped.get(cat)]


def logo_data_uri(logo_path: Path) -> str:
    data = base64.b64encode(logo_path.read_bytes()).decode()
    return f"data:image/png;base64,{data}"


def render_html(items: list[MenuItem]) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)
    template = env.get_template("menu-pdf.html")
    categories = group_by_category(items)
    generated = date.today().strftime("%-d %B %Y")
    return template.render(categories=categories, generated=generated)


def generate_pdf(html: str, output: Path, logo_uri: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    # Header: only the BW logo, top-right corner, on every page.
    # Title/subtitle live in the HTML body so they appear on page 1 only.
    header_template = (
        '<div style="box-sizing:border-box;width:100%;'
        'padding:5mm 31.8mm 0;text-align:right;font-size:0;">'
        f'<img src="{logo_uri}" style="width:28mm;height:auto;display:inline-block;">'
        "</div>"
    )

    # Footer: outer div provides side padding so the border-top only spans content width
    footer_template = (
        '<div style="box-sizing:border-box;width:100%;padding:0 31.8mm;'
        'font-family:Caladea,Cambria,Georgia,serif;">'
        '<div style="border-top:0.5pt solid #4f6228;padding-top:4pt;'
        'text-align:left;font-size:8pt;color:#4f6228;">'
        "* All prices are inclusive of GST. Delivery charges will be separate."
        "</div>"
        "</div>"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        # Ensure web fonts (Caladea via Google Fonts) are fully loaded before PDF render
        page.evaluate("document.fonts.ready")
        page.pdf(
            path=str(output),
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template=header_template,
            footer_template=footer_template,
            # NOTE: Change the CSS in menu-pdf.html if you adjust these
            # margins, to keep the layout consistent
            margin={
                "top": "30mm",
                "right": "31.8mm",
                "bottom": "20mm",
                "left": "31.8mm",
            },
        )
        browser.close()
    print(f"PDF written → {output}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output PDF path")
    ap.add_argument(
        "--save-html", metavar="PATH", help="Save rendered HTML for browser debugging"
    )
    ap.add_argument(
        "--ignore-errors",
        action="store_true",
        help="Skip invalid rows instead of exiting (for debugging)",
    )
    args = ap.parse_args()

    items = load_items(MENU_CSV, ignore_errors=args.ignore_errors)
    logo_uri = logo_data_uri(LOGO_PATH)
    html = render_html(items)

    if args.save_html:
        Path(args.save_html).write_text(html, encoding="utf-8")
        print(f"HTML saved → {args.save_html}")

    generate_pdf(html, Path(args.output), logo_uri)


if __name__ == "__main__":
    main()
