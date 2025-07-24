import os
from pathlib import Path

ROOT = Path(__file__).parent.parent.absolute()
DATA_DIR = ROOT / "data"
DATA_IMAGES_DIR = DATA_DIR / "images"
MENU_CSV = DATA_DIR / "menu.csv"
CONTENT_DIR = ROOT / "content"
TEMPLATE_DIR = ROOT / "templates"
ASSETS_DIR = ROOT / "assets"

CATEGORIES = [
    "Cookies & Shortbreads",
    "Cakes & Puddings",
    "Granola & Pantry",
]

MAX_IMAGE_SIZE = 1 * 1024 * 1024  # 1MB
SITE_URL = "https://punchagan.github.io/experiri"
SITE_NAME = "Orange and Olive Co."
SITE_SUBTITLE = "Handcrafted Cakes, Cookies & Granola"
SITE_DESCRIPTION = """
Orange and Olive Co. is a home bakery in New Delhi, India, specializing in
artisan cookies, cakes, and granola. We offer a range of delicious treats made
with love and the finest ingredients.
"""
