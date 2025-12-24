@echo off
echo Creating virtual environment in .venv
python -m venv .venv
echo Upgrading pip inside venv
.venv\Scripts\python.exe -m pip install --upgrade pip
echo Installing requirements (if any)
.venv\Scripts\python.exe -m pip install -r requirements.txt
echo Done. Activate with: .\.venv\Scripts\activate.bat
