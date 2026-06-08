from typing import List
from duckduckgo_search import DDGS
from src.features.tools.web_search.domain.web_search_entities import WebSearchResult
from src.features.tools.web_search.application.web_search_use_case import WebSearchClient

class DDGSearchClient(WebSearchClient):
    def search(self, query: str, max_results: int = 5) -> List[WebSearchResult]:
        results = []
        try:
            # DuckDuckGoを使用したWeb検索のみを実行
            with DDGS() as ddgs:
                ddg_results = ddgs.text(query, max_results=max_results)
                if ddg_results:
                    for r in ddg_results:
                        results.append(WebSearchResult(
                            title=r.get("title", "No Title"),
                            href=r.get("href", ""),
                            body=r.get("body", "")
                        ))
        except Exception:
            # ネットワークエラーやレートリミット等の場合は例外をキャッチして空のまま返す
            pass

        return results