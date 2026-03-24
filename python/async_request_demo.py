def simple_decorator(func):
    def wrapper(*args, **kwargs):  # *args接收位置参数，**kwargs接收关键字参数（超级重要！）
        print(f"🎁 开始包装，参数是: args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)  # 调用原函数，传参数
        print("🎁 包装结束")
        return result  # 返回原函数结果
    return wrapper

@simple_decorator
def add(a, b):
    return a + b

@simple_decorator
def greet(name, age=25):
    return f"Hello {name}, you are {age}!"

print(add(10, 20))  # 有返回值的
print(greet("lyston"))
print(greet("lyston", age=30))