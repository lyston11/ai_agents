import asyncio
import aiohttp
import operator
import json
from typing import TypedDict, Annotated, Dict, Any
from langgraph.graph import StateGraph, START, END

# 【高能预警：新武器介入】状态保存器，HITL 的必备底层依赖
from langgraph.checkpoint.memory import MemorySaver


# ==========================================
# [本地高危工具库]
# ==========================================
def refund_user(user_name: str, amount: int) -> str:
    """高危操作：财务退款"""
    print(f"\n   💰 [高危物理执行] 正在从公司账户向 {user_name} 退款 {amount} 元...")
    return f"退款成功！流水号：TXN-8888，金额：{amount}"


TOOLS_MANUAL = [{
    "type": "function",
    "function": {
        "name": "refund_user",
        "description": "当用户要求退款时调用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "user_name": {"type": "string"},
                "amount": {"type": "integer", "description": "退款金额"}
            },
            "required": ["user_name", "amount"]
        }
    }
}]


# ==========================================
# [LangGraph 核心] 状态图纸与节点 (复用 2.4 逻辑)
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list[Dict[str, Any]], operator.add]


async def llm_node(state: AgentState):
    print("🧠 [LLM 节点] 正在思考...")
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "llama3.2:3b",  # 默认使用你刚刚升级的最新模型
        "messages": state["messages"],
        "tools": TOOLS_MANUAL,
        "stream": False
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
            return {"messages": [result["message"]]}


async def tool_executor_node(state: AgentState):
    last_msg = state["messages"][-1]
    tool_call = last_msg.get("tool_calls", [])[0]
    func_name = tool_call["function"]["name"]
    func_args = tool_call["function"]["arguments"]

    if func_name == "refund_user":
        tool_result = refund_user(user_name=func_args["user_name"], amount=func_args["amount"])
    else:
        tool_result = "未知工具"

    return {"messages": [{"role": "tool", "content": tool_result}]}


def should_continue(state: AgentState) -> str:
    last_msg = state["messages"][-1]
    if "tool_calls" in last_msg and len(last_msg["tool_calls"]) > 0:
        print("👮 [路由交警] 侦测到高危退款请求！走向 action 节点。")
        return "action"
    return "end"


# ==========================================
# [引擎启动] 带有 HITL 拦截器的图纸
# ==========================================
async def main():
    # 1. 初始化内存保险箱
    memory = MemorySaver()

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", llm_node)
    workflow.add_node("action", tool_executor_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, {"action": "action", "end": END})
    workflow.add_edge("action", "agent")

    # 【架构师核心配置】编译时挂载保险箱，并设置拦截点！
    app = workflow.compile(
        checkpointer=memory,
        interrupt_before=["action"]  # 拦截令：在进入 action 节点之前，强制挂起！
    )

    print("\n=== 2.6 人类在环 (HITL) 生产级安全拦截实战 ===")

    # 线程 ID (Thread ID)：必须有它，保险箱才知道这是谁的会话
    config = {"configurable": {"thread_id": "lyston_thread_001"}}
    initial_state = {"messages": [{"role": "user", "content": "我是 Lyston，你们的服务太差了，立刻给我退款 500 元！"}]}

    # 第一次运行：流水线会在 action 前急刹车
    await app.ainvoke(initial_state, config=config)

    # 【观测点】检查流水线当前的状态
    snapshot = app.get_state(config)

    # 如果 next 里有值，说明流水线被挂起了，等待进入下一个节点
    if snapshot.next:
        print("\n🚨🚨🚨 [系统警报] 流水线已被强制拦截挂起！🚨🚨🚨")
        print(f"   -> 下一个即将执行的节点是: {snapshot.next}")

        # 提取大模型准备执行的工具参数，供人类审查
        pending_tool_call = snapshot.values["messages"][-1]["tool_calls"][0]
        print(f"   -> ⚠️ 大模型正准备执行: {pending_tool_call['function']['name']}")
        print(f"   -> ⚠️ 提取的参数: {pending_tool_call['function']['arguments']}")

        # 人类控制台
        user_approval = input("\n👨‍💻 [人类架构师] 是否批准该笔退款？(输入 Y 放行，输入 N 终止): ")

        if user_approval.strip().upper() == "Y":
            print("\n✅ 人类已授权，释放拦截，流水线继续...")
            # 【恢复执行】传入 None，代表不需要新的用户输入，直接顺着记忆往下跑
            final_state = await app.ainvoke(None, config=config)
            print("\n📊 [最终回复]:", final_state["messages"][-1].get("content"))
        else:
            print("\n🚫 人类已否决，任务强制终止。")
    else:
        print("任务正常结束，未触发拦截。")


if __name__ == "__main__":
    asyncio.run(main())