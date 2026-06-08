from typing import Dict, Any
from src.features.agent_brain.application.brain_loop import AgentTool
from src.features.tools.search.application.search_use_case import ExecuteSearchUseCase

class SearchAgentTool(AgentTool):
    def __init__(self, use_case: ExecuteSearchUseCase):
        self.use_case = use_case

    @property
    def name(self) -> str:
        return "search_tool"

    @property
    def description(self) -> str:
        return "Search the reference documents and specifications for ServoBot XM-430 smart servo, including operating voltage, torque, speed, and PID configurations."

    @property
    def args_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up specifications (e.g. 'voltage', 'torque')"
                }
            },
            "required": ["query"]
        }

    def execute(self, args: Dict[str, Any]) -> str:
        query = args.get("query") or ""
        return self.use_case.execute(query)

