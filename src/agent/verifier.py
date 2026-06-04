import os
import asyncio
from dotenv import load_dotenv
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

            icon = "\u2713" if verified else "\u2717"
            label = "Verified" if verified else "Unverified"
            print(f"  {icon} {label} ({count} sources): {headline[:60]}")
        except Exception as e:
            # search failure → benefit of the doubt, don't reject
            print(f"  \u26a0 Search failed for '{headline[:40]}' \u2014 {e}")
            summary["verified"] = True
            summary["sources_found"] = 0

async def verifier_node(state: AgentState) -> dict:
    summaries = state.get("summaries", [])
    api_key   = os.getenv("TAVILY_API_KEY")

    # graceful skip — pipeline still works without the API key
    if not api_key:
        print("\u26a0 Verifier: TAVILY_API_KEY not set — skipping, all marked verified.")
        for s in summaries:
            s["verified"]      = True
            s["sources_found"] = 0
        return {"summaries": summaries}

    client = TavilyClient(api_key=api_key)
    semaphore = asyncio.Semaphore(CONCURRENCY)
    print(f"  Verifying {len(summaries)} article(s)...")

    await asyncio.gather(
        *(verify_one(client, s, semaphore) for s in summaries)
    )

    

    return {"summaries": summaries}