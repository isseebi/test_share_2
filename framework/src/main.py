import os
import sys
import uvicorn

# --- 1. Python実行パスの調整 ---
# 'src'の親ディレクトリをPythonパスの先頭に追加し、直接実行時でもモジュールを正しく解決できるようにする
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 共有インフラ層のインポート (設定、ロガー)
from src.shared.infrastructure.config import Config
from src.shared.infrastructure.logger import get_logger

# インフラストラクチャ層の実装 (外部リソースや外部APIとの接続)
from src.features.chat.infrastructure.persistence import InMemoryChatSessionRepository  # セッション保存用
from src.features.agent_brain.infrastructure.llm_client import LLMClient                # LLM操作用
from src.features.tools.search.infrastructure.document_store import FileSystemDocumentStore  # ファイル検索用
from src.features.tools.pid_simulation.infrastructure.calculator import PhysicalPIDSimulator   # PID計算エンジン
from src.features.tools.pid_simulation.infrastructure.plot_generator import MatplotlibPlotGenerator # PIDプロット生成エンジン
from src.features.tools.pid_bayesian_optimization.infrastructure.optuna_optimizer import OptunaBayesianOptimizer  # ベイズ最適化エンジン   

# --- 新規追加ツール（P-PI制御、Web検索、ユーザーパラメータ）のインポート ---
# Web Search Tool
from src.features.tools.web_search.infrastructure.ddg_search_client import DDGSearchClient
from src.features.tools.web_search.application.web_search_use_case import ExecuteWebSearchUseCase
from src.features.tools.web_search.interface.web_search_tool import WebSearchAgentTool

# PPI Simulation Tool
from src.features.tools.ppi_simulation.infrastructure.ppi_calculator import PhysicalPPISimulator
from src.features.tools.ppi_simulation.infrastructure.ppi_plot_generator import MatplotlibPPIPlotGenerator
from src.features.tools.ppi_simulation.application.ppi_simulation_use_case import ExecutePPISimulationUseCase
from src.features.tools.ppi_simulation.interface.ppi_simulation_tool import PPISimulationAgentTool

# PPI Bayesian Optimization Tool
from src.features.tools.ppi_bayesian_optimization.infrastructure.ppi_optuna_optimizer import OptunaPPIBayesianOptimizer
from src.features.tools.ppi_bayesian_optimization.application.ppi_optimize_use_case import OptimizePPIParametersUseCase
from src.features.tools.ppi_bayesian_optimization.interface.ppi_bayesian_optimization_tool import PPIBayesianOptimizationTool

# User Parameters Retrieval Tool
from src.features.tools.user_parameters.infrastructure.user_parameters_provider import FileUserParametersProvider
from src.features.tools.user_parameters.application.user_parameters_use_case import GetUserParametersUseCase
from src.features.tools.user_parameters.interface.user_parameters_tool import UserParametersAgentTool


# アプリケーション層 / ユースケース (ビジネスロジックの定義)
from src.features.tools.search.application.search_use_case import ExecuteSearchUseCase
from src.features.tools.pid_simulation.application.simulation_use_case import ExecuteSimulationUseCase
from src.features.agent_brain.application.brain_loop import AgentThinkingLoop
from src.features.tools.pid_bayesian_optimization.application.optimize_use_case import OptimizePIDParametersUseCase

# インターフェース層 / アダプター (UIやエージェントツールへの適合)
from src.features.tools.search.interface.search_tool import SearchAgentTool
from src.features.tools.pid_simulation.interface.simulation_tool import SimulationAgentTool
from src.features.agent_brain.interface.brain_adapter import AgentBrainAdapter
from src.features.tools.pid_bayesian_optimization.interface.bayesian_optimization_tool import BayesianOptimizationTool
import src.features.chat.interface.routes as chat_routes

# ロガーの初期化
logger = get_logger("Main")

