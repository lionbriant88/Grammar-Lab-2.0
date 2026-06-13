@echo off
REM PyInstaller 打包脚本 - Windows

echo ============================================================
echo  Grammar Lab Grammar Service - Build Script
echo ============================================================
echo.

REM 检查虚拟环境
if not exist "venv\" (
    echo [!] 虚拟环境不存在，请先运行:
    echo     python -m venv venv
    echo     venv\Scripts\activate
    echo     pip install -r requirements.txt
    pause
    exit /b 1
)

echo [1/3] 激活虚拟环境...
call venv\Scripts\activate.bat

echo.
echo [2/3] 安装/更新依赖...
pip install -r requirements.txt

echo.
echo [3/3] 使用 PyInstaller 打包...
REM --onefile: 打包为单个 exe
REM --noconsole: 不显示控制台（注释掉以便调试）
REM --clean: 每次清理缓存
pyinstaller ^
    --onefile ^
    --name grammar-service ^
    --add-data "grammar_engine;grammar_engine" ^
    --hidden-import spacy ^
    --hidden-import en_core_web_sm ^
    --hidden-import spacy.lang ^
    --hidden-import spacy.pipeline ^
    --exclude-module matplotlib ^
    --exclude-module IPython ^
    --collect-all spacy ^
    --collect-all en_core_web_sm ^
    app.py

echo.
echo ============================================================
echo  打包完成！
echo  输出文件: dist\grammar-service.exe
echo ============================================================
pause
