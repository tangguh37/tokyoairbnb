import duckdb
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DB_PATH = Path(os.getenv("DB_PATH", "data/tokyo_airbnb.duckdb"))

CSV_FILES = {
    "raw_listings": DATA_DIR / "listings.csv",
    "raw_reviews": DATA_DIR / "reviews.csv",
    "raw_calendar": DATA_DIR / "calendar.csv",
    "raw_neighbourhoods": DATA_DIR / "neighbourhoods.csv",
}


def ingest():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))

    print(f"Connected to {DB_PATH}")
    con.execute("SET memory_limit = '2GB'")

    for table, csv_path in CSV_FILES.items():
        if not csv_path.exists():
            print(f"  SKIP {table}: {csv_path.name} not found (run make download first)")
            continue

        print(f"  Loading {csv_path.name} -> {table} ...")
        con.execute(f"DROP TABLE IF EXISTS {table}")
        con.execute(f"""
            CREATE TABLE {table} AS
            SELECT * FROM read_csv_auto('{csv_path}', header=true)
        """)
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"    Loaded {count:,} rows")

    print("\nVerifying tables:")
    tables = con.execute(
        "SELECT table_name, (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as cols "
        "FROM (SELECT table_name FROM information_schema.tables WHERE table_schema = 'main') t"
    ).fetchall()
    for tbl, cols in tables:
        cnt = con.execute(f"SELECT COUNT(*) FROM \"{tbl}\"").fetchone()[0]
        print(f"  {tbl}: {cnt:,} rows, {cols} columns")

    con.close()
    print(f"\nIngest complete. DB saved to {DB_PATH}")


if __name__ == "__main__":
    ingest()
