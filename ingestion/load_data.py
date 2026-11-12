import pandas as pd
import duckdb
from pathlib import Path
from datetime import datetime, timezone

# 1. Define project paths
PROJECT_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_DIR / "data" / "raw"
DATABASE_PATH = PROJECT_DIR / "data" / "flightpulse.duckdb"

# 2. Find the CSV file
csv_files = list(RAW_DIR.glob("*.csv"))

if not csv_files:
    raise FileNotFoundError(
        "No CSV file found inside data/raw/"
    )

csv_file = csv_files[0]

print(f"Reading file: {csv_file.name}")

# 3. Extract: Read CSV data

#python reads the CSV file and stores its contents in a Pandas DF
df = pd.read_csv(csv_file, low_memory=False)

print(f"Rows extracted: {len(df):,}")

# 4. Basic standardization

#standardizing the column names from all caps to lower case
df.columns = [
    column.strip().lower().replace(" ", "_")
    for column in df.columns
]

# 5. Validate essential columns
required_columns = ["fl_date", "origin", "dest"]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

# 6. Add ingestion metadata
df["source_file"] = csv_file.name
df["ingested_at"] = datetime.now(timezone.utc).isoformat()

# 7. Load: Connect to DuckDB
connection = duckdb.connect(str(DATABASE_PATH))

# 8. Load Records into the database

connection.register("incoming_flights", df)
#making a database table called raw_fights and inserting the records
connection.execute("""
                   CREATE OR REPLACE TABLE raw_flights AS
                   SELECT * FROM incoming_flights
                   """)

# 9. Verify the database load
result = connection.execute("""
                            SELECT COUNT(*) FROM raw_flights
                            """).fetchone()

print(f"Rows loaded: {result[0]:,}")

print("ETL ingestion completed successfully!")

connection.close()