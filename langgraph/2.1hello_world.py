import asyncio
import aiohttp
import operator
from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, START, END


# ==========================================
# [底层设施] 你的 1.8 异步防弹调用工具
# ==========================================
async def call_ollama(prompt: str) -> str:
    url = "http://localhost:11434/api/generate"
    payload = {"model": "llama3.2:3b", "prompt": prompt, "stream": False}
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()
                return result.get("response", "")
    except Exception as e:
        return f"❌ 大模型宕机: {str(e)}"


# ==========================================
# [LangGraph 核心 1] 定义 State 黑板结构
# ==========================================
class AgentState(TypedDict):
    # 【核心魔法点】定义记忆列表，以及如何更新它
    messages: Annotated[list[str], operator.add]


# ==========================================
# [LangGraph 核心 2] 定义 Node 节点函数
# ==========================================
async def llm_node(state: AgentState):
    """大模型处理节点：读取黑板 -> 调用模型 -> 将结果写回黑板"""

    # 1. 读取黑板：获取所有的历史消息
    all_messages = state["messages"]
    # 2. 提取最新消息：列表的最后一个元素就是用户的最新提问
    user_latest_msg = all_messages[-1]

    # 3. 异步调用本地模型算力
    reply = await call_ollama(prompt=user_latest_msg)

    # 4. 写回黑板：必须返回一个字典，Key 必须与 AgentState 中定义的一致
    return {"messages": [f"AI: {reply}"]}


# ==========================================
# [LangGraph 核心 3] 组装图引擎并运行
# ==========================================
async def main():
    # 1. 实例化图纸（声明这个工厂用哪种类型的黑板）
    workflow = StateGraph(AgentState)

    # 2. 注册节点（把工人录入工厂系统）
    workflow.add_node("llm_worker", llm_node)

    # 3. 建立连接（设定传送带的流转方向）
    workflow.add_edge(START, "llm_worker")
    workflow.add_edge("llm_worker", END)

    # 4. 编译引擎（将 Python 逻辑转化为可执行的底层图对象）
    app = workflow.compile()

    # 5. 初始状态：往新黑板上写下第一句话
    initial_state = {"messages": ["User: 为什么天空是蓝色的？请用 15 个字以内回答。"]}

    # 6. 启动异步引擎，推送数据流转
    final_state = await app.ainvoke(initial_state)

    print("\n🏁 运行结束！最终的记忆黑板 (State) 内容：")
    for msg in final_state["messages"]:
        print(msg)


if __name__ == "__main__":
    asyncio.run(main())