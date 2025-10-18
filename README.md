# Orange and Olive Co. — Website Generator

This repository powers the **Orange and Olive Co.** website from a Google
Sheet.

The site content (menu, images, and descriptions) is pulled directly from a
Google Sheet and Google Drive, converted into structured Markdown pages, and
published automatically to **https://orangeandoliveco.in** via **GitHub
Pages**.

---

## 🪄 How the Website Updates

If you only manage the bakery menu and product details:

1. **Open the Google Sheet**
   Update item names, descriptions, categories, prices, or images as needed.
   - Make sure the `show` column is set to “Yes” for items that should appear on the website.
   - Each item’s image must have a valid **Google Drive file ID**.

2. **Save your changes**
   No need to export or upload anything manually.

3. **Trigger a site update**
   - Go to the **GitHub Actions** tab of this repository.
   - Select **“Deploy to GitHub Pages”** → **Run workflow**.
   - Wait for it to finish (typically a couple of minutes).
   - Once it completes, the updated website will be live at:
     👉 **https://orangeandoliveco.in**

---

## 🧩 Local Build (for developers)

If you want to build or test the site locally:

1. **Install dependencies**
   ```bash
   uv sync --locked
   ```

2. **Set environment variable**
   ```bash
   export SPREADSHEET_ID="your-google-sheet-id"
   ```

3. **Run the build**
   ```bash
   ./scripts/build.sh
   ```

This script:
1. Downloads the latest sheet (`src/download.py`)
2. Generates site content (`src/generate.py`)
3. Runs Hugo (`./hugo.sh build`) to build into `public/`

---

## 🧠 Validation & Notes

- The CSV must contain columns like:
  `name`, `category`, `description`, `price`, `weight_unit`, `image`, `file_id`, `show`
- Only rows with `show = Yes` are included.
- Categories must match those defined in `src/constants.py`.
- Images larger than **1 MB** will trigger an error (to keep load times fast).
- Validation errors in the CSV will appear in the workflow logs and stop deployment.

---

## 🧾 License

GNU AGPL v3 © 2025 Orange and Olive Co.
