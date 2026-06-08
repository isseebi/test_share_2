import json
from abc import ABC, abstractmethod
from src.features.tools.pid_simulation.domain.simulation_entities import SimulationParameters, SimulationResult

# Port / Interface
class SimulatorService(ABC):
    @abstractmethod
    def run_simulation(self, params: SimulationParameters) -> SimulationResult:
        pass


class PlotGeneratorService(ABC):
    @abstractmethod
    def generate_plot(self, time_points: list, positions: list, target: float) -> str:
        """
        Generate a waveform plot and return it as a Base64-encoded PNG data URL.
        """
        pass


class ExecuteSimulationUseCase:
    def __init__(self, simulator: SimulatorService, plot_generator: PlotGeneratorService):
        self.simulator = simulator
        self.plot_generator = plot_generator

    def execute(self, kp: float, ki: float, kd: float, steps: int = 50) -> str:
        params = SimulationParameters(kp=kp, ki=ki, kd=kd, steps=steps)
        result = self.simulator.run_simulation(params)

        # Calculate metrics
        final_pos = result.positions[-1]
        target = params.target
        ss_error = abs(target - final_pos)
        
        # Check overshoot
        max_pos = max(result.positions)
        overshoot = max(0.0, max_pos - target)
        overshoot_pct = (overshoot / target) * 100 if target != 0 else 0

        # Simple ASCII plot
        # Let's generate a 10-line text plot of the position
        plot_lines = []
        width = 40
        min_p = min(0.0, min(result.positions))
        max_p = max(target * 1.2, max(result.positions))
        span = max_p - min_p if (max_p - min_p) > 0 else 1.0

        for step_idx in range(0, len(result.positions), max(1, len(result.positions) // 15)):
            pos = result.positions[step_idx]
            t = result.time_points[step_idx]
            
            # Position character index
            pos_idx = int(((pos - min_p) / span) * (width - 1))
            pos_idx = max(0, min(width - 1, pos_idx))
            
            # Target line character index
            tgt_idx = int(((target - min_p) / span) * (width - 1))
            tgt_idx = max(0, min(width - 1, tgt_idx))

            line_chars = [" "] * width
            line_chars[tgt_idx] = "|"
            line_chars[pos_idx] = "*"
            
            line_str = "".join(line_chars)
            plot_lines.append(f"t={t:4.1f}s: {line_str} (pos: {pos:.3f})")

        ascii_chart = "\n".join(plot_lines)

        # Generate the Base64 image of the plot
        image_base64 = self.plot_generator.generate_plot(
            time_points=result.time_points,
            positions=result.positions,
            target=target
        )

        # Prepare JSON string output so downstream steps can extract structured coordinates
        structured_data = {
            "image": image_base64,
            "metrics": {
                "steady_state_error": ss_error,
                "overshoot_percentage": overshoot_pct,
                "max_value": max_pos
            }
        }

        summary = (
            f"PID Simulation completed (Kp={kp:.2f}, Ki={ki:.2f}, Kd={kd:.2f})\n"
            f"--------------------------------------------------\n"
            f"Target Position: {target:.2f}\n"
            f"Final Position: {final_pos:.4f}\n"
            f"Steady-State Error: {ss_error:.4f}\n"
            f"Max Overshoot: {overshoot:.4f} ({overshoot_pct:.1f}%)\n"
            f"--------------------------------------------------\n"
            f"Visual Profile (* = Position, | = Target):\n"
            f"{ascii_chart}\n"
            f"--------------------------------------------------\n"
            f"STRUCTURED_DATA_JSON_START\n"
            f"{json.dumps(structured_data)}\n"
            f"STRUCTURED_DATA_JSON_END"
        )
        return summary
