import os
import requests
import gzip
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

URLS = {
    "listings.csv.gz": os.getenv("LISTINGS_URL"),
    "reviews.csv.gz": os.getenv("REVIEWS_URL"),
    "calendar.csv.gz": os.getenv("CALENDAR_URL"),
    "neighbourhoods.csv": os.getenv("NEIGHBOURHOODS_URL"),
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TokyoAirbnbProject/1.0)"
}


def download_file(url: str, dest: Path):
    if not url:
        print(f"  SKIP: no URL configured for {dest.name}")
        return False
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"  EXISTS: {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
        return True

    print(f"  DOWNLOADING {dest.name}...")
    resp = requests.get(url, headers=HEADERS, stream=True, timeout=300)
    resp.raise_for_status()

    if dest.suffix == ".gz" or ".gz" in str(dest):
        with gzip.GzipFile(fileobj=resp.raw) as gz:
            with open(dest.with_suffix("").with_suffix(".csv"), "wb") as f:
                shutil.copyfileobj(gz, f)
        dest.unlink(missing_ok=True)
        final = dest.with_suffix("").with_suffix(".csv")
    else:
        with open(dest, "wb") as f:
            shutil.copyfileobj(resp.raw, f)
        final = dest

    size_mb = final.stat().st_size / 1e6
    print(f"  DONE: {final.name} ({size_mb:.1f} MB)")
    return True


def main():
    print("Downloading Tokyo Airbnb data...")
    for filename, url in URLS.items():
        dest = DATA_DIR / filename
        download_file(url, dest)
    print("All downloads complete!")


if __name__ == "__main__":
    main()
