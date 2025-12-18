from utils.packages import *
from utils.config import *
from app.ga4_schema_validator import *
from app.nl_parser import *
from app.ga4_client import *
from app.summarizer import *
app = FastAPI()


class AnalyticsRequest(BaseModel):
    propertyId: str
    query: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analytics/query")
def analytics_query(req: AnalyticsRequest):
    try:
        parsed = parse_query(req.query)
        # validate_fields(parsed["metrics"], parsed["dimensions"])
        metrics, dimensions = validate_with_auto_repair(
            client,
            req.propertyId,
            parsed["metrics"],
            parsed["dimensions"]
        )
        # validate_ga4_query(
        #     property_id=req.propertyId,
        #     metrics=parsed["metrics"],
        #     dimensions=parsed["dimensions"]
        # )

        # report_type = infer_report_type(parsed["dimensions"])

        rows = run_report(
        property_id=req.propertyId,
        metrics=metrics,
        dimensions=dimensions,
        start_date=parsed["start_date"],
        end_date=parsed["end_date"],
        page_path=parsed.get("page_path")
        )


        summary = summarize(rows, metrics)


        return {
            "metadata": parsed,
            "data": rows,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))