import asyncio
import aiohttp
import json
from typing import TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END


# ==========================================
# [核心武器] 打造极其严格的 Pydantic 模具
# ==========================================
class UserProfile(BaseModel):
    name: str = Field(description="用户的姓名")
    is_student: bool = Field(description="是否是学生（如本科、研究生等）")
    major: str = Field(description="用户的专业领域，如果没提就填 'Unknown'")
    current_focus: list[str] = Field(description="用户目前正在钻研的技术栈或焦点，提取为列表")


# ==========================================
# [LangGraph 核心] 状态图纸与提取节点
# ==========================================
class AgentState(TypedDict):
    user_input: str
    # 用来存放最终提取出来的干净字典
    extracted_profile: dict | None


async def extract_node(state: AgentState):
    print("🧠 [提取节点] 正在阅读文本，并强制按 Pydantic 模具输出 JSON...")

    url = "http://localhost:11434/api/chat"

    # 【高能魔法】将 Python 的 Pydantic 模型，一键翻译成大模型听得懂的 JSON Schema
    strict_schema = UserProfile.model_json_schema()

    payload = {
        "model": "llama3.2:3b",
        "messages": [{"role": "user", "content": f"请提取以下文本中的人物信息：{state['user_input']}"}],
        # 【绝对核心】戴上紧箍咒！强迫大模型按此格式输出，不准说废话！
        "format": strict_schema,
        "stream": False
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()

                # 拿到大模型的回复
                ai_msg = result["message"]["content"]

                # 因为加了 format 紧箍咒，这里拿到的绝对是干净的 JSON 字符串，直接 load！
                parsed_dict = json.loads(ai_msg)
                print(f"   ✅ [解析成功] 拿到完美字典！")

                return {"extracted_profile": parsed_dict}

    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return {"extracted_profile": None}


# ==========================================
# [引擎启动] 组装极简图纸
# ==========================================
async def main():
    workflow = StateGraph(AgentState)

    workflow.add_node("extractor", extract_node)
    workflow.add_edge(START, "extractor")
    workflow.add_edge("extractor", END)

    app = workflow.compile()

    print("\n=== 2.5 结构化输出强制约束 真机实战 ===")

    # 模拟一段极其口语化的用户输入
    test_text = "大家好，我是 Lyston，目前是个 CS 研究生。我最近白天在实习写 Python，晚上熬夜死磕 LangGraph 和多智能体架构，希望能早日拿到 Remote Offer！"

    initial_state = {"user_input": test_text, "extracted_profile": None}

    final_state = await app.ainvoke(initial_state)

    print("\n📊 [最终 State 里提取出的纯净数据]:")
    # 美化打印最终的字典
    print(json.dumps(final_state["extracted_profile"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())