# 偶数生成器
def even_numbers(n):
    for i in range(n):
        if i % 2 == 0:
            yield i


for e in even_numbers(10):
    print(e, end=' ')
print("\n")

# 无限斐波那契
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

fib = fibonacci()
for _ in range(10):
    print(next(fib), end=' ')
print("\n")

# 练习3：生成器表达式
words = ['apple', 'banana', 'kiwi', 'watermelon']
long_upper = (word.upper() for word in words if len(word) > 5)
for w in long_upper:
    print(w)  # BANANA WATERMELON
    print("\n")
