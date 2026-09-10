"""pytest 公共配置：修正导入路径并提供样例目录 fixture（任务 B5）。"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest

SAMPLE_DIR = BACKEND_DIR.parent / "sample_data"


@pytest.fixture()
def sample_dir() -> Path:
    """返回 sample_data 目录，测试用它读取脱敏简历样例。"""
    return SAMPLE_DIR
