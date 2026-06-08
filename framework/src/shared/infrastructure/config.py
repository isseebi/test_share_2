import os
from dotenv import load_dotenv

# .env ファイルから環境変数を読み込む
load_dotenv()

class Config:
    """
    アプリケーション全体の設定値を管理するクラス。
    環境変数（.env）から読み込み、デフォルト値を設定します。
    """
    # 使用するLLMプロバイダの設定 ('mock', 'ollama', 'claude')
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")
    
    # Ollamaサーバーの接続先URL
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    
    # Anthropic Claude APIのアクセスキー
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    
    # FastAPIバックエンドサーバーがバインドするポート番号
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # FastAPIバックエンドサーバーがバインドするホスト名
    HOST: str = os.getenv("HOST", "127.0.0.1")
    
    # RAG検索対象となるドキュメントが保存されているディレクトリパス
    DOCS_DIR: str = os.getenv("DOCS_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "docs"))
