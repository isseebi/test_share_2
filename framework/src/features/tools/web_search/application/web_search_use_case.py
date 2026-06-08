from abc import ABC, abstractmethod
from typing import List
from src.features.tools.web_search.domain.web_search_entities import WebSearchResult

class WebSearchClient(ABC):
    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[WebSearchResult]:
        pass


class ExecuteWebSearchUseCase:
    def __init__(self, client: WebSearchClient):
        self.client = client

    def execute(self, query: str, max_results: int = 5) -> str:
        if not query.strip():
            return "Empty search query provided."

        try:
            results = self.client.search(query, max_results=max_results)
        except Exception as e:
            return f"Failed to execute web search: {str(e)}"

        if not results:
            return f"No web search results found for query: '{query}'"

        output = [f"DuckDuckGo search results for: '{query}'"]
        for i, res in enumerate(results, 1):
            output.append(
                f"\n[{i}] {res.title}\nURL: {res.href}\nSnippet: {res.body}"
            )
        return "\n".join(output)
