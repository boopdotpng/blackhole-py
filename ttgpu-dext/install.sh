#!/bin/bash
# Build TTGPU.app + the dext signed with your Apple Development team, install to /Applications and activate.
# SIP stays on. Needs full Xcode signed in to an account on the team (Xcode > Settings > Accounts).
set -e
cd "$(dirname "$0")"
[[ -d /Applications/Xcode.app ]] && export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"

xcodebuild -project TinyGPUDriverExtension.xcodeproj -scheme TinyGPU -configuration Debug \
  -derivedDataPath build/dd -allowProvisioningUpdates build

APP_PATH="./build/dd/Build/Products/Debug/TTGPU.app"
codesign --verify --deep --strict "$APP_PATH"
echo "Build complete: $APP_PATH"
[[ "$1" == "--build" ]] && exit 0

rm -rf /Applications/TTGPU.app
cp -R "$APP_PATH" /Applications/
echo "Installed to /Applications/TTGPU.app, activating driver extension..."
/Applications/TTGPU.app/Contents/MacOS/TTGPU install
