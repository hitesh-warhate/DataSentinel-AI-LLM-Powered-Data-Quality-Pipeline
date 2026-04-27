"""
agents/ddl_agent.py
--------------------
AutoGen agent that reads CSV metadata and generates Bronze + Silver DDL.
"""
from __future__ import annotations
from utils.llm import call_llm
import os, re, json, logging
import pandas as pd
from dotenv import load_dotenv


load_dotenv()
logger = logging.getLogger(__name__)


BRONZE_SCHEMA = os.getenv("BRONZE_SCHEMA", "bronze")
SILVER_SCHEMA  = os.getenv("SILVER_SCHEMA",  "silver")


def _infer_pg_type(series: pd.Series) -> str:
    """Map a pandas Series dtype to a PostgreSQL type."""
    dtype = str(series.dtype)
    if dtype.startswith("int"):      return "BIGINT"
    if dtype.startswith("float"):    return "DOUBLE PRECISION"
    if dtype == "bool":              return "BOOLEAN"
    if dtype.startswith("datetime"): return "TIMESTAMP"
    # Try numeric coercion for object columns
    sample = series.dropna().head(50)
    try:
        pd.to_numeric(sample)
        if sample.astype(str).str.contains(r"\.").any():
            return "DOUBLE PRECISION"
        return "BIGINT"
    except Exception:
        pass
    return "TEXT"


def extract_metadata(df: pd.DataFrame) -> list[dict]:
    """Return list of {column, pg_type, nullable, sample_values}."""
    meta = []
    for col in df.columns:
        meta.append({
            "column":        col,
            "pg_type":       _infer_pg_type(df[col]),
            "nullable":      bool(df[col].isna().any()),
            "sample_values": df[col].dropna().astype(str).head(3).tolist(),
        })
    return meta


def generate_ddl(table_name: str, metadata: list[dict]) -> dict:
    """
    Use Gemini to produce Bronze + Silver CREATE TABLE DDL.
    Returns {"bronze": str, "silver": str, "metadata": list}
    """
    meta_str = json.dumps(metadata, indent=2)
    
    # Build explicit NOT NULL column list for clarity
    not_null_cols = [m["column"] for m in metadata if not m["nullable"]]
    nullable_cols = [m["column"] for m in metadata if m["nullable"]]
    
    not_null_str = ", ".join(f'"{col}"' if " " in col else col for col in not_null_cols) if not_null_cols else "(none)"
    nullable_str = ", ".join(f'"{col}"' if " " in col else col for col in nullable_cols) if nullable_cols else "(none)"
    
    # Quote table name if it contains special characters
    needs_quotes = any(c in table_name for c in '-./() \t')
    
    bronze_table_name = f'{table_name}_bronze'
    silver_table_name = f'{table_name}_silver'
    
    bronze_table = f'{BRONZE_SCHEMA}."{bronze_table_name}"' if needs_quotes else f'{BRONZE_SCHEMA}.{bronze_table_name}'
    silver_table = f'{SILVER_SCHEMA}."{silver_table_name}"' if needs_quotes else f'{SILVER_SCHEMA}.{silver_table_name}'

    prompt = f"""You are a PostgreSQL DDL expert.

Given this column metadata for a CSV table called "{table_name}":
{meta_str}

Columns that MUST be NOT NULL in Silver (nullable=false): {not_null_str}
Columns that MUST be NULLABLE in Silver (nullable=true): {nullable_str}

Generate exactly two CREATE TABLE IF NOT EXISTS statements:

1. Bronze layer table: {bronze_table}
   - Contains ALL columns from the metadata exactly as listed
   - Add: ingested_at TIMESTAMP DEFAULT NOW()
   - ALL columns NULLABLE (raw data, no constraints)
   - Do NOT add NOT NULL to any column

2. Silver layer table: {silver_table}
   - Contains ALL columns from the metadata exactly as listed
   - For columns where nullable=false: add NOT NULL constraint
   - For columns where nullable=true: do NOT add NOT NULL constraint (allow NULLs)
   - Add: processed_at TIMESTAMP DEFAULT NOW(), dq_passed BOOLEAN DEFAULT TRUE
   - Apply correct PostgreSQL data types from the metadata

Rules:
- Use {BRONZE_SCHEMA} and {SILVER_SCHEMA} schema prefixes exactly
- Table names with special characters (hyphens, spaces, etc): wrap entire schema.table reference in double quotes, e.g. "{bronze_table}"
- Column names with spaces: wrap in double quotes
- Output ONLY valid SQL, no markdown, no explanations
- Separate the two statements with: -- SILVER --
- CRITICAL: Follow the nullable flags exactly. If nullable=true, the column MUST allow NULLs

Output format:
<bronze DDL here>
-- SILVER --
<silver DDL here>"""

    raw = call_llm(prompt).strip()

    # Split on the separator
    parts = raw.split("-- SILVER --")
    bronze_ddl = parts[0].strip() if len(parts) >= 1 else ""
    silver_ddl  = parts[1].strip() if len(parts) >= 2 else ""

    # Strip any accidental markdown fences
    for fence in ["```sql", "```"]:
        bronze_ddl = bronze_ddl.replace(fence, "").strip()
        silver_ddl  = silver_ddl.replace(fence, "").strip()

    # Guarantee IF NOT EXISTS to prevent 'already exists' errors
    bronze_ddl = re.sub(r"CREATE\s+TABLE\s+(?!IF\s+NOT\s+EXISTS)", "CREATE TABLE IF NOT EXISTS ", bronze_ddl, flags=re.IGNORECASE)
    silver_ddl = re.sub(r"CREATE\s+TABLE\s+(?!IF\s+NOT\s+EXISTS)", "CREATE TABLE IF NOT EXISTS ", silver_ddl, flags=re.IGNORECASE)

    logger.info("DDL agent generated Bronze + Silver DDL for '%s'", table_name)
    logger.debug("Nullable columns: %s", nullable_cols)
    logger.debug("NOT NULL columns: %s", not_null_cols)
    
    return {
        "table_name": table_name,
        "bronze_ddl": bronze_ddl,
        "silver_ddl":  silver_ddl,
        "metadata":    metadata,
        "nullable_cols": nullable_cols,
        "not_null_cols": not_null_cols,
    }


def run_ddl_agent(df: pd.DataFrame, table_name: str) -> dict:
    """Entry point: extract metadata → generate DDL."""
    metadata = extract_metadata(df)
    return generate_ddl(table_name, metadata)
