# Async Ollama Agent API

## 项目描述

这是一个异步 FastAPI 应用，演示了如何使用异步编程调用本地 Ollama 模型。项目包含以下核心特性：

- **异步 FastAPI**：使用 `async/await` 实现非阻塞的 API 端点
- **本地 Ollama 调用**：通过 `httpx.AsyncClient` 异步调用本地 Ollama 服务
- **Pydantic 数据校验**：使用 Pydantic 模型进行请求/响应的数据验证
- **日志装饰器**：自定义异步日志装饰器，记录每个请求的执行时间和状态

## 项目结构

```
async-api-demo/
├── main.py           # FastAPI 应用主文件
├── models.py         # Pydantic 数据模型
├── requirements.txt  # 项目依赖
└── README.md         # 项目文档
```

## 运行步骤

### 1. 确保 Ollama 服务已启动

```bash
# 启动 Ollama 服务（如果还没启动）
ollama serve

# 确保已下载模型（例如 llama3）
ollama pull llama3
```

Ollama 默认运行在 `http://localhost:11434`

### 2. 安装依赖

```bash
cd week1/async-api-demo
pip install -r requirements.txt
```

主要依赖：
- `fastapi` - 现代异步 Web 框架
- `httpx` - 支持异步的 HTTP 客户端
- `pydantic` - 数据验证和设置管理
- `uvicorn` - ASGI 服务器

### 3. 启动服务

```bash
uvicorn main:app --reload --port 8000
```

服务启动后访问：
- API 根路径：http://localhost:8000
- Swagger 文档：http://localhost:8000/docs
- ReDoc 文档：http://localhost:8000/redoc

### 4. 测试 API

#### 方式 1：使用 Swagger UI

1. 打开 http://localhost:8000/docs
2. 点击 `POST /chat` 端点
3. 点击 "Try it out"
4. 输入测试数据：
```json
{
  "message": "你好，请介绍一下Python的异步编程",
  "max_tokens": 512,
  "temperature": 0.7
}
```
5. 点击 "Execute" 查看响应

#### 方式 2：使用 curl

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "解释什么是异步编程",
    "max_tokens": 512,
    "temperature": 0.7
  }'
```

## 截图示例

### Swagger UI 界面
![Swagger UI](screenshots/swagger.png)

访问 `/docs` 可以看到：
- 清晰的 API 文档
- 交互式测试界面
- 请求/响应的数据模型展示
- 自动生成的 OpenAPI 规范

### 日志输出示例

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
[LOG] 开始调用 chat
[LOG] 成功完成，耗时 3.42s
INFO:     127.0.0.1:54321 - "POST /chat HTTP/1.1" 200 OK
```

日志装饰器会记录：
- 函数开始执行的时间
- 执行是否成功或失败
- 实际执行耗时（秒）

## 为什么使用异步？

### 1. **避免阻塞，提高并发能力**

在同步模型中，当调用 Ollama API 时（通常需要几秒钟），服务器线程会被阻塞，无法处理其他请求。异步模型可以在等待 I/O 操作时释放控制权，处理其他请求。

**同步 vs 异步对比：**

```python
# 同步版本（阻塞）
def chat_sync():
    response = requests.post(...)  # 阻塞 3 秒
    return response.json()
# 10 个并发请求 = 30 秒（串行执行）

# 异步版本（非阻塞）
async def chat_async():
    async with AsyncClient() as client:
        response = await client.post(...)  # 不阻塞其他请求
        return response.json()
# 10 个并发请求 ≈ 3 秒（并发执行）
```

### 2. **支持并发工具调用**

在 Agent 系统中，经常需要并发调用多个工具：
- 同时查询数据库、调用 API、读取文件
- 并行执行多个 LLM 调用
- 同时处理多个用户请求

异步编程让这些操作可以并发执行，而不是串行等待：

```python
# 并发调用多个工具
async def agent_workflow():
    # 3 个工具同时执行，总耗时 ≈ max(t1, t2, t3)
    results = await asyncio.gather(
        call_database(),      # 耗时 1s
        call_search_api(),    # 耗时 2s
        call_llm()           # 耗时 3s
    )
    # 总耗时约 3s，而不是 6s
```

### 3. **更好的资源利用**

- **同步**：100 个并发用户 = 需要 100 个线程 = 高内存开销
- **异步**：100 个并发用户 = 1 个事件循环 = 低内存开销

异步 I/O 让单个线程可以高效处理成千上万的并发连接。

### 4. **实际应用场景**

在 AI Agent 开发中，异步特别重要：
- ✅ 等待 LLM 响应时不阻塞（通常需要几秒）
- ✅ 并发调用多个工具/API
- ✅ 实时流式响应（WebSocket）
- ✅ 处理高并发用户请求
- ✅ 集成外部服务（数据库、搜索、向量库等）

## 技术要点

### Pydantic 数据验证

```python
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)  # 必填，最少1个字符
    max_tokens: Optional[int] = Field(512, ge=1, le=8192)  # 范围验证
    temperature: float = Field(0.7, ge=0.0, le=1.0)  # 浮点数范围
```

自动提供：
- 类型检查和转换
- 数据验证（范围、长度等）
- 自动生成 OpenAPI 文档
- 清晰的错误信息

### 异步日志装饰器

```python
def log_execution(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        print(f"[LOG] 开始调用 {func.__name__}")
        try:
            result = await func(*args, **kwargs)  # 注意 await
            print(f"[LOG] 成功完成，耗时 {end - start:.2f}s")
            return result
        except Exception as e:
            print(f"[LOG] 失败: {e}")
            raise
    return wrapper
```

关键点：
- 装饰器本身返回异步函数
- 使用 `await` 调用被装饰的函数
- 保留原函数的元数据（`@wraps`）

## 扩展建议

1. **添加流式响应**：使用 `stream=True` 和 `StreamingResponse`
2. **工具调用系统**：集成多个并发工具
3. **向量数据库**：添加 RAG（检索增强生成）
4. **对话历史**：添加会话管理和上下文记忆
5. **认证授权**：添加 API key 验证
6. **错误重试**：添加自动重试机制

## 相关学习资源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Python asyncio 文档](https://docs.python.org/3/library/asyncio.html)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [Ollama API 文档](https://github.com/ollama/ollama/blob/main/docs/api.md)

## License

MIT
