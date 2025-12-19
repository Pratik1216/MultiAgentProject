from utils.packages import *
from agent.seo_agent import *
from utils.config import *

app = FastAPI()

class SEORequest(BaseModel):
    query: str
    file_path: str

@app.post("/seo/query")
def seo_query(req: SEORequest):
    result = run_seo_agent(
        llm_client=client,
        excel_path=req.file_path,
        query=req.query
    )
    return {"result": result}
