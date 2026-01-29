# Dagster Quickstart Guide

## 1. Installation

```bash
pip install dagster dagster-webserver
```

## 2. Project Setup

Create this structure:
```
my_dagster_project/
├── data/
│   ├── input/
│   └── output/
├── definitions.py
└── __init__.py
```

## 3. Core Concepts

- **Asset**: A data artifact (CSV file, database table, etc.)
- **Job**: A pipeline that produces assets
- **Sensor**: Watches for changes and triggers jobs
- **Lineage**: Tracks how assets depend on each other

## 4. Basic Example: definitions.py

```python
import pandas as pd
from pathlib import Path
from dagster import asset, Definitions, define_asset_job, AssetSelection, sensor, RunRequest, SensorEvaluationContext
import os

DATA_DIR = Path(__file__).parent / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

# Ensure directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============ ASSETS ============

@asset
def raw_sales_data() -> pd.DataFrame:
    """Generate sample CSV data."""
    df = pd.DataFrame({
        "product": ["A", "B", "C", "A", "B"],
        "quantity": [10, 20, 15, 5, 25],
        "price": [100, 200, 150, 100, 200]
    })
    df.to_csv(INPUT_DIR / "sales.csv", index=False)
    return df

@asset(deps=[raw_sales_data])
def copied_sales_data() -> pd.DataFrame:
    """Copy CSV to output folder."""
    df = pd.read_csv(INPUT_DIR / "sales.csv")
    df.to_csv(OUTPUT_DIR / "sales_copy.csv", index=False)
    return df

@asset(deps=[copied_sales_data])
def transformed_sales_data() -> pd.DataFrame:
    """Transform: add total column."""
    df = pd.read_csv(OUTPUT_DIR / "sales_copy.csv")
    df["total"] = df["quantity"] * df["price"]
    df.to_csv(OUTPUT_DIR / "sales_transformed.csv", index=False)
    return df

@asset(deps=[transformed_sales_data])
def sales_summary() -> pd.DataFrame:
    """Aggregate by product."""
    df = pd.read_csv(OUTPUT_DIR / "sales_transformed.csv")
    summary = df.groupby("product").agg({
        "quantity": "sum",
        "total": "sum"
    }).reset_index()
    summary.to_csv(OUTPUT_DIR / "sales_summary.csv", index=False)
    return summary

# ============ JOB ============

sales_pipeline_job = define_asset_job(
    name="sales_pipeline_job",
    selection=AssetSelection.all()
)

# ============ SENSOR ============

@sensor(job=sales_pipeline_job, minimum_interval_seconds=10)
def file_change_sensor(context: SensorEvaluationContext):
    """Trigger job when input file changes."""
    file_path = INPUT_DIR / "sales.csv"
    if not file_path.exists():
        return
    
    mtime = os.path.getmtime(file_path)
    last_mtime = float(context.cursor) if context.cursor else 0
    
    if mtime > last_mtime:
        context.update_cursor(str(mtime))
        yield RunRequest(run_key=f"file_change_{mtime}")

# ============ DEFINITIONS ============

defs = Definitions(
    assets=[raw_sales_data, copied_sales_data, transformed_sales_data, sales_summary],
    jobs=[sales_pipeline_job],
    sensors=[file_change_sensor]
)
```

## 5. Run the UI

```bash
cd my_dagster_project
dagster dev -f definitions.py
```

Open: http://localhost:3000

## 6. Using the UI

| Tab | Purpose |
|-----|---------|
| **Assets** | View all assets and their lineage graph |
| **Jobs** | Run pipelines manually |
| **Runs** | See execution history and logs |
| **Sensors** | Enable/disable file watchers |

### To see lineage:
1. Go to **Assets** tab
2. Click **View global asset lineage** (top right)
3. See: `raw_sales_data → copied_sales_data → transformed_sales_data → sales_summary`

### To run manually:
1. Go to **Assets** tab
2. Select assets → Click **Materialize selected**

### To enable sensor:
1. Go to **Sensors** tab
2. Toggle **file_change_sensor** ON
3. Edit `data/input/sales.csv` → job triggers automatically

## 7. Data Lineage Explained

```
raw_sales_data          # Source (generates data)
       ↓
copied_sales_data       # Copy step
       ↓
transformed_sales_data  # Transform (add calculations)
       ↓
sales_summary           # Aggregate output
```

Dagster tracks:
- Which asset depends on which
- When each was last updated
- Whether assets are stale (upstream changed)

## 8. Next Steps: SQL Server

For SQL Server transformations, you'll use:

```python
from dagster import asset, resource
import pyodbc

@asset
def source_table() -> pd.DataFrame:
    conn = pyodbc.connect("DRIVER={SQL Server};SERVER=...;DATABASE=...")
    return pd.read_sql("SELECT * FROM source_table", conn)

@asset(deps=[source_table])
def target_table(source_table: pd.DataFrame):
    conn = pyodbc.connect("DRIVER={SQL Server};SERVER=...;DATABASE=...")
    source_table.to_sql("target_table", conn, if_exists="replace", index=False)
```

Install: `pip install pyodbc pandas sqlalchemy`

## Quick Reference

| Command | Purpose |
|---------|---------|
| `dagster dev -f definitions.py` | Start UI |
| `dagster job execute -f definitions.py -j sales_pipeline_job` | Run job from CLI |
| `dagster asset materialize -f definitions.py --select raw_sales_data` | Materialize single asset |
