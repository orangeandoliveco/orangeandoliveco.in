from typing import List, Dict
from dataclasses import dataclass
from pathlib import Path
import csv
import shutil
import sys

import jinja2
from pydantic import BaseModel, field_validator, Field, ValidationError

from constants import (
    MENU_CSV,
    DIST_DIR,
    TEMPLATE_DIR,
    ASSETS_DIR,
    DATA_IMAGES_DIR,
    CATEGORIES,
)


class MenuItem(BaseModel):
    name: str
    category: str
    description: str
    price: int
    image: str
    testimonials: list[str] = Field(default_factory=list)

    @field_validator("price", mode="before")
    @classmethod
    def validate_price(cls, v: str) -> str:
        value = v.replace("₹", "").replace(",", "").strip()
        if not value.isdigit():
            raise ValueError(f"Invalid price format: {v}")
        return value

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in CATEGORIES:
            raise ValueError(
                f"Invalid category: '{v}'. Must be one of: {', '.join(CATEGORIES)}"
            )
        return v

    @field_validator("image")
    @classmethod
    def validate_image(cls, v: str) -> str:
        if not v.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            raise ValueError(f"Unsupported image format: {v}")
        return v

    @field_validator("testimonials", mode="before")
    @classmethod
    def split_testimonials(cls, v) -> List[str]:
        if isinstance(v, str):
            return [t.strip() for t in v.split("|") if t.strip()]
        return v


def create_item_page(item: MenuItem, output_dir: Path, env: jinja2.Environment) -> None:
    template = env.get_template("item.html")
    html = template.render(
        name=item.name,
        description=item.description,
        category=item.category,
        price=item.price,
        image=item.image,
        testimonials=item.testimonials,
    )
    filename = f"{item.name.lower().replace(' ', '-')}.html"
    (output_dir / filename).write_text(html, encoding="utf-8")


def generate_site(csv_path: Path, output_path: Path) -> None:
    output_path.mkdir(parents=True, exist_ok=True)

    loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    env = jinja2.Environment(loader=loader)

    # Clean up the output directory
    if output_path.exists():
        shutil.rmtree(output_path)

    # Copy assets to output directory
    static_dir = output_path / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    for asset in ASSETS_DIR.glob("*"):
        if asset.is_file():
            target_path = static_dir / asset.name
            shutil.copy(asset, target_path)

    # Copy images from data/images to output directory
    images_dir = output_path / "images"
    images_dir.mkdir(exist_ok=True)
    for image in DATA_IMAGES_DIR.glob("*"):
        if image.is_file():
            target_path = images_dir / image.name
            shutil.copy(image, target_path)

    # Render index.html to output directory
    index_template = env.get_template("index.html")
    index_html = index_template.render()
    (output_path / "index.html").write_text(index_html, encoding="utf-8")

    # Make item pages
    errors = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["show"].lower()[:1] != "y":
                continue
            try:
                item = MenuItem(**row)
            except ValidationError as e:
                errors.append(f"Validation error for row — {row['name']}: {e}")
                continue
            create_item_page(item, output_path, env)

    if errors:
        print("Errors encountered during validation:")
        for error in errors:
            print(f"❌ {error}")

    return errors


if __name__ == "__main__":
    errors = generate_site(MENU_CSV, DIST_DIR)
    if errors:
        print("Site generation completed with errors.")
        sys.exit(1)
    else:
        print("Site generated successfully.")
