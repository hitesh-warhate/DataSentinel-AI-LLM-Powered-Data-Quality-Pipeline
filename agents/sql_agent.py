"""
agents/sql_agent.py
--------------------
AutoGen-style agent that converts DQ rules into SQL INSERT statements
that move data from Bronze → Silver, applying quality filters.
"""
from __future__ import annotations
from utils.llm import call_llm
import os, json, logging
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
_model = genai.GenerativeModel("gemini-2.0-flash")

BRONZE_SCHEMA = os.getenv("BRONZE_SCHEMA", "bronze")
SILVER_SCHEMA  = os.getenv("SILVER_SCHEMA",  "silver")


def generate_sql_queries(table_name: str, rules: list[dict], metadata: list[dict]) -> dict:
    """
    Given DQ rules and column metadata, produce:
    1. A WHERE clause that enforces all critical rules
    2. A full INSERT INTO silver SELECT FROM bronze statement
    3. A validation count query
    """
    rules_str    = json.dumps(rules, indent=2)
    metadata_str = json.dumps(metadata, indent=2)
    columns      = [m["column"] for m in metadata]
    col_list     = ", ".join(f'"{c}"' if " " in c else c for c in columns)
    
    # Quote table name if it contains special characters
    needs_quotes = any(c in table_name for c in '-./() \t')
    
    bronze_table_name = f'{table_name}_bronze'
    silver_table_name = f'{table_name}_silver'
    
    bronze_table = f'{BRONZE_SCHEMA}."{bronze_table_name}"' if needs_quotes else f'{BRONZE_SCHEMA}.{bronze_table_name}'
    silver_table = f'{SILVER_SCHEMA}."{silver_table_name}"' if needs_quotes else f'{SILVER_SCHEMA}.{silver_table_name}'
    
    # Build NOT NULL checks for non-nullable columns
    not_null_cols = [m["column"] for m in metadata if not m.get("nullable", True)]
    not_null_checks = " AND ".join(
        f'"{c}" IS NOT NULL' if " " in c else f'{c} IS NOT NULL'
        for c in not_null_cols
    ) if not_null_cols else "1=1"

    prompt = f"""You are a PostgreSQL SQL expert specialising in data quality pipelines.

Table: {table_name}
Bronze table: {bronze_table}
Silver table:  {silver_table}

Column metadata:
{metadata_str}

Data Quality rules to enforce:
{rules_str}

CRITICAL CONSTRAINT - These columns must NEVER be NULL in Silver:
{', '.join(f'"{c}"' if ' ' in c else c for c in not_null_cols) if not_null_cols else '(none)'}

Generate the following SQL statements:

1. bronze_to_silver_sql: An INSERT INTO ... SELECT statement that:
   - MUST use this exact INSERT format: INSERT INTO {silver_table} ({col_list}, processed_at, dq_passed)
   - MUST explicitly select the columns (DO NOT use SELECT *): SELECT {col_list}, NOW() AS processed_at, TRUE AS dq_passed FROM {bronze_table}
   - Applies ALL critical severity DQ rules as WHERE conditions
   - ALSO includes: {not_null_checks}
   - Uses proper PostgreSQL syntax (cast, NULLIF, TRIM, etc. where needed)

2. failed_records_sql: A SELECT statement that retrieves FAILED records
   (those that do NOT pass the critical DQ rules) from the bronze table.
   Add a "failure_reason" TEXT column using CASE WHEN to describe why each row failed.

3. stats_sql: A SELECT that returns counts:
   total_records, passed_records, failed_records, pass_rate_pct
   by comparing bronze and silver table counts.

Output a JSON object with exactly these keys:
{{
  "bronze_to_silver_sql": "...",
  "failed_records_sql": "...",
  "stats_sql": "..."
}}

Output ONLY the JSON. No markdown, no explanation."""

    raw = call_llm(prompt).strip()

    try:
        parsed = json.loads(raw)
    except Exception:
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        parsed = json.loads(match.group()) if match else {}

    logger.info("SQL agent generated queries for '%s'", table_name)
    logger.debug("NOT NULL columns enforced: %s", not_null_cols)
    return {
        "table_name":           table_name,
        "bronze_to_silver_sql": parsed.get("bronze_to_silver_sql", ""),
        "failed_records_sql":   parsed.get("failed_records_sql", ""),
        "stats_sql":            parsed.get("stats_sql", ""),
        "not_null_cols":        not_null_cols,
    }


def run_sql_agent(table_name: str, rules: list[dict], metadata: list[dict]) -> dict:
    """Entry point for SQL agent."""
    return generate_sql_queries(table_name, rules, metadata)
