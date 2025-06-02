from pathlib import Path

ROOT = Path(__file__).parent.parent.absolute()
DATA_DIR = ROOT / "data"
DATA_IMAGES_DIR = DATA_DIR / "images"
MENU_CSV = DATA_DIR / "menu.csv"
DIST_DIR = ROOT / "dist"
TEMPLATE_DIR = ROOT / "templates"
ASSETS_DIR = ROOT / "assets"

CATEGORIES = [
    "Cookies & Shortbreads",
    "Cakes & Puddings",
    "Granola & Pantry",
]

MAX_IMAGE_SIZE = 1 * 1024 * 1024  # 1MB
