import asyncio
import aiohttp
import operator
import json
from typing import TypedDict, Annotated, Dict, Any
from langgraph.graph import StateGraph, START, END


# ==========================================
# [本地工具库] 物理世界的真实函数
# ==========================================
def get_weather(location: str) -> str:
    """真实 Python 函数，未来可以替换为调第三方 API 或查数据库"""
    print(f"   ⚙️ [本地物理机] 正在执行 get_weather 函数，传入参数: {location}")
    # 模拟真实数据库
    weather_db = {"台北": "晴天，25度", "彰化": "夜风徐徐，气温 22 度，适合敲代码", "北京": "大风，10度"}
    return weather_db.get(location, "未知地区天气数据")


# 【核心武器】大模型的“工具说明书” (严格遵循 JSON Schema)
TOOLS_MANUAL = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "当用户询问天气时，调用此工具获取实时数据。",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "城市名称，例如：台北、彰化"}
            },
            "required": ["location"]
        }
    }
}]


# ==========================================
# [LangGraph 核心] 状态图纸与双节点
# ==========================================
class AgentState(TypedDict):
    # 注意：现在存的是复杂的字典列表，不再是纯字符串了
    messages: Annotated[list[Dict[str, Any]], operator.add]


async def llm_node(state: AgentState):
    """大模型节点：带着说明书去请求"""
    print("🧠 [LLM 节点] 正在思考，并翻阅工具说明书...")

    # 【细节】必须使用 /api/chat 接口才能支持工具调用
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "llama3.2:3b",
        "messages": state["messages"],
        "tools": TOOLS_MANUAL,  # 把说明书拍在大模型脸上
        "stream": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
            # 直接提取模型返回的 message 字典
            ai_msg = result["message"]
            return {"messages": [ai_msg]}


async def tool_executor_node(state: AgentState):
    """工具节点：负责把 JSON 指令变成真实的代码执行"""
    print("🛠️ [工具节点] 收到大模型的 JSON 调用指令，准备物理执行...")
    last_msg = state["messages"][-1]

    # 提取大模型的指令
    tool_call = last_msg.get("tool_calls", [])[0]
    func_name = tool_call["function"]["name"]
    func_args = tool_call["function"]["arguments"]

    # 动态执行本地代码
    if func_name == "get_weather":
        tool_result = get_weather(location=func_args["location"])
    else:
        tool_result = "未知的工具"

    print(f"   ✅ [本地物理机] 执行完毕，拿到物理结果: {tool_result}")

    # 【灵魂操作】以 role: tool 的身份，把结果写回黑板
    return {"messages": [{
        "role": "tool",
        "content": tool_result
    }]}


# ==========================================
# [LangGraph 核心] 智能路由交警
# ==========================================
def should_continue(state: AgentState) -> str:
    """交警：检查大模型是不是下达了工具调用指令"""
    last_msg = state["messages"][-1]

    # 如果大模型返回了 tool_calls，说明它不打算聊天，它想调工具
    if "tool_calls" in last_msg and len(last_msg["tool_calls"]) > 0:
        print("👮 [路由交警] 侦测到工具调用请求！立刻切换铁轨 -> 走向工具车间。")
        return "tools"
    else:
        print("👮 [路由交警] 侦测到普通文本，Agent 已给出最终答案，任务结束。")
        return "end"


# ==========================================
# [引擎启动] 组装图纸
# ==========================================
async def main():
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", llm_node)
    workflow.add_node("action", tool_executor_node)

    # 1. 发车去 agent
    workflow.add_edge(START, "agent")

    # 2. agent 思考完，交给交警
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "action", "end": END}
    )

    # 3. 【绝对核心】工具执行完，必须倒退回 agent！
    workflow.add_edge("action", "agent")

    app = workflow.compile()

    print("\n=== 2.4 Tool Calling 真机实战 ===")
    initial_state = {"messages": [{"role": "user", "content": "请问彰化现在的天气怎么样？"}]}

    final_state = await app.ainvoke(initial_state)

    print("\n📊 [最终回复]:", final_state["messages"][-1].get("content"))


if __name__ == "__main__":
    asyncio.run(main())