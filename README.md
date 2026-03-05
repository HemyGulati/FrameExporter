# FrameExporter

**Author:** Hemy Gulati  
**GitHub:** https://github.com/HemyGulati  
**Version:** 1.0.0 — 3 March 2026  
**Licence:** MIT

Extract frames from video files at custom intervals. Exports images (JPEG or PNG) and a CSV metadata file per video. Optionally detects numbers in frames using Tesseract OCR.

---

## Features

- **Universal format support** — MP4, MOV, MKV, AVI, HEVC, MXF and anything else FFmpeg handles, via PyAV
- **Multi-video queue** — add as many videos as you like in one session
- **Custom intervals** — export every N seconds *or* every N frames
- **Per-video subfolders** — each video gets its own tidy output folder
- **CSV metadata** — filename, frame number, timestamp (seconds + HH:MM:SS)
- **Number detection (OCR)** — optionally scan frames for numbers using Tesseract
- **Image format choice** — JPG (smaller) or PNG (lossless)
- **Live progress + log** — progress bar and colour-coded log panel
- **Cancel anytime** — graceful mid-export cancellation
- **Windows 11 dark UI** — Fluent Design colour palette and rounded controls

---

## Project Structure

```
FrameExporter/
├── main.py               ← Application source code
├── requirements.txt      ← Python package dependencies
├── build_windows.bat     ← Windows build + installer script
├── build_mac.sh          ← macOS build + DMG creator
├── installer.iss         ← Inno Setup script (Windows installer)
├── LICENSE.txt
├── assets/
│   └── icon.ico          ← Application icon (included)
└── README.md
```

---

## Quick Start — Run from Source

Works on Windows, macOS, and Linux.

### 1 — Prerequisites

- **Python 3.10 or newer** — https://www.python.org/downloads/
  - On Windows: tick ✅ **"Add Python to PATH"** during install

### 2 — Install dependencies

```bash
pip install av Pillow numpy pytesseract
```

Or using the requirements file:

```bash
pip install -r requirements.txt
```

| Package | Purpose |
|---------|---------|
| `av` (PyAV) | Video decoding — supports all FFmpeg formats (MP4, MOV, MKV, HEVC…) |
| `Pillow` | Saving frames as JPEG or PNG |
| `numpy` | Array operations |
| `pytesseract` | Python wrapper for Tesseract OCR |

### 3 — (Optional) Install Tesseract for number detection

Only needed if you want OCR. If using the built Windows installer, **skip this — Tesseract is bundled and installed automatically.**

**Windows (manual / dev):**
Download and run from: https://github.com/UB-Mannheim/tesseract/wiki

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt install tesseract-ocr
```

### 4 — Run

```bash
python main.py
```

---

## Building the Windows Installer

This produces a single `FrameExporter_Setup.exe` that end users double-click to install — no Python required on their machine. The installer silently bundles and installs Tesseract OCR automatically.

### Step 1 — Build the executable

Double-click `build_windows.bat` or run in a terminal:

```cmd
build_windows.bat
```

This will:
1. Locate Python automatically
2. Install all Python dependencies
3. Download the Tesseract installer into `assets/`
4. Bundle everything into `dist/FrameExporter.exe` with the app icon
5. Auto-compile the installer if Inno Setup is already installed

### Step 2 — Compile the installer (if not auto-compiled)

1. Download **Inno Setup** (free): https://jrsoftware.org/isinfo.php
2. Open `installer.iss` in Inno Setup Compiler
3. Press `Ctrl+F9`
4. Installer saved to: `installer_output/FrameExporter_Setup.exe`

### What the end-user installer does

- Welcome screen explaining what FrameExporter is
- Choose install location
- Silently installs Tesseract OCR in the background (no popups)
- Adds Tesseract to PATH automatically
- Creates a Start Menu shortcut with the app icon
- Optional desktop shortcut
- Offers to launch immediately after install
- Full uninstaller in Control Panel

### App icon

The `assets/icon.ico` file is included in the project and contains the icon at multiple resolutions (16×16, 32×32, 48×48, 256×256). It is automatically applied to:
- The `.exe` file (shown in File Explorer and taskbar)
- The Start Menu shortcut
- The desktop shortcut
- The Control Panel uninstaller entry

---

## Building the macOS Installer

```bash
chmod +x build_mac.sh
./build_mac.sh
```

Produces `dist/FrameExporter_macOS.dmg` — drag-to-install format.

---

## Using the App

### 1. Add Videos
Click **＋ Add Videos** and select one or more video files.

Supported formats (anything FFmpeg handles): `.mp4` `.mov` `.avi` `.mkv` `.wmv` `.flv` `.webm` `.m4v` `.mxf` `.ts` `.mts` `.3gp` `.hevc` `.h265` `.vob` and more.

### 2. Select Output Folder
Click **Browse** to choose where exported frames are saved. A subfolder is created automatically for each video:

```
OutputFolder/
├── MyVideo1/
│   ├── MyVideo1_f0000000.jpg
│   ├── MyVideo1_f0000025.jpg
│   └── MyVideo1_frames.csv
└── MyVideo2/
    └── ...
```

### 3. Configure Settings

| Setting | Description |
|---------|-------------|
| Export interval | `1` second = one frame per second; `30` frames = every 30th frame |
| Image format | JPG (smaller, lossy) or PNG (lossless, larger) |
| Number detection | Enable OCR to extract numbers from each frame into the CSV |

### 4. Click Start Export

Progress is shown in the bar and log. Click **Cancel** to stop gracefully at any time.

### 5. Review the CSV

Each video folder contains a CSV:

| filename | frame_number | timestamp | timestamp_hms | numbers_detected |
|----------|-------------|-----------|---------------|-----------------|
| vid_f0000000.jpg | 0 | 0.000 | 00:00:00 | |
| vid_f0000025.jpg | 25 | 1.000 | 00:00:01 | 42; 7 |

`numbers_detected` only appears when OCR is enabled.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: av` | Run `pip install av` |
| `ModuleNotFoundError: PIL` | Run `pip install Pillow` |
| OCR checkbox is greyed out | Install Tesseract (see above) and ensure it is on PATH |
| Video won't open | Verify the file plays in VLC — if it does, it should work here |
| Installer won't build | Make sure `build_windows.bat` completed without errors first |
| App icon not showing on .exe | Ensure `assets/icon.ico` exists before running PyInstaller |
| App won't launch on Mac | Run `xattr -cr /Applications/FrameExporter.app` to clear quarantine |

---

## Editing in VS Code

Open the project folder:

```bash
code .
```

Recommended extensions:
- **Python** — `ms-python.python`
- **Pylance** — `ms-python.vscode-pylance`

Select your Python interpreter (`Ctrl+Shift+P` → **Python: Select Interpreter**), then press `F5` to run.

---

## Licence

MIT — see LICENSE.txt  
Copyright © 2026 Hemy Gulati
