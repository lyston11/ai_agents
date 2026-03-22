import asyncio
import operator
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END


# ==========================================
# [LangGraph 核心 1] 定义 State 黑板结构
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list[str], operator.add]


# ==========================================
# [LangGraph 核心 2] 定义不同的干活节点 (Workers)
# ==========================================
async def llm_node(state: AgentState):
    """普通大模型节点：负责闲聊"""
    print("🧠 [LLM 节点] 收到任务，开始普通的闲聊回复...")
    return {"messages": ["AI: 你好呀！我是一个纯聊天大模型。"]}


async def search_tool_node(state: AgentState):
    """工具节点：假装去调用了谷歌搜索 / RAAP 内部库"""
    last_msg = state["messages"][-1]
    print(f"🛠️ [工具节点] 检测到搜索需求，正在联网查询: '{last_msg}'")
    # 模拟工具调用的耗时
    await asyncio.sleep(1)
    return {"messages": ["Tool: 搜索结果显示，今天天气晴朗，适合敲代码！"]}


# ==========================================
# [LangGraph 核心 3] 定义“交警”路由器 (Router)
# ==========================================
def route_logic(state: AgentState) -> str:
    """
    这是一个普通的函数（不是节点）。
    它不修改黑板，它只负责看黑板，并大喊出下一个应该去哪个节点！
    """
    print("👮 [路由交警] 正在检查黑板，决定下一步去哪...")
    last_msg = state["messages"][-1]

    # 简单的关键字意图识别（在高级架构里，这里会让大模型来做决策）
    if "天气" in last_msg or "搜索" in last_msg:
        print("   -> 判定结果：需要调用工具！")
        return "search_tool"
    else:
        print("   -> 判定结果：只是闲聊，直接让大模型回答。")
        return "llm"


# ==========================================
# [LangGraph 核心 4] 组装带有“条件分支”的流水线
# ==========================================
async def main():
    workflow = StateGraph(AgentState)

    workflow.add_node("llm", llm_node)
    workflow.add_node("search_tool", search_tool_node)
    workflow.add_conditional_edges(START, route_logic)
    workflow.add_edge("llm", END)
    workflow.add_edge("search_tool", END)

    app = workflow.compile()

    # ==========================================
    # [修复核心] 打印并观测 Agent 的最终状态
    # ==========================================
    print("\n=== 测试 1: 普通闲聊意图 ===")
    state_1 = {"messages": ["User: 嘿，老兄，吃了吗？"]}

    # 1. 执行并拿到流水线跑完后的最终黑板
    final_state_1 = await app.ainvoke(state_1)

    # 2. 朗读黑板上的最后一条记录
    print(f"📊 [最终黑板记录]: {final_state_1['messages'][-1]}")

    print("\n=== 测试 2: 触发工具意图 ===")
    state_2 = {"messages": ["User: 帮我搜索一下今天台北的天气怎么样？"]}

    # 1. 同样，必须用变量接住 ainvoke 返回的状态
    final_state_2 = await app.ainvoke(state_2)

    # 2. 朗读黑板
    print(f"📊 [最终黑板记录]: {final_state_2['messages'][-1]}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())