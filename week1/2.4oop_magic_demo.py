from typing import Optional


class Dog:
    def __init__(self, name):  # 初始化
        self.name = name  # 属性

    def bark(self):  # 方法
        return "Woof!"


d = Dog("Buddy")
print(d.name)  # Buddy
print(d.bark())  # Woof!


class AgentTool:
    def __init__(self, name: str, version: str = "1.0"):  # 自动调用
        self.name = name
        self.version = version
        print(f"🛠️ 工具创建成功: {self.name} v{self.version}")

    def __str__(self):  # print时自动调用
        return f"[AgentTool] {self.name} (version {self.version}) - Ready!"

    # 普通方法
    def describe(self):
        return f"This is {self.name} tool."


# 创建对象
tool = AgentTool("RAGRetriever", "2.0")  # 自动__init__

print(tool)  # 自动__str__，好看！

print(tool.describe())  # 普通调用


class MemoryBank:
    def __init__(self, memories):
        self.memories = memories  # 列表

    def __len__(self):
        return len(self.memories)


mb = MemoryBank(["记忆1", "记忆2", "记忆3"])
print(len(mb))  # 自动调用__len__ → 3


class AgentTool:
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return f"Tool: {self.name}"

    def __call__(self, input_data: str) -> str:  # 魔术核心
        print(f"🔧 {self.name} 被调用，处理输入: {input_data}")
        return f"[{self.name} 输出] Processed: {input_data.upper()}"


# 创建
tool = AgentTool("Summarizer")

print(tool)  # __str__

# 像函数调用！
result1 = tool("hello agent")  # 自动__call__
print(result1)

result2 = tool("lyston in Singapore")
print(result2)


class ChatAgent():
    def __init__(self, name: str, location: str = "singapore") -> None:
        self.name = name
        self.location = location

    def __str__(self) -> str:
        return f"ChatAgent:{self.name} from {self.location}"

    def __call__(self, message: str) -> str:
        return f"{self.name} replies: {message} (from{self.location})"


agent  = ChatAgent("lyston")
print(agent)
print(agent("Hello teacher"))
print(agent("I'm learning OOP"))

