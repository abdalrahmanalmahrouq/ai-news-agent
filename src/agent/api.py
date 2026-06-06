import uuid
from loguru import logger
from fastapi import FastAPI, BackgroundTasks, HTTPException
from agent.graph import run_pipeline

# Feeds used when /run is triggered. (You can accept these from the request later.)
DEFAULT_FEEDS = ["https://hnrss.org/frontpage"]

# Live status board: run_id -> {"status": ...}. In memory only — resets on restart.
RUNS: dict[str, dict] = {}

app = FastAPI(title="AI News Agent")

logger.add("../data/logs/agent.log", rotation="1 day", retention="7 days", level="INFO")

async def run_and_track(run_id: str, urls: list[str]) -> None:
    """Background wrapper: run the pipeline and record its status in RUNS."""
    RUNS[run_id] = {"status": "running"}
    logger.info("Background task started | run_id={}", run_id)
    try:
        final_state = await run_pipeline(urls, run_id=run_id)
        run_meta = final_state.get("run_meta", {})
        RUNS[run_id] = {
            "status": "completed",
            "scraped": len(final_state.get("raw_articles", [])),
            "validated": len(final_state.get("validated", [])),
            "delivered_to": run_meta.get("delivered_to", []),
        }
        logger.info("Run completed | run_id={} | validated={}", run_id, RUNS[run_id]["validated"])
    except Exception as e:
        RUNS[run_id] = {"status": "failed", "error": str(e)}
        logger.error("Run failed | run_id={} | error={}", run_id, e)

@app.get("/")
async def root():
    return {"ok": True, "service": "AI News Agent"}


@app.post("/run")
async def trigger_run(background_tasks: BackgroundTasks):
    """Start a pipeline run in the background; return a run_id immediately."""
    run_id = str(uuid.uuid4())[:8]
    RUNS[run_id] = {"status": "running"}
    background_tasks.add_task(run_and_track, run_id, DEFAULT_FEEDS)
    logger.info("Run triggered | run_id={}", run_id)
    return {"run_id": run_id, "status": "started"}


@app.get("/status/{run_id}")
async def get_status(run_id: str):
    """Report the status of a run by its run_id."""
    if run_id not in RUNS:
        raise HTTPException(status_code=404, detail="run_id not found")
    return {"run_id": run_id, **RUNS[run_id]}