def create_app() -> FastAPI:
    """
    FastAPIアプリケーションのインスタンスを生成し、依存関係を注入するファクトリ関数
    """
    app = FastAPI(
        title="Clean Architecture AI Agent Framework",
        description="FastAPI Backend serving a Clean Architecture AI Agent with LangGraph",
        version="1.0.0"
    )

    # --- CORS設定 ---
    # ブラウザからのクロスドメインリクエストを許可する
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 1. 設定の初期化
    # 環境変数やconfigファイルから設定値を読み込む/指定モデルやポート番号など
    config = Config()

    # 2. インフラストラクチャとリポジトリの初期化
    # メモリ上のセッション保存、LLMクライアント、ドキュメントストア、物理シミュレータのインスタンス化
    session_repo = InMemoryChatSessionRepository()
    llm_client = LLMClient(config)
    doc_store = FileSystemDocumentStore(config)
    pid_simulator = PhysicalPIDSimulator()
    plot_generator = MatplotlibPlotGenerator()
    opt_tool = OptunaBayesianOptimizer()

    # 新規追加ツールのインフラ初期化
    ddg_client = DDGSearchClient()
    ppi_simulator = PhysicalPPISimulator()
    ppi_plot_generator = MatplotlibPPIPlotGenerator()
    ppi_opt_tool = OptunaPPIBayesianOptimizer()
    user_params_provider = FileUserParametersProvider()

    # 3. ユースケースの初期化
    # 具体的な処理（ドキュメント検索やシミュレーション実行）を行うクラスを準備
    search_use_case = ExecuteSearchUseCase(doc_store)
    sim_use_case = ExecuteSimulationUseCase(pid_simulator, plot_generator)
    opt_use_case = OptimizePIDParametersUseCase(opt_tool, pid_simulator)

    # 新規追加ツールのユースケース初期化
    web_search_use_case = ExecuteWebSearchUseCase(ddg_client)
    ppi_sim_use_case = ExecutePPISimulationUseCase(ppi_simulator, ppi_plot_generator)
    ppi_opt_use_case = OptimizePPIParametersUseCase(ppi_opt_tool, ppi_simulator)
    user_params_use_case = GetUserParametersUseCase(user_params_provider)

    # 4. エージェント用ツールのラッピング
    # ユースケースをエージェント（LLM）が利用可能な形式（ツール）に変換
    search_tool = SearchAgentTool(search_use_case)
    sim_tool = SimulationAgentTool(sim_use_case)
    opt_tool = BayesianOptimizationTool(opt_use_case)

    # 新規追加ツールのラッピング
    web_search_tool = WebSearchAgentTool(web_search_use_case)
    ppi_sim_tool = PPISimulationAgentTool(ppi_sim_use_case)
    ppi_opt_tool_wrapper = PPIBayesianOptimizationTool(ppi_opt_use_case)
    user_params_tool = UserParametersAgentTool(user_params_use_case)

    # 5. エージェントの思考ループ（LangGraph）の初期化
    # LLMクライアントと利用可能なツールを統合し、エージェントの推論プロセスを定義
    thinking_loop = AgentThinkingLoop(
        llm_client,
        [
            search_tool,
            sim_tool,
            opt_tool,
            web_search_tool,
            ppi_sim_tool,
            ppi_opt_tool_wrapper,
            user_params_tool
        ]
    )

    # 6. インターフェースアダプターの初期化 (依存性逆転の原則: DIP)
    # 思考ループをエージェントアダプターで包み、上位レイヤーから扱いやすくする
    brain_adapter = AgentBrainAdapter(thinking_loop)

    # 7. ルートハンドラへの依存関係注入 (Dependency Injection)
    # 手動での注入。chat_routes内のグローバル変数または特定の属性にリポジトリとアダプターをセット
    chat_routes._repository = session_repo
    chat_routes._agent_brain = brain_adapter

    # 8. ルーターの登録
    # チャット機能のエンドポイント（API）をFastAPIに登録
    app.include_router(chat_routes.router)

    # 9. 静的ファイルの配信設定
    # フロントエンド資産（HTML/CSS/JS）のパスを設定
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_dir = os.path.join(base_dir, "frontend")
    
    # フロントエンドのディレクトリ構造を確認し、必要に応じてマウント
    if os.path.exists(os.path.join(frontend_dir, "css")):
        app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
    if os.path.exists(os.path.join(frontend_dir, "js")):
        app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")

    @app.get("/")
    def serve_frontend():
        """
        ルートURLへのアクセス時にフロントエンドのindex.htmlを返却する
        """
        index_path = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"status": "Backend running, frontend/index.html not found"}

    return app

# アプリケーションの生成
app = create_app()

if __name__ == "__main__":
    # サーバー起動時の設定
    config = Config()
    logger.info(f"Starting server on {config.HOST}:{config.PORT}")
    # uvicornによるWebサーバーの起動
    uvicorn.run("src.main:app", host=config.HOST, port=config.PORT, reload=False)