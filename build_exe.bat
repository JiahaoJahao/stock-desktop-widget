@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name StockWidget ^
  --hidden-import=pytz --hidden-import=requests stock_widget.py
echo.
echo Built: %~dp0dist\StockWidget.exe
dir "%~dp0dist\StockWidget.exe"
