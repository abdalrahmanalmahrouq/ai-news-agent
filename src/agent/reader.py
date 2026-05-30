import json 
from agent.state import AgentState
from agent.llm import get_llm


llm = get_llm()

SUMMARY_PROMPT = """You are an AI news analyst. Read the article below and return a JSON object with exactly these fields:

{{
    "headline": "one clear headline under 15 words",
    "summary": "exactly 3 sentences summarizing the article",
    "category": "one of: AI, Tools, Research, Industry, Other",
    "relevance_score": a float between 0.0 and 1.0 measuring relevance to AI/tech professionals
}}

Rules:
- Return ONLY the JSON object. No explanation, no markdown, no code blocks.
- relevance_score: 0.9-1.0 = must read, 0.6-0.8 = interesting, below 0.6 = low value
- If the article has no useful content, still return the JSON with relevance_score below 0.3

Article URL: {url}
Article Title: {title}
Article Content: {body_text}
"""

async def reader_node(state: AgentState) -> dict:
    raw_articles = state['raw_articles']
    summaries = []

    for article in raw_articles:
        try:
            prompt = SUMMARY_PROMPT.format(
                url=article["url"],
                title=article["title"],
                body_text=article["body_text"][:2000]
            )

            response = llm.invoke(prompt)  # actual llm call 
            raw = response.content.strip()

            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            
            parsed = json.loads(raw)

            summaries.append({
                "url": article["url"],
                "headline": parsed.get("headline", "No headline"),
                "summary": parsed.get("summary", "No summary"),
                "category": parsed.get("category", "Other"),
                "relevance_score": float(parsed.get("relevance_score", 0.5)),
            })

            print(f"✓ Summarized: {article['title'][:60]}")

        except Exception as e:
            print(f"✗ Failed to summarize: {article['url']} — {e}")
        
    return {"summaries": summaries}