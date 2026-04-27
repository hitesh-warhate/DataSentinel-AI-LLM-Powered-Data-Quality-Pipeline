"""
database/db.py
--------------
PostgreSQL integration: schema creation, DDL execution,
Bronze ingestion, Silver promotion, stats.
"""
from __future__ import annotations
import os, logging
from contextlib import contextmanager

import pandas as pd
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

BRONZE_SCHEMA = os.getenv("BRONZE_SCHEMA", "bronze")
SILVER_SCHEMA  = os.getenv("SILVER_SCHEMA",  "silver")


def _conn_params() -> dict:
    return {
        "host":     os.getenv("POSTGRES_HOST",     "localhost"),
        "port":     int(os.getenv("POSTGRES_PORT", "5432")),
        "user":     os.getenv("POSTGRES_USER",     "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "dbname":   os.getenv("POSTGRES_DB",       "dq_pipeline"),
    }


@contextmanager
def get_connection():
    conn = psycopg2.connect(**_conn_params())
    conn.autocommit = False
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def test_connection() -> tuple[bool, str]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                ver = cur.fetchone()[0]
        return True, ver
    except Exception as exc:
        return False, str(exc)


def ensure_schemas() -> None:
    """Create bronze and silver schemas if they don't exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {BRONZE_SCHEMA};")
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SILVER_SCHEMA};")
    logger.info("Ensured schemas: %s, %s", BRONZE_SCHEMA, SILVER_SCHEMA)


def execute_ddl(bronze_ddl: str, silver_ddl: str) -> dict:
    """
    Execute Bronze and Silver DDL statements.
    Returns {"success": bool, "message": str}
    """
    try:
        ensure_schemas()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(bronze_ddl)
                cur.execute(silver_ddl)
        return {"success": True, "message": "Bronze and Silver tables created successfully."}
    except Exception as exc:
        logger.error("DDL execution failed: %s", exc)
        return {"success": False, "message": str(exc)}


def ingest_to_bronze(df: pd.DataFrame, table_name: str) -> dict:
    """
    Bulk-insert the raw DataFrame into the Bronze table.
    Returns {"success": bool, "rows_inserted": int, "message": str}
    """
    try:
        from sqlalchemy import create_engine
        p = _conn_params()
        engine = create_engine(
            f"postgresql+psycopg2://{p['user']}:{p['password']}@{p['host']}:{p['port']}/{p['dbname']}"
        )
        rows = len(df)
        df.to_sql(
            f"{table_name}_bronze",
            engine,
            schema=BRONZE_SCHEMA,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=500,
        )
        logger.info("Inserted %d rows into %s.%s_bronze", rows, BRONZE_SCHEMA, table_name)
        return {"success": True, "rows_inserted": rows, "message": f"Loaded {rows} rows into bronze."}
    except Exception as exc:
        logger.error("Bronze ingest failed: %s", exc)
        return {"success": False, "rows_inserted": 0, "message": str(exc)}


def promote_to_silver(bronze_to_silver_sql: str) -> dict:
    """Run the Bronze → Silver INSERT statement."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(bronze_to_silver_sql)
                rows = cur.rowcount
        logger.info("Promoted %d rows to Silver", rows)
        return {"success": True, "rows_promoted": rows, "message": f"Promoted {rows} rows to silver."}
    except Exception as exc:
        logger.error("Silver promotion failed: %s", exc)
        return {"success": False, "rows_promoted": 0, "message": str(exc)}


def get_layer_stats(stats_sql: str) -> dict | None:
    """Run the stats query and return a dict of counts."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(stats_sql)
                row = cur.fetchone()
                cols = [d[0] for d in cur.description]
        return dict(zip(cols, row)) if row else None
    except Exception as exc:
        logger.error("Stats query failed: %s", exc)
        return None


def run_custom_sql(query: str) -> tuple[list[dict] | None, str]:
    """Execute an arbitrary SELECT and return rows as list of dicts."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                cols = [d[0] for d in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return rows, ""
    except Exception as exc:
        return None, str(exc)
