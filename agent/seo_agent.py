from seo_app.excel_loader import *
from seo_app.executor import *
from seo_app.intent_parser import *
from seo_app.schema_discovery import *
from seo_app.schema_registry import *
from seo_app.schema_resolver import *
from seo_app.summarizer import *

def run_seo_agent(
    llm_client,
    excel_path: str,
    query: str
):
    sheets = load_screaming_frog(excel_path)
    schema = discover_schema(sheets)

    intent = parse_seo_intent(llm_client, query)

    df = execute_intent(sheets, schema, intent)

    if intent["output_mode"] == "rows":
        return df.head(100).to_dict(orient="records")

    if intent["output_mode"] == "summary":
        total = len(df)
        indexable = (df["indexability"] == "Indexable").sum()
        percent = (indexable / total) * 100 if total else 0

        return {
            "total_pages": total,
            "indexable_percentage": round(percent, 2),
            "assessment": seo_health_assessment(percent)
        }
