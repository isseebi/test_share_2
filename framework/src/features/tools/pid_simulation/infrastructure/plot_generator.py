import io
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from src.features.tools.pid_simulation.application.simulation_use_case import PlotGeneratorService

class MatplotlibPlotGenerator(PlotGeneratorService):
    def generate_plot(self, time_points: list, positions: list, target: float) -> str:
        """
        Generate a waveform plot using matplotlib and return it as a Base64-encoded PNG data URL.
        """
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(6, 3.5), dpi=150)
        
        # Style to match dark UI theme
        fig.patch.set_facecolor('#0e0d22')
        ax.set_facecolor('#0e0d22')
        
        # Plot curves
        ax.plot(time_points, positions, color='#00f0ff', label='Position (theta)', linewidth=2)
        ax.axhline(y=target, color='#ff007f', linestyle='--', label='Target', linewidth=1.5)
        
        # Title and Labels
        ax.set_title('PID Step Response Curve', color='white', fontsize=12, pad=10, fontweight='bold')
        ax.set_xlabel('Time (seconds)', color='#a0a0c0', fontsize=10)
        ax.set_ylabel('Position', color='#a0a0c0', fontsize=10)
        
        # Grid lines (very subtle)
        ax.grid(True, color=(1.0, 1.0, 1.0, 0.07), linestyle=':')
        
        # Legend styling
        ax.legend(facecolor='#1e1d3e', edgecolor='none', labelcolor='white', loc='lower right')
        
        # Tick parameters and spines styling
        ax.tick_params(colors='#a0a0c0', which='both')
        for spine in ax.spines.values():
            spine.set_color('#1e1d3e')
            
        plt.tight_layout()
        
        # Save to a BytesIO buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        
        # Convert buffer contents to base64
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"
