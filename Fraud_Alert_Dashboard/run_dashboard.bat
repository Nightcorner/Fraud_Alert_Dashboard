@echo off
cd /d "%~dp0"
py -m streamlit run app.py
if errorlevel 1 (
  echo.
  echo Dashboard could not start. Run install_dashboard.bat first.
  pause
)
