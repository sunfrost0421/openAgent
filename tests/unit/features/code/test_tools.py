"""CodeAgent 工具单元测试"""

import pytest
import tempfile
from pathlib import Path

from src.features.code.tools import read_file, write_file, execute_code


@pytest.fixture
def temp_file():
    """创建临时文件用于测试"""
    fd, path = tempfile.mkstemp(suffix='.txt')
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")
        yield path
    finally:
        # 关闭文件句柄后删除，Windows 上需要延时或重试
        try:
            Path(path).unlink(missing_ok=True)
        except PermissionError:
            # Windows 上文件可能还被占用，忽略
            pass


@pytest.mark.asyncio
async def test_read_file_exists(temp_file):
    """测试读取已存在的文件"""
    result = await read_file.ainvoke({"path": temp_file})
    assert "Line 1" in result
    assert "Line 5" in result


@pytest.mark.asyncio
async def test_read_file_not_found():
    """测试读取不存在的文件"""
    result = await read_file.ainvoke({"path": "/nonexistent/file.txt"})
    assert "Error" in result
    assert "not found" in result


@pytest.mark.asyncio
async def test_read_file_with_lines(temp_file):
    """测试读取指定行范围"""
    result = await read_file.ainvoke({"path": temp_file, "lines": [1, 3]})
    assert "Line 2" in result
    assert "Line 3" in result
    assert "Line 1" not in result
    assert "Line 4" not in result


@pytest.mark.asyncio
async def test_write_file_new(temp_file):
    """测试写入新文件"""
    test_path = temp_file + "_new.txt"
    try:
        result = await write_file.ainvoke({
            "path": test_path,
            "content": "Test content"
        })
        assert "Successfully wrote" in result

        # 验证内容
        with open(test_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == "Test content"
    finally:
        Path(test_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_write_file_append(temp_file):
    """测试追加模式写入"""
    result = await write_file.ainvoke({
        "path": temp_file,
        "content": "\nLine 6",
        "mode": "a"
    })
    assert "Successfully wrote" in result

    # 验证内容
    with open(temp_file, 'r', encoding='utf-8') as f:
        content = f.read()
    assert "Line 5" in content
    assert "Line 6" in content


@pytest.mark.asyncio
async def test_execute_code_simple():
    """测试执行简单代码"""
    result = await execute_code.ainvoke({"code": "print('hello world')"})
    assert "hello world" in result
    assert "completed successfully" in result


@pytest.mark.asyncio
async def test_execute_code_with_error():
    """测试执行出错代码"""
    result = await execute_code.ainvoke({"code": "1/0"})
    assert "Error" in result or "STDERR" in result or "ZeroDivisionError" in result


@pytest.mark.asyncio
async def test_execute_code_timeout():
    """测试超时处理"""
    code = "import time\ntime.sleep(10)"
    result = await execute_code.ainvoke({"code": code, "timeout": 2})
    assert "timed out" in result