import json
from abc import ABC, abstractmethod
from src.features.tools.user_parameters.domain.user_parameters_entities import UserSystemParameters

class UserParametersProvider(ABC):
    @abstractmethod
    def get_parameters(self) -> UserSystemParameters:
        pass


class GetUserParametersUseCase:
    def __init__(self, provider: UserParametersProvider):
        self.provider = provider

    def execute(self) -> str:
        params = self.provider.get_parameters()
        
        # Generate the natural language description/explanation inside the JSON as requested
        explanation = (
            f"現在のシステムのPPI制御パラメータ設定：対象システムは「{params.system_name}」です。"
            f"位置比例ゲイン(Kp)は {params.kp:.2f}、速度比例ゲイン(Kvp)は {params.kvp:.2f}、速度積分ゲイン(Kvi)は {params.kvi:.2f} に設定されています。"
            f"調整ノート: {params.notes}"
        )
        
        response_data = {
            "status": "success",
            "system_name": params.system_name,
            "parameters": {
                "kp": params.kp,
                "kvp": params.kvp,
                "kvi": params.kvi
            },
            "description": explanation
        }
        
        return json.dumps(response_data, ensure_ascii=False, indent=2)
