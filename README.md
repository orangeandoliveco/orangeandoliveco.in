# Orange and Olive Co. — Website Generator

This repository powers the **Orange and Olive Co.** website from a Google
Sheet.

The menu data is pulled from a publicly-accessible Google Sheet, a PDF menu
is generated from it, and the site is published to
**https://orangeandoliveco.in** via **GitHub Pages**.

> **Note on images:** Individual item images are not currently shown on the
> site. The architecture is designed to support them in future — the CSV has
> columns for images, and the Hugo templates are in place.

---

<!-- This section is shown as 'help instructions' in the Excel spreadsheet. -->

<!-- instructions-start -->

## 🪄 How to update the website

The menu data is stored in a Google Sheet. To update the site:

1. **Open the Google Sheet**

   - Update item names, descriptions, categories, prices, or sizes as needed.
   - Use `price_1` / `size_1` for the primary price, and `price_2` / `size_2`
     (etc.) for additional sizes.
   - Set the `show` column to `y` for items that should appear in the menu.

2. **Trigger a site update**

   The site rebuilds automatically on code change. To trigger it
   manually (e.g. after updating only the sheet):
   - Go to the [**GitHub Actions** tab](https://github.com/orangeandoliveco/orangeandoliveco.in/actions/workflows/build.yml).
   - Select **"Update menu on website"** → **Run workflow**.
   - Wait for it to finish (typically 2–3 minutes).
   - The updated site and PDF menu will be live at:
     👉 **https://orangeandoliveco.in**

<!-- instructions-end -->

---

## 🧩 Local Build (for developers)

### Prerequisites

```bash
uv sync --locked
uv run playwright install --with-deps chromium
sudo apt-get install -y fonts-crosextra-caladea  # Cambria-compatible font
```

### Build steps

1. **Set the spreadsheet ID**
   ```bash
   export SPREADSHEET_ID="your-google-sheet-id"
   ```

2. **Run the full build**
   ```bash
   ./scripts/build.sh
   ```

   This runs three steps:
   1. `src/download.py` — fetches `data/menu.csv` from the public Google Sheet
   2. `src/generate_pdf.py` — renders `static/menu.pdf` via Playwright (HTML → PDF)
   3. `./hugo.sh build` — builds the site into `public/`

### Debugging the PDF

To inspect or tweak the PDF layout in a browser:

```bash
# Save the rendered HTML (logo embedded as base64, so it opens standalone)
uv run python src/generate_pdf.py --save-html /tmp/menu_debug.html

# Open in Chrome, then: DevTools → Rendering → Emulate CSS media type → print
```

To generate a test PDF without overwriting `static/menu.pdf`:

```bash
uv run python src/generate_pdf.py --output /tmp/menu_test.pdf
```

To skip validation errors (useful when iterating on new CSV columns):

```bash
uv run python src/generate_pdf.py --ignore-errors --output /tmp/menu_test.pdf
```

---

## 🧠 CSV Format

The sheet must have a `menu` tab with these columns:

| Column | Required | Notes |
|--------|----------|-------|
| `name` | ✓ | Item name |
| `category` | ✓ | Must match one of the categories in `src/constants.py` |
| `description` | | Free text |
| `price_1` | ✓ | Primary price (numeric) |
| `size_1` | ✓ | Primary size/unit (e.g. `1 kg`, `6 cookies`) |
| `price_2`, `size_2` | | Optional second size |
| `price_3`, `size_3` | | Optional third size |
| `show` | ✓ | Set to `y` to include in the menu |

Validation errors appear in workflow logs and stop deployment.

---

## 🧾 License

GNU AGPL v3 © 2025 Orange and Olive Co.
