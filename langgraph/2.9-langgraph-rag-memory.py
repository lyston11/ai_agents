import asyncio
import aiohttp
import operator
import psycopg
from pgvector.psycopg import register_vector_async
from typing import TypedDict, Annotated, Dict, Any
from langgraph.graph import StateGraph, START, END

DB_URI = "postgresql://lyston:lystonagent@localhost:5432/rag_memory"


async def get_embedding(text: str) -> list[float]:
    url = "http://localhost:11434/api/embeddings"
    payload = {"model": "nomic-embed-text", "prompt": text}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            result = await resp.json()
            return result["embedding"]


async def setup_database():
    print("⚙️ [基建大队] 正在连接 PostgreSQL 并初始化 pgvector 扩展...")
    conn = await psycopg.AsyncConnection.connect(DB_URI, autocommit=True)

    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    await register_vector_async(conn)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id serial PRIMARY KEY,
            content text,
            embedding vector(768)
        )
    """)
    await conn.execute("TRUNCATE memories")

    print("🧬 [知识录入] 正在将测试记忆转化为向量并存入数据库...")
    memories = [
        "学习路线：正在按照多阶段路线图，死磕 LangGraph 底层架构和 AI Agent 开发。",
        "开发环境：日常开发主力机是 Mac，熟练使用 Python 进行复杂应用开发。",
        "底层基建：目前采用 OrbStack 替代 Docker，以极低的资源占用运行 PostgreSQL 向量数据库。"
    ]

    for m in memories:
        emb = await get_embedding(m)
        await conn.execute("INSERT INTO memories (content, embedding) VALUES (%s, %s)", (m, emb))

    await conn.close()
    print("✅ [基建完成] 向量数据库准备就绪！\n")


class AgentState(TypedDict):
    messages: Annotated[list[Dict[str, Any]], operator.add]
    long_term_context: str


async def retrieve_node(state: AgentState):
    print(f"🔍 [检索节点] 潜入 PostgreSQL 寻找相关长期记忆...")
    user_msg = state["messages"][-1]["content"]
    query_emb = await get_embedding(user_msg)

    conn = await psycopg.AsyncConnection.connect(DB_URI, autocommit=True)
    await register_vector_async(conn)

    async with conn.cursor() as cur:
        await cur.execute("SELECT content FROM memories ORDER BY embedding <=> %s::vector LIMIT 1", (query_emb,))
        row = await cur.fetchone()

    await conn.close()

    fetched_context = row[0] if row else "未检索到相关记忆。"
    print(f"   💡 [向量库返回]: 命中记忆 -> {fetched_context}")

    return {"long_term_context": fetched_context}


async def llm_node(state: AgentState):
    print("🧠 [LLM 节点] 融合长期记忆与当前对话，开始思考...")
    context = state.get("long_term_context", "")

    sys_msg = {
        "role": "system",
        "content": f"【系统背景库】你从长期数据库中检索到了以下独家信息：\n{context}\n\n请结合上述信息，直接回答用户的提问。"
    }

    final_messages = [sys_msg] + state["messages"]

    url = "http://localhost:11434/api/chat"
    payload = {"model": "llama3.2:3b", "messages": final_messages, "stream": False}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            resp.raise_for_status()
            res = await resp.json()
            return {"messages": [res["message"]]}


async def main():
    await setup_database()

    workflow = StateGraph(AgentState)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("agent", llm_node)

    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "agent")
    workflow.add_edge("agent", END)

    app = workflow.compile()

    print("=== 2.9 生产级原生 RAG 记忆检索测试 ===")

    query1 = "我平时在 Mac 上跑容器化基建，目前主要用的是什么软件？"
    print(f"\n👨‍💻 [User]: {query1}")
    state1 = await app.ainvoke({"messages": [{"role": "user", "content": query1}]})
    print(f"🤖 [Agent]: {state1['messages'][-1]['content']}")

    query2 = "为了实现我未来的职业目标，我目前的核心学习路线是什么？"
    print(f"\n👨‍💻 [User]: {query2}")
    state2 = await app.ainvoke({"messages": [{"role": "user", "content": query2}]})
    print(f"🤖 [Agent]: {state2['messages'][-1]['content']}")


if __name__ == "__main__":
    asyncio.run(main())