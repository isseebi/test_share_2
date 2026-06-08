import os
from typing import List
from src.features.tools.search.domain.search_entities import SearchResult
from src.features.tools.search.application.search_use_case import DocumentStore
from src.shared.infrastructure.config import Config

class FileSystemDocumentStore(DocumentStore):
    """
    ローカルファイルシステム上の Markdown 形式の設計資料を検索する RAG 用のドキュメントストア。
    """
    def __init__(self, config: Config):
        self.docs_dir = config.DOCS_DIR

    def search(self, query: str) -> List[SearchResult]:
        """
        簡易的なキーワードベースのドキュメント検索を実行します。
        
        検索手順:
        1. クエリを単語ごとに分割し、小文字化します。
        2. ドキュメントフォルダ（docs/）内のすべての .md ファイルをスキャンします。
        3. ファイル内容を段落（改行2つ）でセクションに分割します。
        4. 各セクション内のキーワード含有度（スコア）を算出してランキングします。
        """
        if not os.path.exists(self.docs_dir):
            return []

        # クエリ文字列をスペースで区切り、2文字以上の語を検索用キーワードとしてリスト化
        query_terms = [term.lower() for term in query.split() if len(term) > 1]
        if not query_terms:
            query_terms = [query.lower()]

        results = []
        for filename in os.listdir(self.docs_dir):
            if not filename.endswith(".md"):
                continue
            
            filepath = os.path.join(self.docs_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # 段落（\n\n）単位でコンテンツをセクション分割（簡易チャンキング）
                sections = content.split("\n\n")
                for sec in sections:
                    sec_clean = sec.strip()
                    if not sec_clean:
                        continue
                    
                    # キーワードマッチ度に基づく簡易スコアリング
                    sec_lower = sec_clean.lower()
                    matches = sum(1 for term in query_terms if term in sec_lower)
                    if matches > 0:
                        score = matches / len(query_terms)
                        results.append(SearchResult(
                            document_name=filename,
                            content=sec_clean,
                            score=score
                        ))
            except Exception:
                # 読み込みエラーが発生したファイルは無視して次に進む
                continue

        # スコアの高い順（降順）にソートして、上位5件のセグメントを返却
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:5]
