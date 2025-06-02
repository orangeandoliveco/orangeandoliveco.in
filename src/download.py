import os
import requests
import csv
from pathlib import Path

from constants import ROOT, DATA_DIR, DATA_IMAGES_DIR, MENU_CSV, MAX_IMAGE_SIZE


def download_google_sheet_as_csv(spreadsheet_id: str, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv"
    print(f"Downloading CSV from Google Sheets...")
    response = requests.get(url)
    response.raise_for_status()
    output_file.write_bytes(response.content)
    print(f"Downloaded sheet to {output_file}")


def download_drive_image(file_id: str, output_file: Path, check_size: bool) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    print(f"Downloading image from file ID: {file_id}")
    response = requests.get(url)
    response.raise_for_status()
    if check_size and len(response.content) > MAX_IMAGE_SIZE:
        raise ValueError(
            f"Image {file_id} is too large: {len(response.content) / 1024:.1f} KB"
        )
    output_file.write_bytes(response.content)
    print(f"Saved image to {output_file}")


def download_images_from_csv(
    csv_path: Path, image_output_dir: Path, check_size: bool = True
) -> None:
    image_output_dir.mkdir(parents=True, exist_ok=True)
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            file_id = row.get("file_id")
            if not file_id:
                print("❌ No file_id found in row, skipping...")
                continue
            image_name = row.get("image") or f"{file_id}.jpg"
            output_path = image_output_dir / image_name
            try:
                download_drive_image(file_id, output_path, check_size)
            except Exception as e:
                print(f"❌ Failed to download {file_id}: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download Google Sheets and images")

    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        raise EnvironmentError("SPREADSHEET_ID environment variable is not set")

    parser.add_argument(
        "--no-check-size",
        action="store_true",
        help="Don't check image sizes against the maximum allowed size",
    )
    args = parser.parse_args()

    download_google_sheet_as_csv(spreadsheet_id, MENU_CSV)
    download_images_from_csv(
        MENU_CSV, DATA_IMAGES_DIR, check_size=not args.no_check_size
    )
