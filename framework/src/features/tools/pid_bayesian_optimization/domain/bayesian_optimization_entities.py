from abc import ABC, abstractmethod
from typing import List, Any, Protocol

class OptimizationBounds:
    def __init__(
        self,
        kp_min: float = 0.0,
        kp_max: float = 10.0,
        ki_min: float = 0.0,
        ki_max: float = 10.0,
        kd_min: float = 0.0,
        kd_max: float = 10.0
    ):
        self.kp_min = kp_min
        self.kp_max = kp_max
        self.ki_min = ki_min
        self.ki_max = ki_max
        self.kd_min = kd_min
        self.kd_max = kd_max


class OptimizationConfig:
    def __init__(
        self,
        bounds: OptimizationBounds,
        n_trials: int = 50,
        target: float = 1.0,
        steps: int = 50,
        dt: float = 0.1,
        weight_itae: float = 1.0,
        weight_overshoot: float = 2.0,
        weight_steady_state: float = 5.0
    ):
        self.bounds = bounds
        self.n_trials = n_trials
        self.target = target
        self.steps = steps
        self.dt = dt
        self.weight_itae = weight_itae
        self.weight_overshoot = weight_overshoot
        self.weight_steady_state = weight_steady_state


class OptimizationTrial:
    def __init__(
        self,
        number: int,
        kp: float,
        ki: float,
        kd: float,
        score: float
    ):
        self.number = number
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.score = score


class OptimizationResult:
    def __init__(
        self,
        best_kp: float,
        best_ki: float,
        best_kd: float,
        best_score: float,
        trials: List[OptimizationTrial]
    ):
        self.best_kp = best_kp
        self.best_ki = best_ki
        self.best_kd = best_kd
        self.best_score = best_score
        self.trials = trials


class SimulatorLike(Protocol):
    """
    Protocol to represent any simulator that can run simulation.
    This avoids importing SimulatorService from simulation.application,
    thus respecting the Domain layer boundary rules.
    """
    def run_simulation(self, params: Any) -> Any:
        ...


class BayesianOptimizerService(ABC):
    @abstractmethod
    def optimize(
        self,
        config: OptimizationConfig,
        simulator: SimulatorLike
    ) -> OptimizationResult:
        pass
