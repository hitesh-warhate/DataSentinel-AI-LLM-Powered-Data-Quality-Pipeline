"""
agents/dq_agent.py
-------------------
AutoGen-style agent that analyses a DataFrame and generates
Pydantic-based Data Quality rules for every column.
"""
from __future__ import annotations
from utils.llm import call_llm
import os, json, logging
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _profile_column(series: pd.Series) -> dict:
    """Compute basic statistics for a single column."""
    dtype = str(series.dtype)
    profile = {
        "column":       series.name,
        "dtype":        dtype,
        "null_count":   int(series.isna().sum()),
        "null_pct":     round(float(series.isna().mean()) * 100, 2),
        "unique_count": int(series.nunique()),
        "total_count":  int(len(series)),
    }
    non_null = series.dropna()
    if dtype.startswith(("int", "float")):
        num = pd.to_numeric(non_null, errors="coerce").dropna()
        if len(num):
            profile.update({
                "min": float(num.min()),
                "max": float(num.max()),
                "mean": round(float(num.mean()), 4),
            })
    else:
        sample = non_null.astype(str)
        lengths = sample.str.len()
        profile.update({
            "min_length": int(lengths.min()) if len(lengths) else 0,
            "max_length": int(lengths.max()) if len(lengths) else 0,
            "sample_values": sample.head(5).tolist(),
        })
    return profile


def _profile_dataframe(df: pd.DataFrame) -> list[dict]:
    return [_profile_column(df[col]) for col in df.columns]


def generate_dq_rules(df: pd.DataFrame, table_name: str) -> dict:
    """
    Ask Gemini to produce a JSON list of DQ rules for the dataset.
    Returns {"rules": list[dict], "pydantic_code": str}
    """
    profiles = _profile_dataframe(df)
    profile_str = json.dumps(profiles, indent=2)

    prompt = f"""You are a Data Quality expert. Analyse the following column profiles
for the table "{table_name}" and generate comprehensive Data Quality rules.

Column profiles:
{profile_str}

Return a JSON object with two keys:

1. "rules": a list of DQ rule objects. Each rule object must have:
   {{
     "column": "<column_name>",
     "rule_name": "<short_snake_case_name>",
     "rule_type": "<one of: not_null | min_value | max_value | min_length | max_length | regex | allowed_values | uniqueness>",
     "description": "<human-readable description>",
     "threshold": <numeric or string value>,
     "severity": "<critical | warning>"
   }}

2. "pydantic_code": a single Python code string containing a complete Pydantic v2
   model class called `{table_name.title().replace('_','')}DQModel` that enforces
   the most important rules using Field validators and @field_validator decorators.
   Properly escape newlines and quotes in the JSON string (use \\n for newlines, \\" for quotes).

Generate at least 2 rules per column. Be specific using the actual min/max/length
values from the profiles. Output ONLY valid JSON, no markdown, no explanation."""

    raw = call_llm(prompt).strip()

    parsed = None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        # Try to fix common JSON issues
        import re
        logger.warning("Initial JSON parse failed for '%s': %s", table_name, str(e))
        
        # Try extracting just the JSON block if markdown is present
        match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # If still no luck, try raw extraction of braces
        if not parsed:
            match = re.search(r"(\{.*\})", raw, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(1))
                except json.JSONDecodeError as inner_e:
                    logger.error("Could not parse JSON from LLM response. Error: %s", str(inner_e))
                    logger.debug("Raw LLM response: %s", raw[:500])
        
        if not parsed:
            parsed = {"rules": [], "pydantic_code": ""}

    logger.info("DQ agent generated %d rules for '%s'", len(parsed.get("rules", [])), table_name)
    return {
        "table_name":    table_name,
        "rules":         parsed.get("rules", []),
        "pydantic_code": parsed.get("pydantic_code", ""),
        "profiles":      profiles,
    }


def run_dq_agent(df: pd.DataFrame, table_name: str) -> dict:
    """Entry point for DQ agent."""
    return generate_dq_rules(df, table_name)
