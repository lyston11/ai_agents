import asyncio
import operator
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END


# ==========================================
# [LangGraph 核心 1] 增强版 State 黑板
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list[str], operator.add]
    # 【企业级防呆必备】记录循环了多少次，防止大模型陷入死循环把破产！
    loop_step: int


# ==========================================
# [LangGraph 核心 2] 定义相互博弈的两个节点
# ==========================================
async def draft_node(state: AgentState):
    """打工人节点：负责写内容"""
    print("✍️ [草稿节点] 正在奋笔疾书写内容...")

    step = state.get("loop_step", 0)
    # 模拟大模型的表现：第一次敷衍了事，被骂了之后第二次才认真写
    if step == 0:
        draft = "天气不错。"
    else:
        draft = "今晚彰化市的气温凉爽，夜风徐徐，正是坐在电脑前死磕代码、冲击 40k 架构师的好时候！"

    # 注意：我们不仅追加了 message，还把 loop_step 加了 1
    return {"messages": [f"Draft: {draft}"], "loop_step": step + 1}


async def review_node(state: AgentState):
    """监工节点：负责审查质量"""
    print("🧐 [审查节点] 正在严苛地检查草稿质量...")
    # 拿到打工人刚写的草稿
    last_msg = state["messages"][-1]

    # 极简审查逻辑：字数少于 15 个字就直接打回
    if len(last_msg) < 15:
        print("   -> ❌ 审查不通过：字数太少，内容太敷衍！打回重写！")
        return {"messages": ["Reviewer: 写的太简略了，请结合当前的场景，补充更多生动的细节！"]}
    else:
        print("   -> ✅ 审查通过：细节丰富，情绪到位，准许发布！")
        return {"messages": ["Reviewer: 完美，通过审查！"]}


# ==========================================
# [LangGraph 核心 3] 控制循环的交警
# ==========================================
def route_logic(state: AgentState) -> str:
    """决定是结束，还是倒退重写"""
    last_msg = state["messages"][-1]

    # 【安全阀门】如果循环超过 3 次，强制掐断，防止死循环
    if state.get("loop_step", 0) >= 3:
        print("🚨 [安全警报] 达到最大重试次数，强制终止流水线！")
        return "end"

    # 如果监工说完美，就走向结束；否则，走向重写
    if "完美" in last_msg:
        return "end"
    else:
        return "rewrite"


# ==========================================
# [LangGraph 核心 4] 组装循环图 (Cyclic Graph)
# ==========================================
async def main():
    workflow = StateGraph(AgentState)

    workflow.add_node("drafter", draft_node)
    workflow.add_node("reviewer", review_node)

    # 起点 -> 打工人 -> 监工
    workflow.add_edge(START, "drafter")
    workflow.add_edge("drafter", "reviewer")

    # 【高能预警：闭环的诞生】
    # 监工审查完之后，交给交警 route_logic 决定去向
    workflow.add_conditional_edges(
        "reviewer",  # 1. 谁的后面接条件？
        route_logic,  # 2. 谁来做决定？
        {  # 3. 决定结果对应的真实去向字典（路由映射表）
            "rewrite": "drafter",  # 如果交警大喊 rewrite，传送带直接倒退回 drafter！
            "end": END  # 如果交警大喊 end，走向结束
        }
    )

    app = workflow.compile()

    print("\n=== 2.3 循环图：自我反思与纠错测试 ===")
    # 初始黑板：给定初始信息，并将循环计数器清零
    initial_state = {"messages": ["User: 请描述一下现在的天气和氛围。"], "loop_step": 0}

    final_state = await app.ainvoke(initial_state)

    print("\n📊 [最终黑板完整记录]:")
    for msg in final_state["messages"]:
        print("   " + msg)


if __name__ == "__main__":
    asyncio.run(main())