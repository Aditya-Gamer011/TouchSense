$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}

if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
}

if (Test-Path "TouchSense.spec") {
    Remove-Item -Force "TouchSense.spec"
}

python -m PyInstaller `
    --noconfirm `
    --clean `
    --name TouchSense `
    --onefile `
    --windowed `
    --collect-all mediapipe `
    gesture.py
