import os
import json
from src.features.tools.user_parameters.domain.user_parameters_entities import UserSystemParameters
from src.features.tools.user_parameters.application.user_parameters_use_case import UserParametersProvider

class FileUserParametersProvider(UserParametersProvider):
    def __init__(self, filepath: str = "user_parameters.json"):
        self.filepath = filepath

    def get_parameters(self) -> UserSystemParameters:
        """
        Load custom controller parameters from the workspace configuration file.
        Generates a default setup if the file does not exist.
        """
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return UserSystemParameters(
                        system_name=data.get("system_name", "Dynamixel XM430-W350 Custom Load"),
                        kp=float(data.get("kp", 2.2)),
                        kvp=float(data.get("kvp", 1.5)),
                        kvi=float(data.get("kvi", 0.6)),
                        notes=data.get("notes", "No notes available.")
                    )
            except Exception:
                pass

        # Fallback values if the file is missing or corrupted
        default_params = UserSystemParameters(
            system_name="Dynamixel XM430-W350 Default Load System",
            kp=2.5,
            kvp=1.8,
            kvi=0.6,
            notes="Factory recommended default cascaded P-PI configuration for stable position control under moderate external loads."
        )

        # Create the file automatically for ease of maintenance
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "system_name": default_params.system_name,
                    "kp": default_params.kp,
                    "kvp": default_params.kvp,
                    "kvi": default_params.kvi,
                    "notes": default_params.notes
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return default_params
