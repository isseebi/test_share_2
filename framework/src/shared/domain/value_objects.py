import datetime
import uuid

class SessionId:
    def __init__(self, value: str = None):
        if value is None:
            self.value = str(uuid.uuid4())
        else:
            # Simple validation: must not be empty
            if not value.strip():
                raise ValueError("SessionId cannot be empty")
            self.value = value

    def __eq__(self, other):
        if not isinstance(other, SessionId):
            return False
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def __str__(self):
        return self.value


class Timestamp:
    def __init__(self, value: datetime.datetime = None):
        if value is None:
            self.value = datetime.datetime.now(datetime.timezone.utc)
        else:
            self.value = value

    @classmethod
    def from_iso(cls, iso_str: str):
        return cls(datetime.datetime.fromisoformat(iso_str))

    def to_iso(self) -> str:
        return self.value.isoformat()

    def __str__(self):
        return self.to_iso()
