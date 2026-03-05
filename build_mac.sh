#!/usr/bin/env bash
# ============================================================
#  FrameExporter — macOS Build Script
#  Requires: Python 3.10+, pip
#  Produces: dist/FrameExporter.app  +  FrameExporter.dmg
# ============================================================

set -e

echo ""
echo " ==========================================="
echo "  FrameExporter  |  macOS Build Script"
echo " ==========================================="
echo ""

# ── Check Python ──────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo " [ERROR] Python 3 not found. Install from python.org or via Homebrew:"
    echo "         brew install python"
    exit 1
fi

echo " [1/5] Installing Python dependencies..."
pip3 install -r requirements.txt
pip3 install pyinstaller
echo ""

echo " [2/5] Building .app bundle with PyInstaller..."
pyinstaller \
    --onefile \
    --windowed \
    --name "FrameExporter" \
    --icon "assets/icon.icns" \
    --add-data "assets:assets" \
    main.py
echo ""

echo " [3/5] Verifying build..."
if [ ! -f "dist/FrameExporter" ] && [ ! -d "dist/FrameExporter.app" ]; then
    echo " [ERROR] Build failed — no output found in dist/"
    exit 1
fi
echo " Build OK"
echo ""

echo " [4/5] Creating DMG installer..."
# hdiutil creates a drag-and-drop DMG
APP_PATH="dist/FrameExporter.app"
DMG_NAME="FrameExporter_macOS.dmg"

# If .app doesn't exist (--onefile produces a unix binary), wrap it
if [ ! -d "$APP_PATH" ]; then
    mkdir -p dist/FrameExporter.app/Contents/MacOS
    cp dist/FrameExporter dist/FrameExporter.app/Contents/MacOS/FrameExporter
    # Minimal Info.plist
    cat > dist/FrameExporter.app/Contents/Info.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>   <string>FrameExporter</string>
  <key>CFBundleIdentifier</key>   <string>com.frameexporter.app</string>
  <key>CFBundleName</key>         <string>FrameExporter</string>
  <key>CFBundleVersion</key>      <string>1.0.0</string>
  <key>CFBundlePackageType</key>  <string>APPL</string>
  <key>LSMinimumSystemVersion</key> <string>10.13</string>
</dict>
</plist>
EOF
fi

# Create staging folder for DMG
STAGE="dist/dmg_stage"
rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -r "$APP_PATH" "$STAGE/"
ln -s /Applications "$STAGE/Applications"

hdiutil create \
    -volname "FrameExporter" \
    -srcfolder "$STAGE" \
    -ov \
    -format UDZO \
    "dist/$DMG_NAME"

rm -rf "$STAGE"

echo ""
echo " [5/5] Done!"
echo "       App:      dist/FrameExporter.app"
echo "       Installer: dist/$DMG_NAME"
echo ""
echo " Share $DMG_NAME with Mac users."
echo " They drag FrameExporter → Applications to install."
echo ""
