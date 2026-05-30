from langgraph.graph import StateGraph, START, END
from agent.state import AgentState
from agent.scraper import scraper_node
from agent.reader import reader_node
from agent.validator import validator_node
from agent.validator import routing_function
import asyncio


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("scraper", scraper_node)
    graph.add_node("reader", reader_node)
    graph.add_node("validator", validator_node)


    graph.add_edge(START, "scraper")
    graph.add_edge("scraper", "reader")
    graph.add_edge("reader", "validator")

    graph.add_conditional_edges(
        "validator",
        routing_function,
        {
            "continue": END,
            "retry": "reader"
        }
    )

    return graph.compile()


# quick local test
if __name__ == "__main__":

    app = build_graph()

    initial_state = {
        "urls": ["https://hnrss.org/frontpage"],
        "raw_articles": [],
        "summaries": [],
        "validated": [],
        "run_meta": {},
    }

    result = asyncio.run(app.ainvoke(initial_state))

    print("\n--- VALIDATED ---")
    for s in result["validated"]:
        print(f"Headline:  {s['headline']}")
        print(f"Score:     {s['relevance_score']}")
        print()

    print(f"Total validated: {len(result['validated'])}")
    print(f"Retry count: {result['run_meta'].get('retry_count', 0)}")