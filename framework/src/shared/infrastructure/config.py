import os
from dotenv import load_dotenv

# .env ファイルから環境変数を読み込む
load_dotenv()

class Config:
    """
    アプリケーション全体の設定値を管理するクラス。
    環境変数（.env）から読み込み、デフォルト値を設定します。
    """
    # 使用するLLMプロバイダの設定 ('ollama', 'bedrock', 'claude' - ※ 'claude' は 'bedrock' として動作します)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")
    
    # Ollamaサーバーの接続先URL
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    
    # AWS Bedrockの設定
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-northeast-1")
    BEDROCK_MODEL_ID: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_SESSION_TOKEN: str = os.getenv("AWS_SESSION_TOKEN", "")
    
    # FastAPIバックエンドサーバーがバインドするポート番号
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # FastAPIバックエンドサーバーがバインドするホスト名
    HOST: str = os.getenv("HOST", "127.0.0.1")
    
    # RAG検索対象となるドキュメントが保存されているディレクトリパス
    DOCS_DIR: str = os.getenv("DOCS_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "docs"))
