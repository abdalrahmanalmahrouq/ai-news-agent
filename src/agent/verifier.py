import os
import asyncio
from dotenv import load_dotenv
from loguru import logger
from tavily import TavilyClient
from agent.state import AgentState

load_dotenv()

CONCURRENCY = 5


async def verify_one(client: TavilyClient, summary: dict, semaphore: asyncio.Semaphore):
    headline = summary.get("headline", "")
    async with semaphore:
        try:
            response = await asyncio.to_thread(
                client.search,
                headline,
                search_depth="basic",
                max_result=5
            )
            count = len(response.get("results", []))
            verified = count >= 1
            summary["verified"] = verified
            summary["sources_found"] = count

            if verified:
                logger.info("✓ Verified ({} sources): {}", count, headline[:60])
            else:
                logger.warning("✗ Unverified ({} sources): {}", count, headline[:60])
        except Exception as e:
            logger.warning("Search failed for '{}' — {}", headline[:40], e)
            summary["verified"] = True
            summary["sources_found"] = 0


async def verifier_node(state: AgentState) -> dict:
    summaries = state.get("summaries", [])
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        logger.warning("Verifier: TAVILY_API_KEY not set — skipping, all marked verified")
        for s in summaries:
            s["verified"] = True
            s["sources_found"] = 0
        return {"summaries": summaries}

    client = TavilyClient(api_key=api_key)
    semaphore = asyncio.Semaphore(CONCURRENCY)
    logger.info("Verifying {} article(s)...", len(summaries))

    await asyncio.gather(
        *(verify_one(client, s, semaphore) for s in summaries)
    )

    return {"summaries": summaries}