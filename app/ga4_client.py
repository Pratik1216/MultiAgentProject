from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest, FilterExpression, Filter
from google.oauth2 import service_account


def get_client():
    credentials = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/analytics.readonly"]
        )
    return BetaAnalyticsDataClient(credentials=credentials)

def run_report(property_id, metrics, dimensions, start_date, end_date, page_path=None):
    client = get_client()


    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        metrics=[Metric(name=m) for m in metrics],
        dimensions=[Dimension(name=d) for d in dimensions]
        )


    if page_path:
        request.dimension_filter = FilterExpression(
            filter=Filter(
                field_name="pagePath",
                string_filter=Filter.StringFilter(value=page_path)
            )
        )


    response = client.run_report(request)


    rows = []
    for row in response.rows:
        entry = {"date": row.dimension_values[0].value}
        for i, m in enumerate(metrics):
            entry[m] = int(row.metric_values[i].value)
        rows.append(entry)

    return rows
