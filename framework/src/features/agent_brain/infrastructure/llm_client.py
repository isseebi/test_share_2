import json
import httpx
from typing import List, Dict, Any, Tuple
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_ollama import ChatOllama
from langchain_anthropic import ChatAnthropic
from src.shared.infrastructure.config import Config
from src.shared.infrastructure.logger import get_logger
from src.features.agent_brain.application.brain_loop import LLMService

logger = get_logger("LLMClient")

class LLMClient(LLMService):
    """
    LLM (Ollama, Claude, Mock) との通信を行うインフラストラクチャサービス。
    """
    def __init__(self, config: Config):
        self.provider = config.LLM_PROVIDER
        self.ollama_url = config.OLLAMA_URL
        self.claude_api_key = config.CLAUDE_API_KEY

    def _get_ollama_model(self) -> ChatOllama:
        if not hasattr(self, "_ollama_model"):
            self._ollama_model = ChatOllama(
                base_url=self.ollama_url,
                model="gemma4:12b"
            )
        return self._ollama_model

    def _get_claude_model(self) -> ChatAnthropic:
        if not hasattr(self, "_claude_model"):
            self._claude_model = ChatAnthropic(
                api_key=self.claude_api_key,
                model="claude-3-5-sonnet-20241022"
            )
        return self._claude_model

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
        elif self.provider == "claude":
            return self._call_claude(messages, tools)
        else:
            return self._call_mock(messages, tools)

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
            else:
                tool_calls = self._parse_text_for_mock_tool_calls(content)
                
            return content, tool_calls
        except Exception as e:
            logger.error(f"Error calling Ollama via LangChain: {e}. Falling back to mock.")
        
        return self._call_mock(messages, tools)

    def _call_claude(self, messages: List[Dict[str, Any]], tools: List[Any] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Anthropic Claude API を LangChain 経由で呼び出して応答を取得します。
        """
        if not self.claude_api_key:
            logger.warning("Claude API key not set. Falling back to mock.")
            return self._call_mock(messages, tools)
        
        try:
            lc_messages = self._to_lc_messages(messages)
            model = self._get_claude_model()
            
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
            else:
                tool_calls = self._parse_text_for_mock_tool_calls(content)
                
            return content, tool_calls
        except Exception as e:
            logger.error(f"Error calling Claude via LangChain: {e}. Falling back to mock.")
        
        return self._call_mock(messages, tools)


    def _call_mock(self, messages: List[Dict[str, Any]], tools: List[Any] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        [モックモード]
        ツール説明をもとに、ユーザーのクエリと各ツールの名称・説明から最適なツールを動的に判定して呼び出します。
        """
        # 直前のアクションがツール実行（roleがsystem）であった場合、無限ループを防ぎ、実行結果を整形して最終応答とする
        if messages and messages[-1]["role"] == "system":
            system_content = messages[-1]["content"]
            if "PPI Simulation completed" in system_content or ("Simulation completed" in system_content and "kvp" in system_content):
                return f"I have run the PPI control simulation for you. Here are the results and parameters:\n\n{system_content}", []
            elif "Simulation completed" in system_content or "STRUCTURED_DATA_JSON_START" in system_content:
                if "best_params" in system_content:
                    if "kvp" in system_content:
                        return f"I have run the PPI parameter optimization for you. Here are the results:\n\n{system_content}", []
                    else:
                        return f"I have run the PID parameter optimization for you. Here are the results:\n\n{system_content}", []
                else:
                    return f"I have run the PID control simulation for you. Here are the results and parameters:\n\n{system_content}", []
            elif "PPI Parameter Optimization Completed" in system_content or "PPI Parameter Optimization" in system_content:
                return f"I have run the PPI parameter optimization for you. Here are the results:\n\n{system_content}", []
            elif "PID Parameter Optimization Completed" in system_content or "PID Parameter Optimization" in system_content:
                return f"I have run the PID parameter optimization for you. Here are the results:\n\n{system_content}", []
            elif "user_parameters_tool" in system_content or "system_name" in system_content:
                return f"I have retrieved the user system parameters for you. Here is the configuration:\n\n{system_content}", []
            elif "DuckDuckGo search results" in system_content or "web_search_tool" in system_content:
                return f"I have performed a web search using DuckDuckGo. Here is what I found:\n\n{system_content}", []
            else:
                return f"I have searched the reference documentation. Here is what I found:\n\n{system_content}", []

        # ユーザーの最後の入力クエリを取得
        last_user_message = ""
        for m in reversed(messages):
            if m["role"] == "user":
                last_user_message = m["content"].lower()
                break

        if not last_user_message:
            return "Hello! I can help you with your requests.", []

        # 利用可能なツールがある場合、動的にマッチングを試みる
        if tools:
            # First, check if specific keywords match PPI, Web Search, or User Parameter tools
            is_ppi = "ppi" in last_user_message
            is_web = any(k in last_user_message for k in ["web search", "web", "internet", "ddg", "duckduckgo", "ネット検索", "ウェブ検索", "検索"])
            is_user_param = any(k in last_user_message for k in ["user parameter", "user parameters", "parameter info", "システムパラメータ", "パラメータ取得", "現在のパラメータ"])

            best_tool = None
            
            # Prioritize optimization over simulation if both keywords match
            if is_ppi:
                if any(k in last_user_message for k in ["optimize", "optimization", "tuning", "optuna", "bayesian", "最適化"]):
                    for tool in tools:
                        if tool.name == "ppi_bayesian_optimization_tool":
                            best_tool = tool
                            break
                if not best_tool and any(k in last_user_message for k in ["sim", "simulation", "run", "シミュレーション", "実行"]):
                    for tool in tools:
                        if tool.name == "ppi_simulation_tool":
                            best_tool = tool
                            break

            # If not routed yet, check other specific tools
            if not best_tool:
                for tool in tools:
                    if is_web and tool.name == "web_search_tool":
                        best_tool = tool
                        break
                    elif is_user_param and tool.name == "user_parameters_tool":
                        best_tool = tool
                        break

            # Fall back to general matching loop if no specific match was found
            if not best_tool:
                for tool in tools:
                    # Skip PPI-specific tools here unless "ppi" was in last_user_message
                    if "ppi" in tool.name and not is_ppi:
                        continue
                    tool_keywords = [tool.name.lower()]
                    desc_lower = tool.description.lower()
                    
                    # キーワードマッピングの構築
                    if "search_tool" == tool.name:
                        tool_keywords.extend(["search", "find", "spec", "rag", "document", "仕様", "検索", "仕様書"])
                    elif "simulation_tool" == tool.name:
                        tool_keywords.extend(["sim", "simulation", "run", "pid", "control", "シミュレーション", "実行"])
                    elif "bayesian_optimization_tool" == tool.name:
                        tool_keywords.extend(["optimize", "tuning", "optimization", "optuna", "bayesian", "最適化", "チューニング", "ベイズ"])

                    if any(kw in last_user_message for kw in tool_keywords):
                        best_tool = tool
                        break

            if best_tool:
                args = {}
                if best_tool.name == "web_search_tool":
                    query = "servo control"
                    import re
                    match = re.search(r'(?:web search|web|internet|ddg|duckduckgo|ネット検索|ウェブ検索|検索)\s*(.*)', last_user_message)
                    if match and match.group(1).strip():
                        query = match.group(1).strip()
                    args = {"query": query}
                elif best_tool.name == "ppi_simulation_tool":
                    kp, kvp, kvi = 1.0, 1.0, 0.1
                    import re
                    kp_match = re.search(r'kp\s*=\s*([0-9.]+)', last_user_message)
                    kvp_match = re.search(r'kvp\s*=\s*([0-9.]+)', last_user_message)
                    kvi_match = re.search(r'kvi\s*=\s*([0-9.]+)', last_user_message)
                    if kp_match: kp = float(kp_match.group(1))
                    if kvp_match: kvp = float(kvp_match.group(1))
                    if kvi_match: kvi = float(kvi_match.group(1))
                    args = {"kp": kp, "kvp": kvp, "kvi": kvi, "steps": 50}
                elif best_tool.name == "ppi_bayesian_optimization_tool":
                    args = {
                        "kp_min": 1.0, "kp_max": 5.0,
                        "kvp_min": 0.5, "kvp_max": 3.0,
                        "kvi_min": 0.0, "kvi_max": 2.0,
                        "n_trials": 15
                    }
                elif best_tool.name == "user_parameters_tool":
                    args = {}
                elif best_tool.name == "search_tool":
                    query = "servo specification"
                    if "search" in last_user_message:
                        parts = last_user_message.split("search")
                        if len(parts) > 1 and parts[1].strip():
                            query = parts[1].strip()
                    args = {"query": query}
                elif best_tool.name == "simulation_tool":
                    p, i, d = 1.0, 0.1, 0.05
                    import re
                    p_match = re.search(r'p\s*=\s*([0-9.]+)', last_user_message)
                    i_match = re.search(r'i\s*=\s*([0-9.]+)', last_user_message)
                    d_match = re.search(r'd\s*=\s*([0-9.]+)', last_user_message)
                    if p_match: p = float(p_match.group(1))
                    if i_match: i = float(i_match.group(1))
                    if d_match: d = float(d_match.group(1))
                    args = {"kp": p, "ki": i, "kd": d, "steps": 50}
                elif best_tool.name == "bayesian_optimization_tool":
                    args = {
                        "kp_min": 1.0, "kp_max": 5.0,
                        "ki_min": 0.0, "ki_max": 2.0,
                        "kd_min": 0.0, "kd_max": 1.0,
                        "n_trials": 15
                    }

                return f"Running tool {best_tool.name} based on your request...", [{"name": best_tool.name, "args": args}]

        # デフォルトの返答
        return "Hello! I am your Clean Architecture AI Agent. I can help search servo specifications and run P-PI or PID control simulations or optimizations.", []

    def _parse_text_for_mock_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """
        LLMがテキスト形式で出力した特殊タグ (例: `TOOL_CALL: search_tool{"query": "..."}`)
        をパースして構造データに変換するヘルパー関数。
        """
        tool_calls = []
        if "TOOL_CALL: web_search_tool" in text:
            try:
                start = text.index("TOOL_CALL: web_search_tool") + len("TOOL_CALL: web_search_tool")
                json_str = text[start:].strip()
                args = json.loads(json_str)
                tool_calls.append({"name": "web_search_tool", "args": args})
            except Exception:
                pass
        elif "TOOL_CALL: ppi_simulation_tool" in text:
            try:
                start = text.index("TOOL_CALL: ppi_simulation_tool") + len("TOOL_CALL: ppi_simulation_tool")
                json_str = text[start:].strip()
                args = json.loads(json_str)
                tool_calls.append({"name": "ppi_simulation_tool", "args": args})
            except Exception:
                pass
        elif "TOOL_CALL: ppi_bayesian_optimization_tool" in text:
            try:
                start = text.index("TOOL_CALL: ppi_bayesian_optimization_tool") + len("TOOL_CALL: ppi_bayesian_optimization_tool")
                json_str = text[start:].strip()
                args = json.loads(json_str)
                tool_calls.append({"name": "ppi_bayesian_optimization_tool", "args": args})
            except Exception:
                pass
        elif "TOOL_CALL: user_parameters_tool" in text:
            try:
                start = text.index("TOOL_CALL: user_parameters_tool") + len("TOOL_CALL: user_parameters_tool")
                json_str = text[start:].strip()
                args = json.loads(json_str)
                tool_calls.append({"name": "user_parameters_tool", "args": args})
            except Exception:
                pass
        elif "TOOL_CALL: search_tool" in text:
            try:
                start = text.index("TOOL_CALL: search_tool") + len("TOOL_CALL: search_tool")
                json_str = text[start:].strip()
                args = json.loads(json_str)
                tool_calls.append({"name": "search_tool", "args": args})
            except Exception:
                pass
        elif "TOOL_CALL: simulation_tool" in text:
            try:
                start = text.index("TOOL_CALL: simulation_tool") + len("TOOL_CALL: simulation_tool")
                json_str = text[start:].strip()
                args = json.loads(json_str)
                tool_calls.append({"name": "simulation_tool", "args": args})
            except Exception:
                pass
        elif "TOOL_CALL: bayesian_optimization_tool" in text:
            try:
                start = text.index("TOOL_CALL: bayesian_optimization_tool") + len("TOOL_CALL: bayesian_optimization_tool")
                json_str = text[start:].strip()
                args = json.loads(json_str)
                tool_calls.append({"name": "bayesian_optimization_tool", "args": args})
            except Exception:
                pass
        return tool_calls
