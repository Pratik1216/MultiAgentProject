from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.nl_parser import parse_query
from app.validator import validate_fields
from app.ga4_client import run_report
from app.summarizer import summarize


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
        validate_fields(parsed["metrics"], parsed["dimensions"])


        rows = run_report(
        property_id=req.propertyId,
        metrics=parsed["metrics"],
        dimensions=parsed["dimensions"],
        start_date=parsed["start_date"],
        end_date=parsed["end_date"],
        page_path=parsed.get("page_path")
        )


        summary = summarize(rows, parsed["metrics"])


        return {
            "metadata": parsed,
            "data": rows,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))