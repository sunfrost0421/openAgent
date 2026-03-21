def add(a, b):
    """
    返回两个数的和
    
    Args:
        a: 第一个数
        b: 第二个数
    
    Returns:
        两个数的和
    """
    return a + b


# 测试示例
if __name__ == "__main__":
    print(f"3 + 5 = {add(3, 5)}")
    print(f"10 + 20 = {add(10, 20)}")
    print(f"-5 + 10 = {add(-5, 10)}")
    print(f"2.5 + 3.5 = {add(2.5, 3.5)}")
