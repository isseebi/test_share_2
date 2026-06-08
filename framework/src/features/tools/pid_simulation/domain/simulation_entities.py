from typing import List

class SimulationParameters:
    def __init__(
        self,
        kp: float,
        ki: float,
        kd: float,
        target: float = 1.0,
        steps: int = 50,
        dt: float = 0.1
    ):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.target = target
        self.steps = steps
        self.dt = dt


class SimulationResult:
    def __init__(
        self,
        time_points: List[float],
        positions: List[float],
        control_inputs: List[float],
        errors: List[float]
    ):
        self.time_points = time_points
        self.positions = positions
        self.control_inputs = control_inputs
        self.errors = errors

    def calculate_itae(self, dt: float = 0.1) -> float:
        """Integral of Time-weighted Absolute Error (ITAE)"""
        return sum(t * abs(err) for t, err in zip(self.time_points, self.errors)) * dt

    def calculate_ise(self, dt: float = 0.1) -> float:
        """Integral of Squared Error (ISE)"""
        return sum(err ** 2 for err in self.errors) * dt

    def calculate_iae(self, dt: float = 0.1) -> float:
        """Integral of Absolute Error (IAE)"""
        return sum(abs(err) for err in self.errors) * dt

    def calculate_overshoot(self, target: float) -> float:
        """Maximum overshoot value above target"""
        if not self.positions:
            return 0.0
        max_pos = max(self.positions)
        return max(0.0, max_pos - target)

    def calculate_steady_state_error(self, target: float) -> float:
        """Steady state error (absolute difference from target at the end)"""
        if not self.positions:
            return abs(target)
        return abs(target - self.positions[-1])

