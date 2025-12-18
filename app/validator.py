VALID_METRICS = {
"screenPageViews",
"totalUsers",
"sessions"
}


VALID_DIMENSIONS = {
"date",
"pagePath"
}


def validate_fields(metrics, dimensions):
    if set(metrics) - VALID_METRICS:
        raise ValueError("Invalid GA4 metric requested")
    if set(dimensions) - VALID_DIMENSIONS:
        raise ValueError("Invalid GA4 dimension requested")