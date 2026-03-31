import asyncio
import aiohttp
import os
from typing import TypedDict, Annotated, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


# ==========================================
# [架构师绝技：自定义记忆消除棒]
# ==========================================
def memory_reducer(existing_memory: list, new_memory: list) -> list:
    if new_memory and new_memory[0].get("wipe"):
        print("\n   [底层日志] 侦测到 wipe 标记！旧记忆已被彻底清空！")
        clean_memory = [{"role": msg["role"], "content": msg["content"]} for msg in new_memory]
        return clean_memory
    return existing_memory + new_memory


class AgentState(TypedDict):
    messages: Annotated[list[Dict[str, Any]], memory_reducer]


async def llm_node(state: AgentState):
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


async def main():
    os.makedirs("db_data", exist_ok=True)
    db_path = os.path.join("db_data", "time_travel_v4.sqlite")

    async with AsyncSqliteSaver.from_conn_string(db_path) as db_saver:
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", llm_node)
        workflow.add_edge(START, "agent")
        workflow.add_edge("agent", END)
        app = workflow.compile(checkpointer=db_saver)

        # 开启全新的干净时间线 006
        thread_config = {"configurable": {"thread_id": "lyston_timeline_006"}}

        print("\n" + "=" * 50)
        print("🎬 [第一幕：建立原始时间线]")
        print("=" * 50)

        input("⏳ [系统挂起] 请按回车键，发送第一句话...")
        msg1 = {"messages": [{"role": "user", "content": "我的特工代号是『猎鹰』。收到请只回复：已确认。"}]}
        print("\n👨‍💻 [User]:", msg1["messages"][0]["content"])
        await app.ainvoke(msg1, thread_config)

        input("\n⏳ [系统挂起] 请按回车键，验证大模型...")
        msg2 = {"messages": [{"role": "user", "content": "我的特工代号是什么？请只输出代号。"}]}
        print("\n👨‍💻 [User]:", msg2["messages"][0]["content"])
        state_original = await app.ainvoke(msg2, thread_config)
        print("🤖 [Agent 原生回复]:", state_original['messages'][-1]['content'])

        print("\n" + "=" * 50)
        print("🌀 [第二幕：拉取历史快照]")
        print("=" * 50)
        input("⏳ [系统挂起] 按回车键，拉取历史切片...")

        history = []
        async for snapshot in app.aget_state_history(thread_config):
            history.append(snapshot)

        print("\n📋 历史快照列表：")
        for i, snap in enumerate(history):
            print(
                f"   [{i}] ID: {snap.config['configurable']['checkpoint_id']} | 黑板共有 {len(snap.values['messages'])} 句话")

        target_snapshot = next(s for s in history if len(s.values["messages"]) == 2)
        past_config = target_snapshot.config

        print(f"\n🎯 锁定锚点 ID: {past_config['configurable']['checkpoint_id']}")

        print("\n" + "=" * 50)
        print("⚡ [第三幕：终极篡改 (记忆消除棒)]")
        print("=" * 50)
        input("⏳ [系统挂起] 按回车键，启动记忆消除棒，物理抹除旧记忆...")

        tamper_msg = {"messages": [{
            "role": "system",
            "content": "你是极其专业的特工系统。你只知道用户的代号是『毒蛇』。如果被问及代号，只准回答毒蛇！",
            "wipe": True
        }]}

        # 【全场最核心修复】：必须接住返回的新钥匙！！！
        new_config = await app.aupdate_state(past_config, tamper_msg)

        print("\n💉 篡改完毕！旧记忆已被物理抹除，全新的系统指令已植入。")
        print(f"🔑 [时空指纹] 我们获得了平行宇宙的新钥匙: {new_config['configurable']['checkpoint_id']}")

        print("\n" + "=" * 50)
        print("🔀 [第四幕：分裂平行宇宙]")
        print("=" * 50)
        input("⏳ [系统挂起] 按回车键，拿着【全新】的钥匙发车！...")

        print("\n👨‍💻 [User]: 我的特工代号是什么？请只输出代号。 (在平行宇宙再次提问)")

        # 【全场最核心修复】：用 new_config 发车，而不是 past_config！
        state_forked = await app.ainvoke(msg2, config=new_config)

        print("\n🤯 [Agent 洗脑后回复]:", state_forked['messages'][-1]['content'])
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())