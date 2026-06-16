"""pytest 共享配置:把 backend 根目录加入 sys.path,使 `from grammar_engine...` 可导入。

从 backend/ 根运行:`python -m pytest tests/`
"""
import os
import sys

# backend/ 根目录(本文件的上级目录)
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)
