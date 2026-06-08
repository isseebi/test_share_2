class SearchResult:
    def __init__(self, document_name: str, content: str, score: float):
        self.document_name = document_name
        self.content = content
        self.score = score

    def to_dict(self) -> dict:
        return {
            "document_name": self.document_name,
            "content": self.content,
            "score": self.score
        }
