nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
result1 = [x ** 2 for x in nums if x % 2 == 0]
print(result1)

# 练习2：长度和首字母
words = ['apple', 'banana', 'kiwi']
result2 = [[len(word), word[0]] for word in words]
print(result2)

result3 = [x for x in range(20) if x % 3 == 0]
print(result3)
