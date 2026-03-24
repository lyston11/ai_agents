import asyncio
import aiohttp
import time
from typing import Optional, Dict, Any

async def call_ollama(
    prompt: str,
    model: str = "llama3.2:3b",
    temperature: float = 0.7,
    timeout_seconds: int = 30
) -> Optional[Dict[str, Any]]:
    """
    异步调用本地 Ollama 服务的企业级标准函数。
    """
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "stream": False 
    }

    # 设置超时时间拦截器
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    print(f"🚀 [INFO] 开始请求模型: {model}...")
    start_time = time.time()

    try:
        # 异步上下文管理器（负责自动开关网络连接）
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                
                # 状态码核查：非 200 直接抛出异常
                response.raise_for_status() 
                
                # 挂起当前协程，等待网卡数据返回
                result = await response.json()
                print(f"✅ [SUCCESS] 请求成功，耗时: {time.time() - start_time:.2f}秒")
                return result

    # 细粒度异常捕获拦截网
    except asyncio.TimeoutError:
        print(f"❌ [ERROR] 请求超时！超过了设定的 {timeout_seconds} 秒。")
    except aiohttp.ClientConnectionError:
        print("❌ [ERROR] 连接拒绝！请检查本地 Ollama 服务是否在后台运行。")
    except Exception as e:
        print(f"❌ [ERROR] 发生了未知错误: {str(e)}")
        
    # 发生异常时安全返回 None
    return None

async def main():
    print("=== 测试 1: 正常发起请求 ===")
    response = await call_ollama(prompt="作为资深工程师，用一句话描述 Python 异步的优势。")
    if response:
        print(f"🤖 模型回复: {response.get('response', '')}\n")

    print("=== 测试 2: 模拟一次会失败的请求 ===")
    await call_ollama(prompt="你好", model="fake-model:888b")

if __name__ == "__main__":
    # 启动异步事件循环引擎
    asyncio.run(main())