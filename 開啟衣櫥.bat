@echo off
chcp 65001 >nul
title 數位衣櫥 ✨

echo.
echo  ========================================
echo    ✨  啟動數位衣櫥中，請稍候...
echo  ========================================
echo.

# 🌟 修正：確保安裝的是最新的 google-genai 移民包
pip show google-genai >nul 2>&1
if %errorlevel% neq 0 (
    echo  正在安裝 2026 最新版 AI 通訊套件...
    pip install -U google-genai
    echo.
)

# 移除舊版衝突套件（如果有的話）
pip uninstall google-generativeai -y >nul 2>&1

echo  開啟瀏覽器中...
# 🌟 修正：加上 headless 參數，解決一次開啟兩個視窗的問題
start http://localhost:8501
streamlit run app.py --server.port 8501 --server.headless true
pause