from typing import Any, TypedDict

from langgraph.graph import StateGraph, START, END

from agent.nodes import AuditAgentNodes


class AuditAgentState(TypedDict, total=False):
    question: str
    user_role: str

    route: str

    documents: list[Any]

    critique: str
    answer: str
    verification: str

    retrieval_attempts: int


def build_graph():
    """
    Build the AuditAgent LangGraph workflow.
    """

    nodes = AuditAgentNodes()

    graph = StateGraph(AuditAgentState)

    graph.add_node(
        "planner",
        nodes.planner,
    )

    graph.add_node(
        "retrieve",
        nodes.retrieve,
    )

    graph.add_node(
        "critic",
        nodes.critic,
    )

    graph.add_node(
        "synthesizer",
        nodes.synthesizer,
    )

    graph.add_node(
        "verifier",
        nodes.verifier,
    )

    graph.add_node(
        "abstain",
        nodes.abstain,
    )

    graph.add_edge(
        START,
        "planner",
    )

    graph.add_edge(
        "planner",
        "retrieve",
    )

    graph.add_edge(
        "retrieve",
        "critic",
    )

    graph.add_conditional_edges(
        "critic",
        critic_router,
        {
            "sufficient": "synthesizer",
            "insufficient": "abstain",
        },
    )

    graph.add_edge(
        "synthesizer",
        "verifier",
    )

    graph.add_conditional_edges(
        "verifier",
        verifier_router,
        {
            "supported": END,
            "unsupported": "abstain",
        },
    )

    graph.add_edge(
        "abstain",
        END,
    )

    return graph.compile()


def critic_router(state: AuditAgentState) -> str:
    """
    Decide whether retrieved evidence is sufficient.
    """

    if state.get("critique") == "SUFFICIENT":
        return "sufficient"

    return "insufficient"


def verifier_router(state: AuditAgentState) -> str:
    """
    Decide whether the generated answer is supported.
    """

    if state.get("verification") == "SUPPORTED":
        return "supported"

    return "unsupported"


if __name__ == "__main__":

    app = build_graph()

    result = app.invoke(
        {
            "question": "What was the company revenue in Q1 2026?",
            "user_role": "finance",
            "retrieval_attempts": 0,
        }
    )

    print("\n" + "=" * 60)
    print("AUDITAGENT LANGGRAPH TEST")
    print("=" * 60)

    print("\nQuestion:")
    print(result["question"])

    print("\nRole:")
    print(result["user_role"])

    print("\nRoute:")
    print(result.get("route"))

    print("\nCritique:")
    print(result.get("critique"))

    print("\nVerification:")
    print(result.get("verification"))

    print("\nAnswer:")
    print(result.get("answer"))

    print("=" * 60)