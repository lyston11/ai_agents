import time
from functools import wraps  # 导入这个，保持原函数信息

def log_execution(func):
    @wraps(func)  # 重要！不加的话，func.__name__会错
    def wrapper(*args, **kwargs):
        start = time.time()
        print(f"[LOG] 开始执行函数: {func.__name__}")
        print(f"     参数: args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        end = time.time()
        print(f"[LOG] 执行结束，耗时: {end - start:.2f}秒")
        print(f"     结果: {result}")
        return result
    return wrapper

@log_execution
def add(a, b):
    time.sleep(1)  # 模拟LLM调用慢
    return a + b

@log_execution
def greet(name: str) -> str:
    return f"Hello {name} from Incheon!"


def count_calls(func):
    count = 0
    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal count
        count+= 1
        print(f"[COUNT]{func.__name__}被调用了{count}次")
        return func(*args, **kwargs)
    return wrapper


@count_calls
@log_execution
def test():
    print("[TEST]")

if __name__ == "__main__":
    add(100, 200)
    greet("lyston")
    test()
    test()