from typing import List, Dict
from dataclasses import dataclass
from pathlib import Path
import csv
import jinja2
import shutil

from constants import MENU_CSV, DIST_DIR, TEMPLATE_DIR, ASSETS_DIR, DATA_IMAGES_DIR


@dataclass
class MenuItem:
    name: str
    category: str
    description: str
    price: str
    image: str
    testimonials: List[str]


def parse_csv_row(row: Dict[str, str]) -> MenuItem:
    return MenuItem(
        name=row["name"],
        category=row["category"],
        description=row["description"],
        price=row["price"],
        image=row["image"],
        testimonials=[t.strip() for t in row["testimonials"].split("|") if t.strip()],
    )


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
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item = parse_csv_row(row)
            create_item_page(item, output_path, env)


if __name__ == "__main__":
    generate_site(MENU_CSV, DIST_DIR)
