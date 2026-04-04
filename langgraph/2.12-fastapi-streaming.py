import os

# 强行注入本地直连免死金牌，防代理劫持
os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"

import asyncio
import json
import operator
from typing import TypedDict, Annotated, Dict, Any
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama

# 【核心修复】：导入 LangChain 的底层配置对象
from langchain_core.runnables import RunnableConfig


# ==========================================
# [一、 LangGraph 核心架构]
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list[Dict[str, Any]], operator.add]


llm = ChatOllama(model="llama3.2:3b", temperature=0.7)


# 【核心修复】：节点必须接收 config，并把它作为“麦克风”塞给大模型！
async def call_model(state: AgentState, config: RunnableConfig):
    print("\n🧠 [节点触发] 正在向模型发起请求...")
    # 把 config 传给 ainvoke，彻底打通流式事件广播通道！
    response = await llm.ainvoke(state["messages"], config)
    return {"messages": [{"role": "assistant", "content": response.content}]}


workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_edge(START, "agent")
workflow.add_edge("agent", END)
app_graph = workflow.compile()

# ==========================================
# [二、 FastAPI 生产级接入]
# ==========================================
app = FastAPI(title="raap Agent Streaming API")


async def token_generator(query: str):
    inputs = {"messages": [{"role": "user", "content": query}]}
    print(f"\n🌐 [网络通道建立] 接收到查询: {query}")

    async for event in app_graph.astream_events(inputs, version="v2"):
        kind = event["event"]

        # 拦截‘模型正在吐字’的瞬间
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                yield f"data: {json.dumps({'token': content})}\n\n"

        elif kind == "on_chain_end" and event["name"] == "LangGraph":
            print("\n✅ [网络通道关闭] 流转结束。")
            yield "data: [DONE]\n\n"


@app.get("/chat")
async def chat(query: str):
    return StreamingResponse(
        token_generator(query),
        media_type="text/event-stream"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)