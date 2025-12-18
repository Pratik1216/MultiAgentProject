from datetime import date, timedelta
import re
import json
import os

# ---------------- Rule-based fallback ----------------
METRIC_MAP = {
    "page views": "screenPageViews",
    "pageviews": "screenPageViews",
    "users": "totalUsers",
    "sessions": "sessions"
}

DIMENSIONS = ["date"]

# Enabled only if OPENAI_API_KEY is present
def llm_parse(query: str):
    try:
        if not os.getenv("OPENAI_API_KEY"):
            return None

        from openai import OpenAI
        client = OpenAI()

        prompt = f"""
You are a GA4 analytics query parser.

Extract:
- GA4 metrics (screenPageViews, totalUsers, sessions,...)
- Number of days
- Optional page path

Return STRICT JSON ONLY.

Query:
{query}

JSON format:
{{
  "metrics": ["screenPageViews", "totalUsers"],
  "days": 14,
  "page_path": "/pricing"
}}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        return json.loads(response.choices[0].message.content)

    except Exception:
        # Any failure → fallback to rules
        return None


# ---------------- Unified parser ----------------
def parse_query(query: str):
    # 1️⃣ Try LLM-based parsing
    llm_result = llm_parse(query)

    if llm_result:
        days = llm_result.get("days", 7)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        return {
            "metrics": llm_result.get("metrics", []),
            "dimensions": DIMENSIONS,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "page_path": llm_result.get("page_path"),
            "dateRange": f"last {days} days",
            "parser": "llm"
        }

    # 2️⃣ Deterministic rule-based fallback
    q = query.lower()

    metrics = [v for k, v in METRIC_MAP.items() if k in q]
    if not metrics:
        raise ValueError("No valid GA4 metrics found in query")

    days_match = re.search(r"last (\d+) days", q)
    days = int(days_match.group(1)) if days_match else 7

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    page_match = re.search(r"/(\w+)", q)
    page_path = f"/{page_match.group(1)}" if page_match else None

    return {
        "metrics": metrics,
        "dimensions": DIMENSIONS,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "page_path": page_path,
        "dateRange": f"last {days} days",
        "parser": "rules"
    }
