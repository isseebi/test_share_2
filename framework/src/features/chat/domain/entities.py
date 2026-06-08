from typing import List, Dict, Any
from src.shared.domain.value_objects import SessionId, Timestamp

class Message:
    def __init__(self, role: str, content: str, timestamp: Timestamp = None):
        if role not in ["user", "assistant", "system"]:
            raise ValueError(f"Invalid message role: {role}")
        if not content.strip():
            raise ValueError("Message content cannot be empty")
        self.role = role
        self.content = content
        self.timestamp = timestamp or Timestamp()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.to_iso()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=Timestamp.from_iso(data["timestamp"])
        )


class ChatSession:
    def __init__(self, session_id: SessionId = None, messages: List[Message] = None):
        self.session_id = session_id or SessionId()
        self.messages = messages or []

    def add_message(self, message: Message):
        self.messages.append(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": str(self.session_id),
            "messages": [msg.to_dict() for msg in self.messages]
        }
