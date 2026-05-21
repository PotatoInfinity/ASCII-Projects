#!/bin/bash
set -e

APP_NAME="ASCII-Lens"
APP_DIR="${APP_NAME}.app"

echo "=== Cleaning old build ==="
rm -rf "$APP_DIR"

echo "=== Creating App Bundle Directory Structure ==="
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

echo "=== Copying Info.plist ==="
cp Info.plist "$APP_DIR/Contents/Info.plist"

echo "=== Compiling Swift Sources ==="
swiftc -O -o "$APP_DIR/Contents/MacOS/$APP_NAME" \
    main.swift \
    AppDelegate.swift \
    ScreenCaptureManager.swift \
    OverlayWindow.swift \
    ControllerWindow.swift \
    ASCIIFilterRenderer.swift \
    MetalShaderSource.swift \
    -framework AppKit \
    -framework Metal \
    -framework MetalKit \
    -framework ScreenCaptureKit \
    -framework CoreMedia \
    -framework CoreVideo

echo "=== Build Succeeded! ==="
echo "You can run the app with: open $APP_DIR"
