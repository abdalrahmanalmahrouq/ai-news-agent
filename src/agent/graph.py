from langgraph.graph import StateGraph, START, END
from agent.state import AgentState
from agent.scraper import scraper_node
import asyncio


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("scraper", scraper_node)

    graph.add_edge(START, "scraper")
    graph.add_edge("scraper", END)

    return graph.compile()


# quick local test
if __name__ == "__main__":

    app = build_graph()

    initial_state = {
        "urls": ["https://hnrss.org/frontpage"],
        "raw_articles": [],
    }

    result = asyncio.run(app.ainvoke(initial_state))

    print("\n--- RESULT ---")
    for article in result["raw_articles"]:
        print(f"Title: {article['title']}")
        print(f"Body preview: {article['body_text'][:200]}...\n")