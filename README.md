# Orange and Olive Co. — Website Generator

This repository powers the **Orange and Olive Co.** website from a Google
Sheet.

The site content (menu, images, and descriptions) is pulled directly from a
Google Sheet and Google Drive, converted into structured Markdown pages, and
published automatically to **https://orangeandoliveco.in** via **GitHub
Pages**.

---

<!-- This section is shown as 'help instructions' in the Excel spreadsheet. -->

<!-- instructions-start -->

## 🪄 How to update the website

The menu data is stored in a Google Sheet, and the images are stored in a
Google Drive.

To update the site, you can follow these steps:

1. **Open the Google Sheet**

   - Update item names, descriptions, categories, prices, or images as needed.
   - Make sure the `show` column is set to "y" for items that should appear on
     the website.
   - Each item must also have an "image" name filled in, for it to appear on
     the website.

2. **Save your changes**

   No need to export or upload anything manually. The site will be updated
   automatically in about two hours. If you need a faster update, you can
   manually trigger a build.

3. **Trigger a site update**
   - Go to the [**GitHub Actions** tab](https://github.com/orangeandoliveco/orangeandoliveco.in/actions/workflows/build.yml) of this repository.
   - Select **“Deploy to GitHub Pages”** → **Run workflow**.
   - Wait for it to finish (typically a couple of minutes).
   - Once it completes, the updated website will be live at:
     👉 **https://orangeandoliveco.in**

<!-- instructions-end -->

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
