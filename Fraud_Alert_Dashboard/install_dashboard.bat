@echo off
cd /d "%~dp0"
echo Installing dashboard dependencies...
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Installation failed. Check your Python and internet connection.
  pause
  exit /b 1
)
echo.
echo Dependencies installed successfully.
pause
