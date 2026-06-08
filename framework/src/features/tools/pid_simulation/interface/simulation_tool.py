from typing import Dict, Any
from src.features.agent_brain.application.brain_loop import AgentTool
from src.features.tools.pid_simulation.application.simulation_use_case import ExecuteSimulationUseCase

class SimulationAgentTool(AgentTool):
    def __init__(self, use_case: ExecuteSimulationUseCase):
        self.use_case = use_case

    @property
    def name(self) -> str:
        return "simulation_tool"

    @property
    def description(self) -> str:
        return "Run a discrete-time physical numerical simulation of a DC motor with a PID controller to evaluate position, control inputs, errors, steady state error, and overshoot percentage."

    @property
    def args_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "kp": {
                    "type": "number",
                    "description": "Proportional gain of the PID controller"
                },
                "ki": {
                    "type": "number",
                    "description": "Integral gain of the PID controller"
                },
                "kd": {
                    "type": "number",
                    "description": "Derivative gain of the PID controller"
                },
                "steps": {
                    "type": "integer",
                    "description": "Number of simulation steps (default: 50)"
                }
            },
            "required": ["kp", "ki", "kd"]
        }

    def execute(self, args: Dict[str, Any]) -> str:
        kp = float(args.get("kp", 1.0))
        ki = float(args.get("ki", 0.0))
        kd = float(args.get("kd", 0.0))
        steps = int(args.get("steps", 50))
        return self.use_case.execute(kp=kp, ki=ki, kd=kd, steps=steps)

