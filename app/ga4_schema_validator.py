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

METRIC_ALIASES = {
    # ecommerce
    "purchases": "ecommercePurchases",
    "purchase": "ecommercePurchases",

    # events
    "conversions": "keyEvents",
    "conversion": "keyEvents",

    # pages
    "pageviews": "screenPageViews",
    "page views": "screenPageViews",
    "page_views": "screenPageViews",

    # sessions
    "events per session": "eventsPerSession",
    "eventcountpersession": "eventsPerSession",

    # revenue
    "revenue": "totalRevenue"
}

DIMENSION_ALIASES = {
    # pages
    "page": "pagePath",
    "page path": "pagePath",
    "page url": "pagePathPlusQueryString",

    # geo
    "country name": "country",
    "location": "country",
    "city name": "city",

    # device
    "device": "deviceCategory",
    "os": "operatingSystem",
    "operating system": "operatingSystem",

    # traffic
    "source": "source",
    "source / medium": "sourceMedium",
    "traffic source": "sourceMedium",
    "campaign": "campaignName",

    # time
    "day": "date",
    "daily": "date",
    "week": "week",
    "month": "month"
}

def normalize_metrics(metrics: list[str]) -> list[str]:
    normalized = []

    for m in metrics:
        key = m.lower().replace(" ", "")
        canonical = METRIC_ALIASES.get(key) or METRIC_ALIASES.get(m.lower())
        normalized.append(canonical if canonical else m)
        
    return normalized

def normalize_dimensions(dimensions: list[str]) -> list[str]:
    normalized = []
    for d in dimensions:
        key = d.lower().strip()
        normalized.append(DIMENSION_ALIASES.get(key, d))
    return normalized

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

    metric_types = {
        m.api_name: m.type_
        for m in metadata.metrics
    }

    dimension_set = {d.api_name for d in metadata.dimensions}

    return metric_types, dimension_set




# -----------------------------
# Core Validation
# -----------------------------

def validate_ga4_query(property_id, metrics, dimensions):
    metric_types, dimension_set = load_metadata(property_id)

    # --- existence ---
    for m in metrics:
        if m not in metric_types:
            raise GA4ValidationError(f"Invalid GA4 metric: {m}", metrics, dimensions)

    for d in dimensions:
        if d not in dimension_set:
            raise GA4ValidationError(f"Invalid GA4 dimension: {d}", metrics, dimensions)

    # --- scope rules ---
    for m in metrics:
        metric_type = metric_types[m]

        if metric_type == "SESSION" and EVENT_DIMENSIONS & set(dimensions):
            raise GA4ValidationError(
                "Session metrics cannot be broken down by event dimensions",
                metrics,
                dimensions
            )

        if metric_type == "USER" and ITEM_DIMENSIONS & set(dimensions):
            raise GA4ValidationError(
                "User metrics cannot be broken down by item dimensions",
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
IMPORTANT:
GA4 metric names MUST match the GA4 Data API exactly.

Examples:
- Use "ecommercePurchases" NOT "purchases"
- Use "eventsPerSession" NOT "eventCountPerSession"
- Use "screenPageViews" NOT "pageViews"
- Use "keyEvents" NOT "conversions"

If unsure, choose the closest valid GA4 metric.
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
        metrics = normalize_metrics(metrics)
        dimensions = normalize_dimensions(dimensions)
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


