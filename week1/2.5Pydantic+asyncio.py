from pydantic import BaseModel, Field
from typing import Optional


class ChatMessage(BaseModel):  # 继承BaseModel = 自动验证
    message: str = Field(..., min_length=1)  # ... = 必填，最短1字符
    temperature: float = Field(0.7, ge=0.0, le=1.0)  # 默认0.7，范围0-1
    max_tokens: Optional[int] = Field(512, ge=1)  # 可选，>=1
    user_id: int = Field(1, gt=0)


# 好数据：自动通过
good = ChatMessage(message="Hello Agent from Incheon!",user_id=1)
print(good)  # 直接打印模型，好看
print(good.model_dump())  # 转dict，API常用 {'message': '...', ...}

# 坏数据：自动报详细错！
try:
    bad1 = ChatMessage(message="")  # 太短
except Exception as e:
    print("坏1错误:", e)

try:
    bad2 = ChatMessage(message="Hi", temperature=1.5)  # 超范围
except Exception as e:
    print("坏2错误:", e)

try:
    bad3 = ChatMessage(message="Hi", max_tokens=0)  # <1
except Exception as e:
    print("坏3错误:", e)

try:
    bad3 = ChatMessage(message="Hi", max_tokens=0.7, user_id=0)  # <1
except Exception as e:
    print("坏4错误:", e)
