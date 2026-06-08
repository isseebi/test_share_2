import json
import pytest
from src.features.tools.simulation.infrastructure.calculator import PhysicalPIDSimulator
from src.features.tools.bayesian_optimization.infrastructure.optuna_optimizer import OptunaBayesianOptimizer
from src.features.tools.bayesian_optimization.application.optimize_use_case import OptimizePIDParametersUseCase
from src.features.tools.bayesian_optimization.domain.bayesian_optimization_entities import (
    OptimizationBounds,
    OptimizationConfig
)
from src.features.tools.bayesian_optimization.interface.bayesian_optimization_tool import BayesianOptimizationTool

def test_bayesian_optimization_flow():
    """Verify that Bayesian Optimization runs and finds sub-optimal parameters that improve the PID response."""
    simulator = PhysicalPIDSimulator()
    optimizer = OptunaBayesianOptimizer()
    use_case = OptimizePIDParametersUseCase(optimizer, simulator)

    # Set optimization parameters
    bounds = OptimizationBounds(
        kp_min=1.0, kp_max=5.0,
        ki_min=0.0, ki_max=2.0,
        kd_min=0.0, kd_max=1.0
    )
    config = OptimizationConfig(
        bounds=bounds,
        n_trials=20,
        target=1.0,
        steps=30,
        dt=0.1
    )

    # Execute
    result = use_case.execute(config)

    # Assertions
    assert result.best_kp >= bounds.kp_min and result.best_kp <= bounds.kp_max
    assert result.best_ki >= bounds.ki_min and result.best_ki <= bounds.ki_max
    assert result.best_kd >= bounds.kd_min and result.best_kd <= bounds.kd_max
    assert result.best_score > 0.0
    assert len(result.trials) == 20

    # Test the interface tool wrapper
    tool = BayesianOptimizationTool(use_case)
    tool_args = {
        "kp_min": 1.0, "kp_max": 5.0,
        "ki_min": 0.0, "ki_max": 2.0,
        "kd_min": 0.0, "kd_max": 1.0,
        "n_trials": 15,
        "steps": 30
    }
    tool_output = tool.run_optimization(tool_args)

    assert "PID Parameter Optimization Completed" in tool_output
    assert "STRUCTURED_DATA_JSON_START" in tool_output
    
    # Parse and verify the JSON output
    json_part = tool_output.split("STRUCTURED_DATA_JSON_START")[1].split("STRUCTURED_DATA_JSON_END")[0].strip()
    data = json.loads(json_part)
    
    assert "best_params" in data
    assert "kp" in data["best_params"]
    assert len(data["trials_history"]) == 15
