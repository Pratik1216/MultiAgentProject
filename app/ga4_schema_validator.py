from utils.packages import *

"""
GA4 Validator with Metadata API + Rule-based checks + LLM Auto-repair
NO caching (no lru_cache)
"""

from typing import List
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.oauth2 import service_account


# -----------------------------
# Constants
# -----------------------------

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]

TIME_DIMENSIONS = {
    "date", "dateHour", "dateHourMinute", "week", "month", "year"
}

EVENT_DIMENSIONS = {
    "eventName", "eventCategory", "eventLabel"
}

ITEM_DIMENSIONS = {
    "itemName", "itemBrand", "itemCategory","browser","city","cohort"
}

SESSION_METRICS = {
    "sessions",
    "averageSessionDuration",
    "engagementRate",
    "sessionsPerUser"
}

USER_METRICS = {
    "totalUsers",
    "activeUsers",
    "newUsers"
}

ADS_METRICS = {
    "advertiserAdClicks",
    "advertiserAdCost",
    "advertiserAdImpressions"
}


# -----------------------------
# Errors
# -----------------------------

class GA4ValidationError(Exception):
    def __init__(self, reason, metrics, dimensions):
        super().__init__(reason)
        self.reason = reason
        self.metrics = metrics
        self.dimensions = dimensions


# -----------------------------
# Metadata Loader (NO CACHE)
# -----------------------------

def load_metadata(property_id: str):
    credentials = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/analytics.readonly"]
    )

    client = BetaAnalyticsDataClient(credentials=credentials)

    metadata = client.get_metadata(
        name=f"properties/{property_id}/metadata"
    )

    metric_blocked_dims = {
        m.api_name: set(m.blocked_dimensions)
        for m in metadata.metrics
    }

    dimension_set = {d.api_name for d in metadata.dimensions}

    return metric_blocked_dims, dimension_set



# -----------------------------
# Core Validation
# -----------------------------

def validate_ga4_query(
    property_id: str,
    metrics: List[str],
    dimensions: List[str]
):
    # metric_map, dimension_set = load_metadata(property_id)
    metric_blocked_dims, dimension_set = load_metadata(property_id)
    # ---- existence checks ----
    for m in metrics:
        if m not in metric_map:
            raise GA4ValidationError(
                f"Invalid GA4 metric: {m}", metrics, dimensions
            )

    for d in dimensions:
        if d not in dimension_set:
            raise GA4ValidationError(
                f"Invalid GA4 dimension: {d}", metrics, dimensions
            )

    # ---- compatibility (authoritative) ----
    for m in metrics:
        blocked = metric_blocked_dims[m]
        invalid_dims = set(dimensions) & blocked
        if invalid_dims:
            raise GA4ValidationError(
                f"Metric '{m}' incompatible with dimensions {list(invalid_dims)}",
                metrics,
                dimensions
            )

    # ---- rule-based guards ----
    if SESSION_METRICS & set(metrics) and EVENT_DIMENSIONS & set(dimensions):
        raise GA4ValidationError(
            "Session metrics cannot be broken down by event dimensions",
            metrics,
            dimensions
        )

    if USER_METRICS & set(metrics) and ITEM_DIMENSIONS & set(dimensions):
        raise GA4ValidationError(
            "User metrics cannot be broken down by item dimensions",
            metrics,
            dimensions
        )

    if ADS_METRICS & set(metrics):
        raise GA4ValidationError(
            "Ads metrics require Ads-linked GA4 property",
            metrics,
            dimensions
        )

    return True


# -----------------------------
# LLM Auto-repair
# -----------------------------

def build_repair_prompt(error, metric_map, dimension_set):
    return f"""
You are a Google Analytics 4 query repair agent.

The GA4 query below is INVALID.

Reason:
{error.reason}

Metrics:
{error.metrics}

Dimensions:
{error.dimensions}

VALID METRICS:
{list(metric_map.keys())}

VALID DIMENSIONS:
{list(dimension_set)}

Rules:
- Use ONLY valid metrics and dimensions
- Ensure compatibility
- Preserve original intent
- Prefer removing invalid dimensions over changing metrics

Return STRICT JSON ONLY.

Format:
{{
  "metrics": [...],
  "dimensions": [...]
}}
"""


def llm_repair_query(
    client,
    property_id: str,
    error: GA4ValidationError
):
    metric_map, dimension_set = load_metadata(property_id)

    prompt = build_repair_prompt(error, metric_map, dimension_set)

    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    from app.nl_parser import safe_json_loads
    return safe_json_loads(response.choices[0].message.content)


# -----------------------------
# Validation + Repair Loop
# -----------------------------

def validate_with_auto_repair(
    client,
    property_id: str,
    metrics: List[str],
    dimensions: List[str],
    retries: int = 1
):
    try:
        validate_ga4_query(property_id, metrics, dimensions)
        return metrics, dimensions

    except GA4ValidationError as e:
        if retries <= 0:
            raise

        repaired = llm_repair_query(client, property_id, e)

        return validate_with_auto_repair(
            client,
            property_id,
            repaired["metrics"],
            repaired["dimensions"],
            retries - 1
        )


