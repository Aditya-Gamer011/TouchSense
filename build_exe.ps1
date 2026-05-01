$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

python -m PyInstaller `
    --noconfirm `
    --clean `
    --name TouchSense `
    --onefile `
    --windowed `
    --collect-all mediapipe `
    gesture.py
