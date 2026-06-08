import json
from typing import Dict, Any
from src.features.agent_brain.application.brain_loop import AgentTool
from src.features.tools.ppi_bayesian_optimization.domain.ppi_bayesian_optimization_entities import (
    PPIOptimizationBounds,
    PPIOptimizationConfig
)
from src.features.tools.ppi_bayesian_optimization.application.ppi_optimize_use_case import OptimizePPIParametersUseCase

class PPIBayesianOptimizationTool(AgentTool):
    """
    Interface adapter for executing and presenting P-PI parameter optimization results.
    """
    def __init__(self, use_case: OptimizePPIParametersUseCase):
        self.use_case = use_case

    @property
    def name(self) -> str:
        return "ppi_bayesian_optimization_tool"

    @property
    def description(self) -> str:
        return "Perform Bayesian Optimization (hyperparameter tuning) for a cascaded P-PI motor controller (position outer P, velocity inner PI) using the physical motor simulator to find optimal gains (Kp, Kvp, Kvi)."

    @property
    def args_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "kp_min": {"type": "number", "description": "Minimum value for Kp"},
                "kp_max": {"type": "number", "description": "Maximum value for Kp"},
                "kvp_min": {"type": "number", "description": "Minimum value for Kvp"},
                "kvp_max": {"type": "number", "description": "Maximum value for Kvp"},
                "kvi_min": {"type": "number", "description": "Minimum value for Kvi"},
                "kvi_max": {"type": "number", "description": "Maximum value for Kvi"},
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
        bounds = PPIOptimizationBounds(
            kp_min=float(args.get("kp_min", 0.0)),
            kp_max=float(args.get("kp_max", 10.0)),
            kvp_min=float(args.get("kvp_min", 0.0)),
            kvp_max=float(args.get("kvp_max", 10.0)),
            kvi_min=float(args.get("kvi_min", 0.0)),
            kvi_max=float(args.get("kvi_max", 10.0))
        )

        # Parse config
        config = PPIOptimizationConfig(
            bounds=bounds,
            n_trials=int(args.get("n_trials", 30)),
            target=float(args.get("target", 1.0)),
            steps=int(args.get("steps", 50)),
            dt=float(args.get("dt", 0.1)),
            weight_itae=float(args.get("weight_itae", 1.0)),
            weight_overshoot=float(args.get("weight_overshoot", 2.0)),
            weight_steady_state=float(args.get("weight_steady_state", 5.0))
        )

        # Run optimization
        result = self.use_case.execute(config)

        # Build detailed trials log for visualization/debugging
        trials_data = []
        for t in result.trials:
            trials_data.append({
                "trial": t.number,
                "kp": t.kp,
                "kvp": t.kvp,
                "kvi": t.kvi,
                "score": t.score
            })

        structured_result = {
            "best_params": {
                "kp": result.best_kp,
                "kvp": result.best_kvp,
                "kvi": result.best_kvi
            },
            "best_score": result.best_score,
            "trials_history": trials_data
        }

        # Format output
        summary = (
            f"PPI Parameter Optimization Completed\n"
            f"--------------------------------------------------\n"
            f"Best Kp: {result.best_kp:.4f}\n"
            f"Best Kvp: {result.best_kvp:.4f}\n"
            f"Best Kvi: {result.best_kvi:.4f}\n"
            f"Best Score (Objective Loss): {result.best_score:.4f}\n"
            f"Total Trials: {len(result.trials)}\n"
            f"--------------------------------------------------\n"
            f"STRUCTURED_DATA_JSON_START\n"
            f"{json.dumps(structured_result)}\n"
            f"STRUCTURED_DATA_JSON_END"
        )
        return summary
