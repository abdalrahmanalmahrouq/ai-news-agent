import httpx
from bs4 import BeautifulSoup
from agent.state import AgentState


async def scraper_node(state: AgentState) -> dict:
    urls = state["urls"]
    raw_articles = []

    async with httpx.AsyncClient(timeout=10) as client:
        for url in urls:
            try:
                response = await client.get(url)
                soup = BeautifulSoup(response.text, "html.parser")

                raw_articles.append({
                    "url": url,
                    "title": soup.title.text.strip() if soup.title else "No title",
                    "body_text": soup.get_text(separator=" ", strip=True)[:3000],
                    "source": url,
                })

                print(f"✓ Scraped: {url}")

            except Exception as e:
                print(f"✗ Failed: {url} — {e}")

    return {"raw_articles": raw_articles}
