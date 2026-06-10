from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# アプリケーション層（ユースケースやリポジトリのインターフェース）のインポート
from src.features.chat.application.use_cases import (
    SendMessageUseCase,
    SendMessageInputDTO,
    GetSessionsUseCase,
    ChatSessionRepository,
    AgentBrainService
)
from src.shared.domain.value_objects import SessionId

# --- Pydantic Schemas (バリデーションおよびレスポンス定義) ---

class MessageRequest(BaseModel):
    """クライアントからのメッセージ送信リクエスト"""
    content: str = Field("", description="Message content")
    image: Optional[str] = Field(None, description="Base64 encoded image or image URL")

class MessageResponse(BaseModel):
    """個別のメッセージ内容のレスポンス"""
    role: str
    content: str
    timestamp: str
    image: Optional[str] = None

class SendMessageResponse(BaseModel):
    """メッセージ送信後の全体レスポンス（思考プロセス等を含む）"""
    session_id: str
    response_content: str
    thinking_steps: List[Dict[str, Any]]
    messages: List[MessageResponse]

class SessionSummaryResponse(BaseModel):
    """セッション一覧などで使用するサマリー情報"""
    session_id: str
    last_message: str


# ルーターの設定 (プレフィックス: /api/sessions)
router = APIRouter(prefix="/api/sessions", tags=["chat"])

# --- 依存性注入(DI)のためのグローバル変数と関数 ---
# main.pyなどで初期化されることを想定
_repository: Optional[ChatSessionRepository] = None
_agent_brain: Optional[AgentBrainService] = None

def get_repository() -> ChatSessionRepository:
    """リポジトリのインスタンスを取得するための依存関数"""
    if _repository is None:
        raise RuntimeError("ChatSessionRepository not initialized")
    return _repository

def get_agent_brain() -> AgentBrainService:
    """AI（Agent）のロジックを扱うサービスのインスタンスを取得するための依存関数"""
    if _agent_brain is None:
        raise RuntimeError("AgentBrainService not initialized")
    return _agent_brain


# --- エンドポイント定義 ---

@router.post("", response_model=SessionSummaryResponse)
def create_session(
    repo: ChatSessionRepository = Depends(get_repository)
):
    """
    新規チャットセッションを作成するエンドポイント
    """
    from src.features.chat.domain.entities import ChatSession
    session = ChatSession()
    repo.save(session)
    return SessionSummaryResponse(
        session_id=str(session.session_id),
        last_message="New Session"
    )


@router.get("", response_model=List[SessionSummaryResponse])
def get_sessions(
    repo: ChatSessionRepository = Depends(get_repository)
):
    """
    保存されているすべてのセッション一覧を取得するエンドポイント
    """
    use_case = GetSessionsUseCase(repo)
    results = use_case.execute()
    return [SessionSummaryResponse(**res) for res in results]


@router.post("/{session_id}/messages", response_model=SendMessageResponse)
def send_message(
    session_id: str,
    payload: MessageRequest,
    repo: ChatSessionRepository = Depends(get_repository),
    brain: AgentBrainService = Depends(get_agent_brain)
):
    """
    特定のセッションにメッセージを送信し、AIからの回答を取得するエンドポイント
    """
    try:
        # セッションIDの形式バリデーション（Value Objectを利用）
        s_id = SessionId(session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # ユースケースの実行
    use_case = SendMessageUseCase(repo, brain)#ここでmain.pyで初期化されたリポジトリとエージェントブレインのインスタンスが注入される
    input_dto = SendMessageInputDTO(content=payload.content, session_id=str(s_id), image=payload.image)
    output_dto = use_case.execute(input_dto)

    # DTOからレスポンススキーマに変換して返却
    return SendMessageResponse(
        session_id=output_dto.session_id,
        response_content=output_dto.response_content,
        thinking_steps=output_dto.thinking_steps,
        messages=[
            MessageResponse(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"],
                image=msg.get("image")
            )
            for msg in output_dto.messages
        ]
    )


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
def get_session_messages(
    session_id: str,
    repo: ChatSessionRepository = Depends(get_repository)
):
    """
    特定のセッションに紐付くメッセージ履歴を取得するエンドポイント
    """
    try:
        s_id = SessionId(session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # セッションの存在確認
    session = repo.find_by_id(s_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    # ドメインエンティティのメッセージリストをレスポンス形式に変換
    return [
        MessageResponse(
            role=msg.role,
            content=msg.content,
            timestamp=msg.timestamp.to_iso(),
            image=getattr(msg, "image", None)
        )
        for msg in session.messages
    ]