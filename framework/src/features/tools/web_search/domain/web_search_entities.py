class WebSearchResult:
    def __init__(self, title: str, href: str, body: str):
        self.title = title
        self.href = href
        self.body = body

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "href": self.href,
            "body": self.body
        }
