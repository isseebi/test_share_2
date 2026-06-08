from src.features.tools.pid_bayesian_optimization.domain.bayesian_optimization_entities import (
    OptimizationConfig,
    OptimizationResult,
    BayesianOptimizerService
)
from src.features.tools.pid_simulation.application.simulation_use_case import SimulatorService

class OptimizePIDParametersUseCase:
    def __init__(
        self,
        optimizer: BayesianOptimizerService,
        simulator: SimulatorService
    ):
        self.optimizer = optimizer
        self.simulator = simulator

    def execute(self, config: OptimizationConfig) -> OptimizationResult:
        """
        Run the Bayesian Optimization process to find optimal Kp, Ki, Kd parameters.
        """
        return self.optimizer.optimize(config, self.simulator)
