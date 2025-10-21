from typing import List
from pathlib import Path
import csv
import shutil
import sys
import yaml

from pydantic import BaseModel, field_validator, Field, ValidationError

from constants import (
    MENU_CSV,
    CONTENT_DIR,
    CATEGORIES,
    DATA_WEB_IMAGES_DIR,
)
from utils import slugify


class MenuItem(BaseModel):
    name: str = Field(serialization_alias="title")
    category: str
    description: str
    price: int
    weight_unit: str
    image: str
    testimonials: list[str] = Field(default_factory=list)

    @field_validator("price", mode="before")
    @classmethod
    def validate_price(cls, v: str) -> str:
        value = v.replace("₹", "").replace(",", "").strip()
        if not value.isdigit():
            raise ValueError(f"Invalid price format: {v}")
        return value

    @field_validator("weight_unit")
    @classmethod
    def validate_weight_unit(cls, v: str) -> str:
        return v.strip() or "kg"

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
        if not v.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".heic")):
            raise ValueError(f"Unsupported image format: {v}")
        return v

    @field_validator("testimonials", mode="before")
    @classmethod
    def split_testimonials(cls, v) -> List[str]:
        if isinstance(v, str):
            return [t.strip() for t in v.split("|") if t.strip()]
        return v


def create_item_markdown(item: MenuItem, output_dir: Path, images_dir: Path) -> None:
    slug = slugify(item.name)
    image = item.image = f"{slug}.jpg"
    item_dir = output_dir / slug
    item_dir.mkdir(parents=True, exist_ok=True)

    src_image_path = images_dir / image
    dst_image_path = item_dir / image
    if src_image_path.exists():
        shutil.copy(src_image_path, dst_image_path)
    else:
        print(f"⚠ Image {src_image_path} not found.")

    front_matter = item.model_dump(by_alias=True, exclude_none=True)
    markdown = f"---\n{yaml.dump(front_matter, sort_keys=False)}---\n\n"
    markdown += f"{item.description}\n\n"

    with (item_dir / f"index.md").open("w", encoding="utf-8") as f:
        f.write(markdown)


def generate_site_content(
    csv_path: Path, content_path: Path, images_dir: Path
) -> List[str]:
    content_path.mkdir(parents=True, exist_ok=True)

    # Clean up the content directory
    if content_path.exists():
        shutil.rmtree(content_path)

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
            print(f"Creating page for {item.name}...")
            create_item_markdown(item, content_path / "items", images_dir)

    # Make menu page
    menu_dir = content_path / "menu"
    menu_dir.mkdir(parents=True, exist_ok=True)
    with (menu_dir / "_index.md").open("w", encoding="utf-8") as f:
        f.write("---\n")
        f.write("title: Our Menu\n")
        f.write("---\n\n")

    if errors:
        print("Errors encountered during validation:")
        for error in errors:
            print(f"❌ {error}")

    return errors


if __name__ == "__main__":
    errors = generate_site_content(MENU_CSV, CONTENT_DIR, DATA_WEB_IMAGES_DIR)
    if errors:
        print("Site generation completed with errors.")
        sys.exit(1)
    else:
        print("Site generated successfully.")
