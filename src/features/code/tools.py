"""CodeAgent 工具定义"""

from langchain.tools import tool
from pathlib import Path
import subprocess
import tempfile
from typing import Optional, Tuple

# 项目根目录（功能优先阶段：允许任意路径）
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


@tool
def read_file(path: str, lines: Optional[Tuple[int, int]] = None) -> str:
    """读取文件内容

    Args:
        path: 文件路径（绝对路径或相对于项目根目录）
        lines: 可选，指定行范围 (start, end)，从 0 开始计数

    Returns:
        文件内容字符串

    Example:
        >>> read_file.invoke({"path": "README.md"})
        >>> read_file.invoke({"path": "src/main.py", "lines": [0, 10]})
    """
    # 功能优先阶段：允许绝对路径
    file_path = Path(path) if Path(path).is_absolute() else PROJECT_ROOT / path

    if not file_path.exists():
        return f"Error: File not found: {path}"

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if lines:
            line_list = content.split('\n')[lines[0]:lines[1]]
            return '\n'.join(line_list)

        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def write_file(path: str, content: str, mode: str = 'w') -> str:
    """写入/创建文件

    Args:
        path: 文件路径（绝对路径或相对于项目根目录）
        content: 文件内容
        mode: 写入模式 ('w' 覆盖，'a' 追加)

    Returns:
        操作结果字符串

    Example:
        >>> write_file.invoke({"path": "output.txt", "content": "Hello World"})
        >>> write_file.invoke({"path": "log.txt", "content": "New line", "mode": "a"})
    """
    file_path = Path(path) if Path(path).is_absolute() else PROJECT_ROOT / path

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w' if mode == 'w' else 'a', encoding='utf-8') as f:
            f.write(content)

        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@tool
def execute_code(code: str, timeout: int = 30) -> str:
    """执行 Python 代码

    Args:
        code: Python 代码字符串
        timeout: 超时时间（秒），默认 30 秒

    Returns:
        执行结果（stdout/stderr 和退出码）

    Example:
        >>> execute_code.invoke({"code": "print('hello')"})
        >>> execute_code.invoke({"code": "1+1", "timeout": 10})
    """
    try:
        # 创建临时文件执行
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name

        result = subprocess.run(
            ['python', temp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_ROOT  # 在项目根目录执行
        )

        # 清理临时文件
        Path(temp_path).unlink()

        output = []
        if result.stdout:
            output.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output.append(f"STDERR:\n{result.stderr}")
        if result.returncode == 0:
            output.append("Execution completed successfully")
        else:
            output.append(f"Exit code: {result.returncode}")

        return '\n'.join(output)

    except subprocess.TimeoutExpired:
        return f"Error: Execution timed out after {timeout} seconds"
    except Exception as e:
        return f"Error: {str(e)}"


def get_all_tools():
    """获取所有工具列表

    Returns:
        工具列表 [read_file, write_file, execute_code]
    """
    return [read_file, write_file, execute_code]