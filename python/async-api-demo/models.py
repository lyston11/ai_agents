from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户消息，必填")
    max_tokens: Optional[int] = Field(512, ge=1, le=8192, description="最大tokens")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="温度0-1")

class ChatResponse(BaseModel):
    reply: str