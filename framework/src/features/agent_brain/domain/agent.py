from typing import Dict, Any, List, Optional

class AgentAction:
    def __init__(self, tool_name: str, tool_input: Dict[str, Any]):
        self.tool_name = tool_name
        self.tool_input = tool_input

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "tool_input": self.tool_input
        }


class AgentState:
    """
    Representation of the internal state of the agent loop.
    In LangGraph, this is modeled as a StateGraph Schema.
    """
    def __init__(
        self,
        messages: List[Dict[str, Any]],
        thinking_steps: List[Dict[str, Any]] = None,
        next_node: str = "think",
        action: Optional[AgentAction] = None,
        response: Optional[str] = None
    ):
        self.messages = messages
        self.thinking_steps = thinking_steps or []
        self.next_node = next_node
        self.action = action
        self.response = response

    def add_step(self, node_name: str, status: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.thinking_steps.append({
            "node": node_name,
            "status": status,
            "message": message,
            "details": details or {}
        })
