#!/usr/bin/env pwsh
$Venv = ".venv"
Write-Host "Creating virtual environment at $Venv"
python -m venv $Venv
Write-Host "Upgrading pip in venv"
& "$Venv\Scripts\python.exe" -m pip install --upgrade pip
Write-Host "Installing requirements (if any)"
& "$Venv\Scripts\python.exe" -m pip install -r requirements.txt
Write-Host "Done. Activate with: .\$Venv\Scripts\Activate.ps1"
