import asyncio
import operator
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver


# ==========================================
# [一、 状态黑板定义]
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list[str], operator.add]
    approved: bool  # 【新增】核心鉴权标记


# ==========================================
# [二、 业务节点]
# ==========================================
async def planner_node(state: AgentState):
    print("\n🧠 [AI 规划大脑] 收到用户需求，正在分析环境与代码差异...")
    await asyncio.sleep(1)  # 模拟 AI 思考耗时
    print("   ↳ 制定计划：即将对 raap 核心集群执行高危的替换部署。")
    return {"messages": ["【系统日志】AI 申请执行高危操作：集群覆写部署。"]}


async def execute_node(state: AgentState):
    # 【高危节点】执行前，严格检查黑板上的鉴权标记
    if not state.get("approved", False):
        print("\n❌ [执行引擎] 物理拦截！黑板上缺乏人类最高授权，拒绝执行销毁指令！")
        return {"messages": ["【系统日志】操作已被人类否决。"]}

    print("\n🔥 [执行引擎] 授权通过！正在连接生产集群，执行毁灭性覆写...")
    await asyncio.sleep(1)
    print("   ↳ 部署成功！线上服务已更新。")
    return {"messages": ["【系统日志】高危部署已圆满完成！"]}


# ==========================================
# [三、 引擎启动与断点配置]
# ==========================================
async def main():
    workflow = StateGraph(AgentState)
    workflow.add_node("planner", planner_node)
    workflow.add_node("execute", execute_node)

    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "execute")
    workflow.add_edge("execute", END)

    # 【基建大队】：想要冻结时间，必须有记忆存档点
    memory = MemorySaver()

    # 【全场最核心】：编译引擎时，在 execute 节点前强行埋下地雷！
    app = workflow.compile(
        checkpointer=memory,
        interrupt_before=["execute"]  # <-- 物理刹车片
    )

    # 锁定当前宇宙的时间线
    config = {"configurable": {"thread_id": "raap_prod_deployment_001"}}

    print("=== 2.11 生产级断点拦截 (HITL) 启动 ===")
    print("\n👨‍💼 [User]: 帮我把最新的架构代码推到生产环境。")

    # [第一阶段：发车，直到触发断点]
    await app.ainvoke({"messages": ["用户发起部署指令"]}, config)

    # [第二阶段：侦测系统挂起状态]
    snapshot = app.get_state(config)
    print(f"\n⏸️  [底层内核] 引擎已强行挂起！")
    print(f"   ↳ 引擎指针卡在门外，等待进入的节点是: {snapshot.next}")

    # [第三阶段：人类插手，篡改时空]
    user_input = input("\n⚠️ [人类最高指挥官] AI 申请覆写线上集群，是否批准？(y/n): ")

    if user_input.lower() == 'y':
        # 动用上帝视角，给黑板强行写入批准标记
        app.update_state(config, {"approved": True})
        print("\n✅ 指挥官已授予最高权限，正在释放引擎刹车...")
    else:
        # 动用上帝视角，写入拒绝标记
        app.update_state(config, {"approved": False})
        print("\n🚫 指挥官已拒绝，正在通知下游节点取消行动...")

    # [第四阶段：重新点火，恢复流转]
    # 注意：传入 None，代表不需要新输入，只需引擎从刚才挂起的地方继续跑！
    final_state = await app.ainvoke(None, config)

    print(f"\n🏁 [最终黑板记录]: {final_state['messages'][-1]}")


if __name__ == "__main__":
    asyncio.run(main())