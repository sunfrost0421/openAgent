"""Pytest 全局配置 - 添加 src 到 Python 路径"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
