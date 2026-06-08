import json
from typing import Dict, Any
from src.features.agent_brain.application.brain_loop import AgentTool
from src.features.tools.pid_bayesian_optimization.domain.bayesian_optimization_entities import (
    OptimizationBounds,
    OptimizationConfig
)
from src.features.tools.pid_bayesian_optimization.application.optimize_use_case import OptimizePIDParametersUseCase

class BayesianOptimizationTool(AgentTool):
    """
    Interface adapter for executing and presenting PID parameter optimization results.
    """
    def __init__(self, use_case: OptimizePIDParametersUseCase):
        self.use_case = use_case

    @property
    def name(self) -> str:
        return "bayesian_optimization_tool"

    @property
    def description(self) -> str:
        return "Perform Bayesian Optimization (hyperparameter tuning) for a PID controller using the physical DC motor simulator to find optimal gains (Kp, Ki, Kd)."

    @property
    def args_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "kp_min": {"type": "number", "description": "Minimum value for Kp"},
                "kp_max": {"type": "number", "description": "Maximum value for Kp"},
                "ki_min": {"type": "number", "description": "Minimum value for Ki"},
                "ki_max": {"type": "number", "description": "Maximum value for Ki"},
                "kd_min": {"type": "number", "description": "Minimum value for Kd"},
                "kd_max": {"type": "number", "description": "Maximum value for Kd"},
                "n_trials": {"type": "integer", "description": "Number of optimization trials (default: 30)"}
            }
        }

    def execute(self, args: Dict[str, Any]) -> str:
        return self.run_optimization(args)

    def run_optimization(self, args: Dict[str, Any]) -> str:
        """
        Execute optimization using bounds and configuration provided in arguments,
        returning a formatted summary.
        """
        # Parse search bounds (use defaults if not provided)
        bounds = OptimizationBounds(
            kp_min=float(args.get("kp_min", 0.0)),
            kp_max=float(args.get("kp_max", 10.0)),
            ki_min=float(args.get("ki_min", 0.0)),
            ki_max=float(args.get("ki_max", 10.0)),
            kd_min=float(args.get("kd_min", 0.0)),
            kd_max=float(args.get("kd_max", 5.0))
        )

        # Parse config
        config = OptimizationConfig(
            bounds=bounds,
            n_trials=int(args.get("n_trials", 30)),
            target=float(args.get("target", 1.0)),
            steps=int(args.get("steps", 50)),
            dt=float(args.get("dt", 0.1)),
            weight_itae=float(args.get("weight_itae", 1.0)),
            weight_overshoot=float(args.get("weight_overshoot", 2.0)),
            weight_steady_state=float(args.get("weight_steady_state", 5.0))
        )

        # Run
        result = self.use_case.execute(config)

        # Build detailed trials log for visualization/debugging
        trials_data = []
        for t in result.trials:
            trials_data.append({
                "trial": t.number,
                "kp": t.kp,
                "ki": t.ki,
                "kd": t.kd,
                "score": t.score
            })

        structured_result = {
            "best_params": {
                "kp": result.best_kp,
                "ki": result.best_ki,
                "kd": result.best_kd
            },
            "best_score": result.best_score,
            "trials_history": trials_data
        }

        # Format output
        summary = (
            f"PID Parameter Optimization Completed\n"
            f"--------------------------------------------------\n"
            f"Best Kp: {result.best_kp:.4f}\n"
            f"Best Ki: {result.best_ki:.4f}\n"
            f"Best Kd: {result.best_kd:.4f}\n"
            f"Best Score (Objective Loss): {result.best_score:.4f}\n"
            f"Total Trials: {len(result.trials)}\n"
            f"--------------------------------------------------\n"
            f"STRUCTURED_DATA_JSON_START\n"
            f"{json.dumps(structured_result)}\n"
            f"STRUCTURED_DATA_JSON_END"
        )
        return summary
