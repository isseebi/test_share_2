from typing import List

class PPISimulationParameters:
    def __init__(
        self,
        kp: float,
        kvp: float,
        kvi: float,
        target: float = 1.0,
        steps: int = 50,
        dt: float = 0.1
    ):
        self.kp = kp
        self.kvp = kvp
        self.kvi = kvi
        self.target = target
        self.steps = steps
        self.dt = dt


class PPISimulationResult:
    def __init__(
        self,
        time_points: List[float],
        positions: List[float],
        velocities: List[float],
        target_velocities: List[float],
        control_inputs: List[float],
        errors: List[float]
    ):
        self.time_points = time_points
        self.positions = positions
        self.velocities = velocities
        self.target_velocities = target_velocities
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
        """Maximum overshoot value above target velocity"""
        if not self.velocities:
            return 0.0
        max_vel = max(self.velocities)
        return max(0.0, max_vel - target)

    def calculate_steady_state_error(self, target: float) -> float:
        """Steady state error (absolute difference from target velocity at the end)"""
        if not self.velocities:
            return abs(target)
        if self.target_velocities:
            return abs(self.target_velocities[-1] - self.velocities[-1])
        return abs(self.velocities[-1])
