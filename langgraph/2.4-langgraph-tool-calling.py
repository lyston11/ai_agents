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
    print(f"   ⚙️ [本地物理机] 正在执行 get_weather 函数，传入参数: {location}")
    weather_db = {"台北": "晴天，25度", "彰化": "夜风徐徐，气温 22 度，适合敲代码", "北京": "大风，10度"}
    return weather_db.get(location, "未知地区天气数据")


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
# [环境侦测] 动态服务发现 (解决你的多机兼容问题)
# ==========================================
async def auto_detect_model() -> str:
    """向本地 Ollama 查询已安装的模型，按优先级自动匹配"""
    url = "http://localhost:11434/api/tags"
    # 【架构师思维】你的优先级列表：首选 3.2:3b，次选 3:latest
    candidates = ["llama3.2:3b", "llama3:latest", "llama3.2:latest", "llama3"]

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    installed = [m["name"] for m in data.get("models", [])]

                    # 遍历优先级列表，匹配本机存在的模型
                    for target in candidates:
                        if target in installed:
                            return target
    except Exception:
        pass
    return "llama3:latest"  # 如果探测失败，给一个兜底的默认值


# ==========================================
# [LangGraph 核心] 状态图纸与双节点
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list[Dict[str, Any]], operator.add]
    # 【核心新增】将模型配置作为状态的一部分存入黑板
    model_name: str


async def llm_node(state: AgentState):
    # 打工人从黑板上读取今天该用哪个模型干活
    current_model = state.get("model_name", "llama3:latest")
    print(f"🧠 [LLM 节点] 正在使用 {current_model} 思考，并翻阅工具说明书...")

    url = "http://localhost:11434/api/chat"
    payload = {
        "model": current_model,
        "messages": state["messages"],
        "tools": TOOLS_MANUAL,
        "stream": False
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()

                # 防弹机制：如果 Ollama 依然抛错，优雅拦截
                if "message" not in result:
                    error_detail = result.get("error", "未知底层错误")
                    print(f"\n🚨 [Ollama 原始报错]: {error_detail}\n")
                    return {"messages": [{"role": "assistant", "content": f"系统拦截到模型异常: {error_detail}"}]}

                response.raise_for_status()
                return {"messages": [result["message"]]}

    except Exception as e:
        print(f"❌ [请求物理异常]: {str(e)}")
        return {"messages": [{"role": "assistant", "content": "大模型服务连接彻底失败"}]}


async def tool_executor_node(state: AgentState):
    print("🛠️ [工具节点] 收到大模型的 JSON 调用指令，准备物理执行...")
    last_msg = state["messages"][-1]

    tool_call = last_msg.get("tool_calls", [])[0]
    func_name = tool_call["function"]["name"]
    func_args = tool_call["function"]["arguments"]

    if func_name == "get_weather":
        tool_result = get_weather(location=func_args["location"])
    else:
        tool_result = "未知的工具"

    print(f"   ✅ [本地物理机] 执行完毕，拿到物理结果: {tool_result}")
    return {"messages": [{"role": "tool", "content": tool_result}]}


def should_continue(state: AgentState) -> str:
    last_msg = state["messages"][-1]
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
    # 【架构师操作 1】开机瞬间，自动侦测当前电脑环境！
    best_model = await auto_detect_model()
    print(f"🌐 [系统启动] 成功为当前电脑适配模型: {best_model}\n")

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", llm_node)
    workflow.add_node("action", tool_executor_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "action", "end": END})
    workflow.add_edge("action", "agent")

    app = workflow.compile()

    print("=== 2.4 Tool Calling 真机兼容版实战 ===")

    # 【架构师操作 2】依赖注入：把侦测到的模型名字，作为初始状态写入黑板
    initial_state = {
        "messages": [{"role": "user", "content": "请问彰化现在的天气怎么样？"}],
        "model_name": best_model
    }

    final_state = await app.ainvoke(initial_state)
    print("\n📊 [最终回复]:", final_state["messages"][-1].get("content"))


if __name__ == "__main__":
    asyncio.run(main())