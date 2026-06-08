import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END

from src.features.agent_brain.domain.agent import AgentAction, AgentState

logger = logging.getLogger("AgentThinkingLoop")

# ==========================================
# 抽象インターフェース定義 (DIP 適用部分)
# ==========================================

class LLMService(ABC):
    """
    LLM クライアントを抽象化するインターフェース (Port)。
    インフラレイヤーの具体的な LLM 実装に依存しないようにします。
    """
    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: List["AgentTool"] = None
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        メッセージ履歴から推論結果とツール呼び出し情報を生成します。
        """
        pass

class AgentTool(ABC):
    """
    エージェントが使用するツールの抽象ベースクラス。
    各カスタムツール（検索、シミュレーションなど）はこのインターフェースを実装します。
    """
    @property
    @abstractmethod
    def name(self) -> str:
        """ツールの識別名"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """ツールの説明"""
        pass

    @property
    def args_schema(self) -> Dict[str, Any]:
        """ツールの引数スキーマ（JSON Schema形式）"""
        return {}

    @abstractmethod
    def execute(self, args: Dict[str, Any]) -> str:
        """ツールの実行ロジック"""
        pass



# ==========================================
# LangGraph ステート定義
# ==========================================

class LangGraphAgentState(TypedDict):
    """
    LangGraph ワークフロー内で受け渡される状態（ステート）のスキーマ。
    """
    messages: List[Dict[str, Any]]       # 会話メッセージ履歴
    thinking_steps: List[Dict[str, Any]] # クライアントに送信する思考プロセスのログ
    next_node: str                       # 次に遷移するノード名
    action: Optional[Dict[str, Any]]     # 実行されるツールの情報 (名称、引数)
    response: Optional[str]              # 最終応答テキスト
    loop_count: int                      # ループ回数（無限ループ防止用リミッター）
    


# ==========================================
# エージェント思考ループ実装 (LangGraph)
# ==========================================

class AgentThinkingLoop:
    """
    LangGraph を使用して、エージェントの推論とツール実行のループを定義・管理するクラス。
    """
    def __init__(self, llm_client: LLMService, tools: List[AgentTool], max_loops: int = 10):
        self.llm_client = llm_client
        self.tools = {tool.name: tool for tool in tools}
        self.max_loops = max_loops
        self.graph = self._build_graph()
        self._print_graph_structure()

    def _print_graph_structure(self) -> None:
        """
        エージェントの LangGraph 構造をアスキーアート形式でターミナルに出力します。
        """
        print("\n" + "=" * 60)
        print("  [LangGraph Agent Brain] Graph Structure Initialized")
        print("=" * 60)
        try:
            # grandalf パッケージがインストールされている場合、LangGraph 標準のアスキーアートを出力
            print(self.graph.get_graph().draw_ascii())
        except Exception:
            # grandalf がない場合のカスタムアスキーアートフォールバック
            print("ga grandalf package not found, displaying simplified graph structure:") 
        print("=" * 60 + "\n")

    def _build_graph(self) -> StateGraph:
        """
        LangGraph のノードとエッジ（遷移ルール）を構築します。
        """
        workflow = StateGraph(LangGraphAgentState)

        # 各ノードの登録
        workflow.add_node("think", self._node_think)
        workflow.add_node("execute_tool", self._node_execute_tool)
        workflow.add_node("generate_response", self._node_generate_response)

        # エントリーポイントの決定
        workflow.set_entry_point("think")

        # 条件付きエッジの登録 (thinkノード終了後、次のアクションを判断)
        workflow.add_conditional_edges(
            "think",
            self._decide_next_step,
            {
                "call_tool": "execute_tool",
                "respond": "generate_response"
            }
        )

        # 標準エッジの登録 (ツールの実行後は再びthinkノードへ戻る)
        workflow.add_edge("execute_tool", "think")
        workflow.add_edge("generate_response", END)

        return workflow.compile()

    def run(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        エージェントの推論ワークフローを実行します。
        """
        initial_state: LangGraphAgentState = {
            "messages": messages,
            "thinking_steps": [],
            "next_node": "think",
            "action": None,
            "response": None,
            "loop_count": 0
        }
        print("\n🚀 [Agent Loop] Starting LangGraph Agent Thinking Loop...")
        result = self.graph.invoke(initial_state)
        print("🏁 [Agent Loop] Workflow completed.\n")
        return result

    def _sanitize_messages_for_llm(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        システムメッセージ内のSTRUCTURED_DATA_JSON_STARTからSTRUCTURED_DATA_JSON_ENDまでの
        大きなJSONデータブロック（時系列データ等）を除去し、LLMに不要なデータを送信しないようにします。
        また、画像が含まれている場合は、messageに "image" フィールドとして持たせることでマルチモーダルメッセージへの変換を容易にします。
        """
        import json
        sanitized = []
        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            image_url = m.get("image")
            
            if "STRUCTURED_DATA_JSON_START" in content:
                parts = content.split("STRUCTURED_DATA_JSON_START")
                before = parts[0]
                after = ""
                extracted_image = None
                if len(parts) > 1:
                    subparts = parts[1].split("STRUCTURED_DATA_JSON_END")
                    if len(subparts) > 0:
                        try:
                            data = json.loads(subparts[0].strip())
                            if isinstance(data, dict) and "image" in data:
                                extracted_image = data["image"]
                        except Exception:
                            pass
                    if len(subparts) > 1:
                        after = subparts[1]
                sanitized_content = (before + after).strip()
                sanitized.append({
                    "role": role,
                    "content": sanitized_content,
                    "image": extracted_image or image_url
                })
            else:
                sanitized.append({
                    "role": role,
                    "content": content,
                    "image": image_url
                })
        return sanitized


    # --- 各ノードの実装 ---

    def _node_think(self, state: LangGraphAgentState) -> Dict[str, Any]:
        """
        [think ノード]
        現在の会話履歴を元にLLMへ問い合わせ、次のアクション（ツール呼び出し、または最終返答）を考えます。
        """
        print("\n🧠 [Node: think] Analyzing user request and conversation history...")
        messages = state["messages"]
        thinking_steps = list(state["thinking_steps"])
        loop_count = state.get("loop_count", 0)

        # ループ回数の上限チェック
        if loop_count >= self.max_loops:
            logger.warning(f"Agent thinking loop exceeded maximum iterations ({loop_count}/{self.max_loops}). Halting.")
            thinking_steps.append({
                "node": "think",
                "status": "warning",
                "message": f"Maximum iteration limit ({self.max_loops}) reached. Execution halted to prevent infinite loop.",
                "details": {"loop_count": loop_count, "max_loops": self.max_loops}
            })
            return {
                "messages": messages,
                "thinking_steps": thinking_steps,
                "next_node": "respond",
                "action": None,
                "response": f"推論ループの上限回数（{self.max_loops}回）に達したため、処理を一時中断しました。現在の結果を元に応答します。",
                "loop_count": loop_count
            }

        # LLMへ送るプロンプトをクリーンにする（巨大な時系列JSONデータの除外）
        sanitized_messages = self._sanitize_messages_for_llm(messages)

        # LLMを呼び出し、思考結果と検出されたツール呼び出し情報を取得
        llm_response, tool_calls = self.llm_client.generate(sanitized_messages, tools=list(self.tools.values()))
        
        # LLMとのJson形式のやり取りを出力
        import json
        print("   ➔ [LLM Request JSON (Sanitized)]:")
        print(json.dumps(sanitized_messages, indent=2, ensure_ascii=False))
        print("   ➔ [LLM Response JSON]:")
        print(json.dumps({
            "response_text": llm_response,
            "tool_calls": tool_calls
        }, indent=2, ensure_ascii=False))

        print(f"   ➔ Thought generated: \"{llm_response}\"")

        thinking_steps.append({
            "node": "think",
            "status": "success",
            "message": f"LLM generated thought: {llm_response}",
            "details": {"tool_calls_detected": len(tool_calls)}
        })

        if tool_calls:
            # 簡単化のため、最初に検出されたツールのみを実行対象とします
            tc = tool_calls[0]
            action = {"tool_name": tc["name"], "tool_input": tc["args"]}
            print(f"   ➔ Decision: CALL_TOOL (Name: '{tc['name']}', Args: {tc['args']})")
            return {
                "messages": messages,
                "thinking_steps": thinking_steps,
                "next_node": "call_tool",
                "action": action,
                "response": None,
                "loop_count": loop_count + 1
            }
        else:
            # ツール呼び出しが不要な場合、最終回答フェーズへ遷移
            print("   ➔ Decision: RESPOND (No tools required)")
            return {
                "messages": messages,
                "thinking_steps": thinking_steps,
                "next_node": "respond",
                "action": None,
                "response": llm_response,
                "loop_count": loop_count + 1
            }

    def _node_execute_tool(self, state: LangGraphAgentState) -> Dict[str, Any]:
        """
        [execute_tool ノード]
        指示されたツールを検索し、引数を渡して実行します。結果はシステムメッセージとして履歴に追加されます。
        """
        action = state["action"]
        if not action:
            return state

        tool_name = action["tool_name"]
        tool_input = action["tool_input"]
        print(f"\n🛠️ [Node: execute_tool] Invoking tool '{tool_name}' with parameters: {tool_input}")

        messages = list(state["messages"])
        thinking_steps = list(state["thinking_steps"])

        thinking_steps.append({
            "node": "execute_tool",
            "status": "running",
            "message": f"Executing tool: {tool_name} with parameters: {tool_input}",
            "details": action
        })

        # 登録されているツールから該当するものを取得して実行
        tool = self.tools.get(tool_name)
        if tool:
            try:
                result_str = tool.execute(tool_input)
                status = "success"
                msg_detail = f"Tool {tool_name} successfully executed."
                print(f"   ➔ Execution Status: Success")
            except Exception as e:
                result_str = f"Error executing tool: {str(e)}"
                status = "error"
                msg_detail = f"Tool {tool_name} execution failed."
                print(f"   ➔ Execution Status: Error ({str(e)})")
        else:
            result_str = f"Tool '{tool_name}' not found."
            status = "error"
            msg_detail = f"Tool {tool_name} not registered in agent brain."
            print(f"   ➔ Execution Status: Tool Not Found")

        thinking_steps.append({
            "node": "execute_tool",
            "status": status,
            "message": msg_detail,
            "details": {"output": result_str}
        })

        # ツールの実行結果を会話履歴の末尾に追加（LLMが次の推論で結果を参照できるようにする）
        messages.append({
            "role": "system",
            "content": f"Tool '{tool_name}' execution result: {result_str}"
        })

        return {
            "messages": messages,
            "thinking_steps": thinking_steps,
            "next_node": "think",
            "action": None,
            "response": None
        }

    def _node_generate_response(self, state: LangGraphAgentState) -> Dict[str, Any]:
        """
        [generate_response ノード]
        エージェントの最終回答を作成し、推論プロセス全体を完了します。
        """
        print("\n💬 [Node: generate_response] Formulating final response to the user...")
        thinking_steps = list(state["thinking_steps"])
        response = state["response"] or "Response generated."

        # 履歴内のシステムメッセージ（ツール実行結果）から構造化データJSONブロックを抽出
        # 今回のターン（最後のUserメッセージ以降）で実行されたすべてのツールの結果を対象とします
        latest_user_idx = -1
        messages = state["messages"]
        for idx in range(len(messages) - 1, -1, -1):
            if messages[idx].get("role") == "user":
                latest_user_idx = idx
                break

        json_blocks = []
        start_search_idx = latest_user_idx + 1 if latest_user_idx != -1 else 0
        for idx in range(start_search_idx, len(messages)):
            m = messages[idx]
            if m.get("role") == "system" and "STRUCTURED_DATA_JSON_START" in m.get("content", ""):
                content_str = m["content"]
                parts = content_str.split("STRUCTURED_DATA_JSON_START")
                if len(parts) > 1:
                    subparts = parts[1].split("STRUCTURED_DATA_JSON_END")
                    if len(subparts) > 0:
                        json_blocks.append(f"STRUCTURED_DATA_JSON_START\n{subparts[0].strip()}\nSTRUCTURED_DATA_JSON_END")

        # LLMが最終回答にJSONブロックを含めていなかった場合、自動ですべてのブロックを末尾に付加する
        for block in json_blocks:
            if block not in response:
                response = f"{response}\n\n{block}"


        print(f"   ➔ Response preview: \"{response[:100]}...\"")

        thinking_steps.append({
            "node": "generate_response",
            "status": "success",
            "message": "Final response generated successfully.",
            "details": {"response": response}
        })

        return {
            "messages": state["messages"],
            "thinking_steps": thinking_steps,
            "next_node": END,
            "action": None,
            "response": response
        }

    # --- 遷移判断 ---

    def _decide_next_step(self, state: LangGraphAgentState) -> str:
        """
        条件付きエッジで使用され、次に遷移すべきノード名を返します。
        """
        return state["next_node"]
