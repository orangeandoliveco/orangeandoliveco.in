from pathlib import Path

ROOT = Path(__file__).parent.parent.absolute()
DATA_DIR = ROOT / "data"
BUILD_DIR = ROOT / "_build"
MENU_CSV = BUILD_DIR / "menu.csv"
TEMPLATE_DIR = ROOT / "templates"

CATEGORIES = [
    "Cakes",
    "Cookies and Shortbreads",
    "Granola and Pantry",
]
