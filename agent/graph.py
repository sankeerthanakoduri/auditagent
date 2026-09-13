from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    abstain,
    critic,
    planner,
    reformulate,
    retrieve,
    sql_query,
    synthesizer,
    verifier,
    web_search,
)


class AgentState(TypedDict, total=False):
    question: str
    user_role: str

    route: str

    search_query: str
    retrieval_attempts: int

    documents: list

    sql_query: str
    sql_results: list
    sql_error: str | None

    web_results: list
    web_error: str | None

    critique: str
    answer: str
    verification: str


def route_after_planner(state: AgentState):
    route = state.get("route")

    if route == "document":
        return "retrieve"

    if route == "sql":
        return "sql_query"

    if route == "web":
        return "web_search"

    return "abstain"


def route_after_critic(state: AgentState):
    if state.get("critique") == "SUFFICIENT":
        return "synthesizer"

    route = state.get("route")

    attempts = state.get("retrieval_attempts", 0)

    # Only internal document retrieval supports the
    # reformulation/retry loop.
    if (
        route == "document"
        and attempts < 1
    ):
        return "reformulate"

    return "abstain"


def route_after_verifier(state: AgentState):
    if state.get("verification") == "SUPPORTED":
        return END

    return "abstain"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner)
    graph.add_node("retrieve", retrieve)
    graph.add_node("sql_query", sql_query)
    graph.add_node("web_search", web_search)
    graph.add_node("critic", critic)
    graph.add_node("reformulate", reformulate)
    graph.add_node("synthesizer", synthesizer)
    graph.add_node("verifier", verifier)
    graph.add_node("abstain", abstain)

    graph.add_edge(START, "planner")

    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "retrieve": "retrieve",
            "sql_query": "sql_query",
            "web_search": "web_search",
            "abstain": "abstain",
        },
    )

    graph.add_edge("retrieve", "critic")
    graph.add_edge("sql_query", "critic")
    graph.add_edge("web_search", "critic")

    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "synthesizer": "synthesizer",
            "reformulate": "reformulate",
            "abstain": "abstain",
        },
    )

    graph.add_edge("reformulate", "retrieve")

    graph.add_edge("synthesizer", "verifier")

    graph.add_conditional_edges(
        "verifier",
        route_after_verifier,
        {
            END: END,
            "abstain": "abstain",
        },
    )

    graph.add_edge("abstain", END)

    return graph.compile()


app = build_graph()


if __name__ == "__main__":
    test_questions = [
        (
            "What was the company revenue in Q1 2026?",
            "finance",
        ),
        (
            "How many employees are in the Finance department?",
            "finance",
        ),
        (
            "What is Python?",
            "employee",
        ),
    ]

    for question, role in test_questions:
        print("\n" + "=" * 70)
        print(f"Question: {question}")
        print(f"Role: {role}")

        result = app.invoke(
            {
                "question": question,
                "user_role": role,
                "retrieval_attempts": 0,
            }
        )

        print(f"Route: {result.get('route')}")
        print(f"Critique: {result.get('critique')}")
        print(f"Verification: {result.get('verification')}")
        print(f"Answer: {result.get('answer')}")