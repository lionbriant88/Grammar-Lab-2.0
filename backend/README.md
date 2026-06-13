# Grammar Lab Grammar Service

时态分析与句子重写引擎 - Python 后端服务

## 目录结构

```
backend/
├── app.py                    # FastAPI 入口
├── requirements.txt          # 依赖清单
├── build.bat                # PyInstaller 打包脚本
├── grammar_engine/
│   ├── __init__.py
│   ├── models.py            # Pydantic 数据模型
│   └── nlp_loader.py        # spaCy 模型单例加载器
└── tests/
    └── test_health.py       # 健康检查测试
```

## 安装

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 开发模式运行

```bash
python app.py
```

服务将在 `http://127.0.0.1:18765` 启动。

## API 接口

### GET /health
健康检查，返回服务状态和模型加载情况。

### POST /api/tense/analyze
分析句子中的时态。

**请求体：**
```json
{
  "sentence": "I got up early yesterday.",
  "mode": "offline"
}
```

### POST /api/tense/rewrite
改写句子（拖拽后的时态转换）。

**请求体：**
```json
{
  "sentence": "I got up early yesterday.",
  "target_verb_id": "v1",
  "target_zone": "future",
  "scope": "single_verb",
  "preserve_aspect": true,
  "mode": "offline"
}
```

## 打包

```bash
# Windows
build.bat
```

打包后生成 `dist/grammar-service.exe`，可独立运行。

## 测试

```bash
# 启动服务后，另开一个终端
pytest tests/
# 或直接运行
python tests/test_health.py
```
