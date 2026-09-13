import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class WebResult:
    title: str
    url: str
    snippet: str


class WebTool:
    """
    External web-search abstraction for AuditAgent.

    Uses the Tavily REST API directly so that the project does not
    depend on a rapidly changing third-party Python SDK.
    """

    TAVILY_ENDPOINT = "https://api.tavily.com/search"

    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")

    def search(self, query: str, max_results: int = 5) -> list[WebResult]:
        if not self.api_key:
            raise RuntimeError(
                "TAVILY_API_KEY is not configured. "
                "Add it to the .env file before using the web route."
            )

        if not query.strip():
            raise ValueError("Web search query cannot be empty.")

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
            "include_answer": False,
        }

        request = urllib.request.Request(
            self.TAVILY_ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                response_data = json.loads(
                    response.read().decode("utf-8")
                )

        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Tavily web search failed with HTTP {exc.code}: {error_body}"
            ) from exc

        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Unable to reach the web search provider: {exc.reason}"
            ) from exc

        results = []

        for item in response_data.get("results", []):
            results.append(
                WebResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                )
            )

        return results