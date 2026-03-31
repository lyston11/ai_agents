import asyncio
import aiohttp
import operator
import json
from typing import TypedDict, Annotated, Dict, Any
from langgraph.graph import StateGraph, START, END


class AgentState(TypedDict):
    messages: Annotated[list[Dict[str, Any]], operator.add]
    next_agent: str


async def supervisor_node(state: AgentState):
    print("\n🧠 [包工头 Supervisor] 正在统筹全局，决定下一步动作...")
    sys_prompt = """你是开发团队的包工头。团队有两个小弟：
1. 'coder': 负责编写 Python 代码。
2. 'researcher': 负责解答云原生、k9s 等理论问题。

根据对话历史分配任务。严格输出 JSON 格式：
{"next": "coder" 或 "researcher" 或 "FINISH"}"""

    final_messages = [{"role": "system", "content": sys_prompt}] + state["messages"]

    # 【核心修复 1】：末端强注射 (Tail Injection)
    if state["messages"] and "交付】" in state["messages"][-1]["content"]:
        # 在整个对话的绝对末尾，强行塞入一个最高优先级的 User 指令
        final_messages.append({
            "role": "user",
            "content": "【系统绝对指令】：检测到小弟刚刚已经提交了最终产出！不要做任何二次分析，不要分配给其他人，立刻、马上输出 {\"next\": \"FINISH\"} ！"
        })

    url = "http://localhost:11434/api/chat"
    payload = {"model": "llama3.2:3b", "messages": final_messages, "stream": False, "format": "json"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            res = await resp.json()
            try:
                decision = json.loads(res["message"]["content"])
                next_action = decision.get("next", "FINISH")
            except:
                next_action = "FINISH"
            print(f"   🎯 [包工头决策]: 下一步交由 -> {next_action}")
            return {"next_agent": next_action}


async def coder_node(state: AgentState):
    print("   👨‍💻 [Coder 小弟] 收到！正在疯狂手撕 Python 代码...")
    sys_prompt = "你是顶级 Python 开发专家。只输出高质的代码和极简注释。如果任务无需代码，请直接回复『此任务无需代码』，绝不输出空白！"
    final_messages = [{"role": "system", "content": sys_prompt}] + state["messages"]
    url = "http://localhost:11434/api/chat"
    payload = {"model": "llama3.2:3b", "messages": final_messages, "stream": False}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            res = await resp.json()
            result_msg = res["message"]["content"]
            if not result_msg.strip():
                result_msg = "（系统拦截：Coder 生成了空内容，强行阻断幻觉）"
            print(f"\n      📄 [Coder 产出明细]:\n{result_msg}\n")
            return {"messages": [{"role": "assistant", "content": f"【Coder 交付】\n{result_msg}"}]}


async def researcher_node(state: AgentState):
    print("   🔬 [Researcher 小弟] 收到！正在检索云原生与 k9s 手册...")
    # 【核心修复 2】：给 Researcher 加上防哑巴装甲
    sys_prompt = "你是云原生架构师。请给出专业的 Kubernetes/k9s 解答。如果任务与云原生完全无关，请直接回复『此任务非我专业』，绝不输出空白！"
    final_messages = [{"role": "system", "content": sys_prompt}] + state["messages"]
    url = "http://localhost:11434/api/chat"
    payload = {"model": "llama3.2:3b", "messages": final_messages, "stream": False}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            res = await resp.json()
            result_msg = res["message"]["content"]
            # 【核心修复 3】：增加空包弹物理拦截
            if not result_msg.strip():
                result_msg = "（系统拦截：Researcher 生成了空内容，强行阻断幻觉）"
            print(f"\n      📄 [Researcher 产出明细]:\n{result_msg}\n")
            return {"messages": [{"role": "assistant", "content": f"【Researcher 交付】\n{result_msg}"}]}


def router(state: AgentState) -> str:
    next_step = state.get("next_agent", "FINISH")
    if next_step == "coder":
        return "coder"
    elif next_step == "researcher":
        return "researcher"
    else:
        return "end"


async def main():
    workflow = StateGraph(AgentState)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("researcher", researcher_node)

    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges("supervisor", router, {"coder": "coder", "researcher": "researcher", "end": END})
    workflow.add_edge("coder", "supervisor")
    workflow.add_edge("researcher", "supervisor")

    app = workflow.compile()
    print("=== 2.10 生产级多智能体团队启动 ===")

    query1 = "帮我用 Python 写一个极简的计算两个数最大公约数的函数。"
    print(f"\n👨‍💼 [Boss (User)]: {query1}")
    await app.ainvoke({"messages": [{"role": "user", "content": query1}]})

    print("\n" + "=" * 50)

    query2 = "我在本地 kind 集群里怎么用 k9s 快速看某个 Pod 的报错日志？"
    print(f"\n👨‍💼 [Boss (User)]: {query2}")
    await app.ainvoke({"messages": [{"role": "user", "content": query2}]})


if __name__ == "__main__":
    asyncio.run(main())