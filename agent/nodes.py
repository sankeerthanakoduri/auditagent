import os
from typing import Any

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from retrieval.hybrid import HybridRetriever

from agent.prompts import (
    PLANNER_PROMPT,
    CRITIC_PROMPT,
    SYNTHESIZER_PROMPT,
    VERIFIER_PROMPT,
)


load_dotenv()


class AuditAgentNodes:
    """
    Node implementations used by the AuditAgent LangGraph workflow.
    """

    def __init__(self):
        groq_api_key = os.getenv("GROQ_API_KEY")

        if not groq_api_key:
            raise RuntimeError(
                "GROQ_API_KEY was not found. "
                "Make sure it is present in the project's .env file."
            )

        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0,
            api_key=groq_api_key,
        )

        self.retriever = HybridRetriever()

    def planner(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Determine which data source should handle the question.
        """

        question = state["question"]

        prompt = PLANNER_PROMPT.format(
            question=question
        )

        response = self.llm.invoke(prompt)

        route = response.content.strip().lower()

        if route != "document":
            route = "document"

        return {
            "route": route
        }

    def retrieve(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Retrieve documents using the existing secure hybrid retriever.
        """

        question = state["question"]
        user_role = state["user_role"]

        documents = self.retriever.search(
            query=question,
            user_role=user_role,
        )

        return {
            "documents": documents
        }

    def critic(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Determine whether retrieved evidence is sufficient.
        """

        question = state["question"]
        documents = state.get("documents", [])

        evidence = "\n\n".join(
            document.document.text
            for document in documents
        )

        if not evidence:
            return {
                "critique": "INSUFFICIENT"
            }

        prompt = CRITIC_PROMPT.format(
            question=question,
            evidence=evidence,
        )

        response = self.llm.invoke(prompt)

        critique = response.content.strip().upper()

        if "SUFFICIENT" in critique:
            critique = "SUFFICIENT"
        else:
            critique = "INSUFFICIENT"

        return {
            "critique": critique
        }

    def synthesizer(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Generate an answer using authorized retrieved evidence.
        """

        question = state["question"]
        documents = state.get("documents", [])

        evidence = "\n\n".join(
            document.document.text
            for document in documents
        )

        if not evidence:
            return {
                "answer": (
                    "I could not find sufficient authorized information "
                    "to answer this question."
                )
            }

        prompt = SYNTHESIZER_PROMPT.format(
            question=question,
            evidence=evidence,
        )

        response = self.llm.invoke(prompt)

        return {
            "answer": response.content.strip()
        }

    def verifier(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Verify that the generated answer is supported by evidence.
        """

        question = state["question"]
        answer = state.get("answer", "")
        documents = state.get("documents", [])

        evidence = "\n\n".join(
            document.document.text
            for document in documents
        )

        if not answer or not evidence:
            return {
                "verification": "UNSUPPORTED"
            }

        prompt = VERIFIER_PROMPT.format(
            question=question,
            evidence=evidence,
            answer=answer,
        )

        response = self.llm.invoke(prompt)

        verification = response.content.strip().upper()

        if "SUPPORTED" in verification:
            verification = "SUPPORTED"
        else:
            verification = "UNSUPPORTED"

        return {
            "verification": verification
        }

    def abstain(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Return a safe response when evidence is insufficient.
        """

        return {
            "answer": (
                "I cannot provide a reliable answer because the "
                "available authorized documents do not contain "
                "sufficient supporting evidence."
            )
        }