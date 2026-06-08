from abc import ABC, abstractmethod
from typing import List
from src.features.tools.search.domain.search_entities import SearchResult

# Port / Interface for DB/File operations
class DocumentStore(ABC):
    @abstractmethod
    def search(self, query: str) -> List[SearchResult]:
        pass


class ExecuteSearchUseCase:
    def __init__(self, store: DocumentStore):
        self.store = store

    def execute(self, query: str) -> str:
        if not query.strip():
            return "Empty search query provided."

        results = self.store.search(query)
        if not results:
            return f"No documentation found matching query: '{query}'"

        # Format results nicely for LLM consumption
        output = [f"Found {len(results)} relevant documents/sections:"]
        for i, res in enumerate(results, 1):
            output.append(
                f"\n[{i}] Document: {res.document_name} (Score: {res.score:.2f})\nContent snippet:\n{res.content}"
            )
        return "\n".join(output)
