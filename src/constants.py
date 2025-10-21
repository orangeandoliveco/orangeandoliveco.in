from pathlib import Path

ROOT = Path(__file__).parent.parent.absolute()
DATA_DIR = ROOT / "data"
DATA_RAW_IMAGES_DIR = DATA_DIR / "images_raw"
DATA_WEB_IMAGES_DIR = DATA_DIR / "images_web"
MENU_CSV = DATA_DIR / "menu.csv"
CONTENT_DIR = ROOT / "content"
TEMPLATE_DIR = ROOT / "templates"
ASSETS_DIR = ROOT / "assets"
MANIFEST_PATH = DATA_DIR / "manifest.json"

CATEGORIES = [
    "Cookies & Shortbreads",
    "Cakes & Puddings",
    "Granola & Pantry",
]
