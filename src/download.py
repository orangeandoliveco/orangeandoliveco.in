#!/usr/bin/env python3
"""
Download menu data and images using Google APIs (Sheets + Drive), not public links.

- Reads a Sheet tab via Sheets API and writes data/menu.csv
- Streams image bytes from Drive via fileId (Drive API)
- Maintains a manifest of raw image hashes to avoid unnecessary reprocessing
- Generates web-friendly images (JPEG/WebP)

Env:
  GOOGLE_APPLICATION_CREDENTIALS = /path/to/service-account.json
  SPREADSHEET_ID = <your sheet id>

CLI:
  uv run python src/fetch_api.py --sheet-tab menu [--fix-images]
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import time
from pathlib import Path
from typing import List

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image
from pillow_heif import register_heif_opener

from constants import DATA_RAW_IMAGES_DIR, DATA_WEB_IMAGES_DIR, MANIFEST_PATH, MENU_CSV
from utils import slugify

RAW_MAX_BYTES = 4 * 1024 * 1024
WEB_MAX_BYTES = 1 * 1024 * 1024
MAX_DIM = 1200
EMIT_JPEG = True
EMIT_WEBP = False
JPEG_QUALITY_START = 85
WEBP_QUALITY_START = 80
SHEETS_READ_SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"
DRIVE_READ_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
DRIVE_WRITE_SCOPE = "https://www.googleapis.com/auth/drive.file"

register_heif_opener()


def _credentials(scopes=None):
    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if scopes is None:
        scopes = [SHEETS_READ_SCOPE, DRIVE_READ_SCOPE]
    if not key_path:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS env var is not set")
    return service_account.Credentials.from_service_account_file(
        key_path, scopes=scopes
    )


def _sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def _load_manifest() -> dict:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"images": {}}


def _save_manifest(m: dict) -> None:
    MANIFEST_PATH.write_text(
        json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def fetch_sheet_to_csv(spreadsheet_id: str, sheet_tab: str, out_csv: Path) -> None:
    """Read values from a Sheet tab and write a CSV (first row = headers)."""
    sheets = build("sheets", "v4", credentials=_credentials())
    resp = (
        sheets.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=sheet_tab)
        .execute()
    )
    values: List[List[str]] = resp.get("values", [])
    if not values:
        raise RuntimeError(f"No data returned from sheet tab '{sheet_tab}'")

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for row in values:
            writer.writerow(row)
    print(f"Sheet '{sheet_tab}' → {out_csv}")


def _drive_download_bytes(
    file_id: str, credentials: service_account.Credentials
) -> bytes:
    drive = build("drive", "v3", credentials=credentials)
    req = drive.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, req, chunksize=1024 * 1024)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue()


def _drive_list_files(dir_id: str, credentials) -> list[dict[str, str]]:
    """List files in a Google Drive folder by ID.

    NOTE: Make sure the directory is shared with the service account email!

    """
    drive = build("drive", "v3", credentials=credentials)
    query = f"'{dir_id}' in parents and trashed = false"
    files = []
    page_token = None

    while True:
        resp = (
            drive.files()
            .list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType)",
                pageSize=1000,
                pageToken=page_token,
            )
            .execute()
        )
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return files


def _ensure_dirs():
    DATA_RAW_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    DATA_WEB_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _save_image(raw_path: Path, content: bytes) -> None:
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(content)


def _save_with_budget(
    img: Image.Image, out_path: Path, fmt: str, max_bytes: int, q_start: int
) -> None:
    """Adaptive quality loop to keep bytes <= max_bytes."""

    img2 = img.copy()
    img2.thumbnail((MAX_DIM, MAX_DIM))

    best_q = q_start
    while best_q >= 30:
        params = {"format": fmt, "optimize": True, "quality": best_q}
        if fmt.upper() == "JPEG":
            img2 = img2.convert("RGB")
        img2.save(out_path, **params)
        size = out_path.stat().st_size

        if size <= max_bytes:
            break
        else:
            best_q -= 5


def _generate_web_images(raw_path: Path, base_stem: str) -> dict:
    out = {}
    img = Image.open(raw_path)

    if EMIT_JPEG:
        jpg = DATA_WEB_IMAGES_DIR / f"{base_stem}.jpg"
        _save_with_budget(img, jpg, "JPEG", WEB_MAX_BYTES, JPEG_QUALITY_START)
        out["jpeg"] = jpg.name
        out["jpeg_bytes"] = jpg.stat().st_size
    if EMIT_WEBP:
        webp = DATA_WEB_IMAGES_DIR / f"{base_stem}.webp"
        _save_with_budget(img, webp, "WEBP", WEB_MAX_BYTES, WEBP_QUALITY_START)
        out["webp"] = webp.name
        out["webp_bytes"] = webp.stat().st_size
    return out


def download_images_from_csv(
    csv_path: Path, google_drive_id: str, fix_images: bool = False
) -> list[str]:
    credentials = _credentials()
    files = _drive_list_files(google_drive_id, credentials)

    web_dir_ids = [f for f in files if f["name"] == "web"]
    if web_dir_ids:
        web_dir_id = web_dir_ids[0]["id"]
        web_files = _drive_list_files(web_dir_id, credentials)
        web_files = {f["name"]: f["id"] for f in web_files}
    else:
        # Make web dir if missing.
        scopes = [DRIVE_READ_SCOPE, DRIVE_WRITE_SCOPE]
        credentials = _credentials(scopes=scopes)
        resp = (
            build("drive", "v3", credentials=credentials)
            .files()
            .create(
                body={
                    "name": "web",
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [google_drive_id],
                }
            )
            .execute()
        )
        web_dir_id = resp.get("id")
        web_files = {}

    _ensure_dirs()
    manifest = _load_manifest()
    m = manifest["images"]

    errors, new_rows = [], []
    manual_upload = False
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        for row in reader:
            new_rows.append(row)
            name = (row.get("name") or "").strip()
            if not name:
                continue
            image_raw_name = row.get("image")
            if not image_raw_name:
                print(f"❌ No image name for item '{name}', skipping...")
                continue

            matching_files = [f for f in files if f["name"] == image_raw_name]
            file_id = matching_files[0].get("id") if matching_files else None
            if not file_id:
                print(
                    f"❌ No file with ID '{image_raw_name}' found in Drive, skipping..."
                )
                continue

            slug = slugify(name)
            # Keep the existing image name for raw storage
            raw_path = DATA_RAW_IMAGES_DIR / image_raw_name

            try:
                # Always refetch to detect changed bytes on same file_id
                content = _drive_download_bytes(file_id, credentials)
                raw_sha = _sha256_bytes(content)
                raw_bytes = len(content)

                if raw_bytes > RAW_MAX_BYTES:
                    errors.append(
                        f"⚠ Raw {image_raw_name} {raw_bytes/1024:.0f}KB > {RAW_MAX_BYTES/1024:.0f}KB"
                    )

                prev = m.get(file_id, {})
                raw_changed = prev.get("raw_sha") != raw_sha

                if raw_changed or not raw_path.exists():
                    _save_image(raw_path, content)

                need_web = fix_images or raw_changed
                jpeg_path = DATA_WEB_IMAGES_DIR / f"{slug}.jpg"
                webp_path = DATA_WEB_IMAGES_DIR / f"{slug}.webp"

                if webp_path.name in web_files:
                    webp_file_id = web_files[webp_path.name]
                    webp_content = _drive_download_bytes(webp_file_id, credentials)
                    webp_path.write_bytes(webp_content)

                if jpeg_path.name in web_files:
                    jpeg_file_id = web_files[jpeg_path.name]
                    jpeg_content = _drive_download_bytes(jpeg_file_id, credentials)
                    jpeg_path.write_bytes(jpeg_content)

                if not jpeg_path.exists() and not webp_path.exists():
                    need_web = True
                    manual_upload = True

                if need_web:
                    out = _generate_web_images(raw_path, slug)
                else:
                    out = {}
                    if jpeg_path.exists():
                        out["jpeg"] = jpeg_path.name
                        out["jpeg_bytes"] = jpeg_path.stat().st_size
                    if webp_path.exists():
                        out["webp"] = webp_path.name
                        out["webp_bytes"] = webp_path.stat().st_size

                # Update manifest and CSV row
                m[file_id] = {
                    "name": name,
                    "raw_name": image_raw_name,
                    "raw_sha": raw_sha,
                    "raw_bytes": raw_bytes,
                    "slug": slug,
                    **out,
                    "updated_at": int(time.time()),
                }

            except Exception as e:
                errors.append(f"❌ file_id={file_id}: {e}")
                raise e

    _save_manifest(manifest)
    if manual_upload:
        url = f"https://drive.google.com/drive/folders/{web_dir_id}"
        errors.append(
            f"⚠ Some web images were generated but need to be manually uploaded to Drive at {url}. "
            "Upload the 'data/images_web' directory!"
        )
    return errors


def main():
    ssid = os.environ.get("SPREADSHEET_ID")
    if not ssid:
        raise RuntimeError("SPREADSHEET_ID env var is not set")

    gdid = os.environ.get("GOOGLE_DRIVE_ID")
    if not gdid:
        raise RuntimeError("GOOGLE_DRIVE_ID env var is not set")

    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet-tab", default="menu", help="Sheet tab name (e.g., 'menu')")
    ap.add_argument(
        "--fix-images",
        action="store_true",
        help="(Re)generate web images & write updated CSV",
    )
    args = ap.parse_args()

    # 1) Fetch sheet → CSV
    fetch_sheet_to_csv(ssid, args.sheet_tab, MENU_CSV)

    # 2) Download images from Drive (by file_id), process if needed
    errs = download_images_from_csv(MENU_CSV, gdid, fix_images=args.fix_images)
    if errs:
        print("Completed with warnings/errors:")
        for e in errs:
            print(f" -{e}")
    else:
        print("✅ Data & images up to date")


if __name__ == "__main__":
    main()
