from typing import List, Dict, Any, Tuple
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_ollama import ChatOllama
from langchain_aws import ChatBedrock
from src.shared.infrastructure.config import Config
from src.shared.infrastructure.logger import get_logger
from src.features.agent_brain.application.brain_loop import LLMService

logger = get_logger("LLMClient")

class LLMClient(LLMService):
    """
    LLM (Ollama, Bedrock) との通信を行うインフラストラクチャサービス。
    """
    def __init__(self, config: Config):
        self.provider = config.LLM_PROVIDER
        self.ollama_url = config.OLLAMA_URL
        self.aws_region = config.AWS_REGION
        self.bedrock_model_id = config.BEDROCK_MODEL_ID
        self.aws_access_key_id = config.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = config.AWS_SECRET_ACCESS_KEY
        self.aws_session_token = config.AWS_SESSION_TOKEN

    def _get_ollama_model(self) -> ChatOllama:
        if not hasattr(self, "_ollama_model"):
            self._ollama_model = ChatOllama(
                base_url=self.ollama_url,
                model="gemma4:12b"
            )
        return self._ollama_model

    def _get_bedrock_model(self) -> ChatBedrock:
        if not hasattr(self, "_bedrock_model"):
            kwargs = {
                "model_id": self.bedrock_model_id,
                "region_name": self.aws_region,
            }
            if self.aws_access_key_id:
                kwargs["aws_access_key_id"] = self.aws_access_key_id
            if self.aws_secret_access_key:
                kwargs["aws_secret_access_key"] = self.aws_secret_access_key
            if self.aws_session_token:
                kwargs["aws_session_token"] = self.aws_session_token
            
            self._bedrock_model = ChatBedrock(**kwargs)
        return self._bedrock_model

    def _to_lc_messages(self, messages: List[Dict[str, Any]]) -> List[Any]:
        lc_messages = []
        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            image_url = m.get("image")
            
            if image_url:
                content_blocks = [
                    {"type": "text", "text": content},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
                if role == "system":
                    # Convert system messages with images to HumanMessages since APIs don't support images in system messages
                    lc_messages.append(HumanMessage(content=content_blocks))
                elif role == "user":
                    lc_messages.append(HumanMessage(content=content_blocks))
                elif role == "assistant":
                    lc_messages.append(AIMessage(content=content_blocks))
            else:
                if role == "system":
                    lc_messages.append(SystemMessage(content=content))
                elif role == "user":
                    lc_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    lc_messages.append(AIMessage(content=content))
        return lc_messages

    def generate(self, messages: List[Dict[str, Any]], tools: List[Any] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        メッセージ履歴を受け取り、応答テキストと検出されたツール呼び出し情報をタプルで返します。
        
        返り値: (response_text, tool_calls)
        - tool_calls 例: [{"name": "search_tool", "args": {"query": "..."}}]
        """
        logger.info(f"Generating response using provider: {self.provider}")
        
        if self.provider == "ollama":
            return self._call_ollama(messages, tools)
        elif self.provider == "bedrock" or self.provider == "claude":
            if self.provider == "claude":
                logger.info("Provider is 'claude', routing to AWS Bedrock.")
            return self._call_bedrock(messages, tools)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    def _call_ollama(self, messages: List[Dict[str, Any]], tools: List[Any] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        ローカルで起動している Ollama API を LangChain 経由で呼び出して応答を取得します。
        """
        try:
            lc_messages = self._to_lc_messages(messages)
            model = self._get_ollama_model()
            
            # ツールが提供されている場合、モデルにバインドする
            if tools:
                lc_tools = []
                for tool in tools:
                    lc_tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.args_schema or {
                            "type": "object",
                            "properties": {}
                        }
                    })
                model = model.bind_tools(lc_tools)
                
            response = model.invoke(lc_messages)
            content = str(response.content)
            
            tool_calls = []
            if hasattr(response, "tool_calls") and response.tool_calls:
                for tc in response.tool_calls:
                    tool_calls.append({
                        "name": tc["name"],
                        "args": tc["args"]
                    })
            return content, tool_calls
        except Exception as e:
            logger.error(f"Error calling Ollama via LangChain: {e}")
            raise e

    def _call_bedrock(self, messages: List[Dict[str, Any]], tools: List[Any] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        AWS Bedrock Claude API を LangChain 経由で呼び出して応答を取得します。
        """
        try:
            lc_messages = self._to_lc_messages(messages)
            model = self._get_bedrock_model()
            
            # ツールが提供されている場合、モデルにバインドする
            if tools:
                lc_tools = []
                for tool in tools:
                    lc_tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.args_schema or {
                            "type": "object",
                            "properties": {}
                        }
                    })
                model = model.bind_tools(lc_tools)
                
            response = model.invoke(lc_messages)
            content = str(response.content)
            
            tool_calls = []
            if hasattr(response, "tool_calls") and response.tool_calls:
                for tc in response.tool_calls:
                    tool_calls.append({
                        "name": tc["name"],
                        "args": tc["args"]
                    })
            return content, tool_calls
        except Exception as e:
            logger.error(f"Error calling Bedrock via LangChain: {e}")
            raise e
