# TouchSense
A mouse. The mouse. A technology here to revolutionise the mouse forever. 

This is my attempt to recreate what I saw in the Iron Man movies as a kid. 
It allows you to control your laptop using just your hands and a camera.
It uses cv2 and mediapipe to understand the gestures.

## Setup
Install the project dependencies with:

```powershell
pip install -r requirements.txt
```

Gestures:-
1) Index+Middle up, rest down: General mouse pointer
2) Pinch: Hold (to drag around objects like windows)
3) Thumbs up/down: Scroll up/down

## Executable build
To rebuild it locally, run:

```powershell
.\build_exe.ps1
```

This uses PyInstaller in one-file windowed mode and bundles MediaPipe assets with the app. The generated `build/`, `dist/`, and `*.spec` files are ignored in Git so the repository stays clean.
