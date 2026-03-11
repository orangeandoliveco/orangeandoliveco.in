from pathlib import Path

ROOT = Path(__file__).parent.parent.absolute()
DATA_DIR = ROOT / "data"
MENU_CSV = DATA_DIR / "menu.csv"
TEMPLATE_DIR = ROOT / "templates"

CATEGORIES = [
    "Cakes",
    "Cookies and Shortbreads",
    "Granola and Pantry",
]
