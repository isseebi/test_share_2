from typing import Dict, Any
from src.features.agent_brain.application.brain_loop import AgentTool
from src.features.tools.web_search.application.web_search_use_case import ExecuteWebSearchUseCase

class WebSearchAgentTool(AgentTool):
    def __init__(self, use_case: ExecuteWebSearchUseCase):
        self.use_case = use_case

    @property
    def name(self) -> str:
        return "web_search_tool"

    @property
    def description(self) -> str:
        return "Search the live web using DuckDuckGo to find up-to-date specifications, documentation, datasheets, or general details about motor controllers, servo motors, or PPI/PID architectures."

    @property
    def args_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up (e.g., 'Dynamixel XM430-W350 stall torque')"
                }
            },
            "required": ["query"]
        }

    def execute(self, args: Dict[str, Any]) -> str:
        query = args.get("query") or ""
        return self.use_case.execute(query)
