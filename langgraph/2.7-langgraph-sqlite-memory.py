import asyncio
import aiohttp
import operator
import os  # 【新增】用来做操作系统的文件和目录管理
from typing import TypedDict, Annotated, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


# ==========================================
# [LangGraph 核心] 状态图纸与打工人
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list[Dict[str, Any]], operator.add]


async def llm_node(state: AgentState):
    print("🧠 [LLM 节点] 正在读取硬盘里的记忆，并思考回复...")

    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "llama3.2:3b",
        "messages": state["messages"],
        "stream": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            response.raise_for_status()
            result = await response.json()
            return {"messages": [result["message"]]}


# ==========================================
# [引擎启动] 组装带有硬盘记忆的流水线
# ==========================================
async def main():
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", llm_node)
    workflow.add_edge(START, "agent")
    workflow.add_edge("agent", END)

    # ==========================================
    # 【架构师操作：规范化持久层目录】
    # ==========================================
    # 1. 定义子目录的名称（比如叫 db_data）
    db_directory = "db_data"

    # 2. 【核心防御】如果文件夹不存在，自动创建它 (exist_ok=True 表示如果已经存在就不报错)
    os.makedirs(db_directory, exist_ok=True)

    # 3. 完美拼接出文件路径：db_data/lyston_memory.sqlite
    db_path = os.path.join(db_directory, "lyston_memory.sqlite")

    print(f"📁 [系统初始化] 数据库将安全保存在: {db_path}")

    # 4. 把安全路径交给底层的 Saver
    async with AsyncSqliteSaver.from_conn_string(db_path) as db_saver:

        app = workflow.compile(checkpointer=db_saver)

        print("\n=== 2.7 企业级持久化记忆测试 (输入 'quit' 退出) ===")
        config = {"configurable": {"thread_id": "lyston_prod_001"}}

        while True:
            user_input = input("\n👨‍💻 [User]: ")
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 结束会话，但你的记忆已永久封存在数据库中！")
                break

            initial_state = {"messages": [{"role": "user", "content": user_input}]}
            final_state = await app.ainvoke(initial_state, config=config)

            print(f"🤖 [Agent]: {final_state['messages'][-1]['content']}")


if __name__ == "__main__":
    asyncio.run(main())