from langgraph.graph import StateGraph, START, END
from agent.state import AgentState
from agent.scraper import scraper_node
from agent.reader import reader_node
import asyncio


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("scraper", scraper_node)
    graph.add_node("reader", reader_node)

    graph.add_edge(START, "scraper")
    graph.add_edge("scraper", "reader")
    graph.add_edge("reader", END)

    return graph.compile()


# quick local test
if __name__ == "__main__":

    app = build_graph()

    initial_state = {
        "urls": ["https://hnrss.org/frontpage"],
        "raw_articles": [],
        "summaries": [],
    }

    result = asyncio.run(app.ainvoke(initial_state))

    print("\n--- SUMMARIES ---")
    for s in result["summaries"]:
        print(f"Headline:  {s['headline']}")
        print(f"Category:  {s['category']}")
        print(f"Score:     {s['relevance_score']}")
        print(f"Summary:   {s['summary']}")
        print()