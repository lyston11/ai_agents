import time
from functools import wraps
from fastapi import FastAPI, HTTPException
from httpx import AsyncClient
from models import ChatRequest, ChatResponse

app = FastAPI(
    title="Lyston Async Ollama Agent API",
    description="异步调用本地Ollama的Agent原型",
    version="1.0"
)

# 异步日志装饰器（复习第1周）
def log_execution(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        print(f"[LOG] 开始调用 {func.__name__}")
        try:
            result = await func(*args, **kwargs)
            end = time.time()
            print(f"[LOG] 成功完成，耗时 {end - start:.2f}s")
            return result
        except Exception as e:
            end = time.time()
            print(f"[LOG] 失败: {e}，耗时 {end - start:.2f}s")
            raise HTTPException(status_code=500, detail=str(e))
    return wrapper

# 异步调用Ollama
async def call_ollama(request: ChatRequest) -> str:
    payload = {
        "model": "llama3",  # 改成你的模型，如 "qwen2:72b"
        "prompt": request.message,
        "options": {
            "temperature": request.temperature,
            "num_ctx": request.max_tokens or 512
        },
        "stream": False
    }
    async with AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json=payload
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            raise Exception(f"Ollama调用失败: {e}")

@app.post("/chat", response_model=ChatResponse)
@log_execution
async def chat(request: ChatRequest):
    reply = await call_ollama(request)
    return ChatResponse(reply=reply)

@app.get("/")
async def root():
    return {"message": "Lyston Async Ollama API 运行中！去 /docs 测试"}