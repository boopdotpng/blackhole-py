#!/bin/bash
# Build TTGPU.app (+ embedded dext), copy it to /Applications, and activate the dext. --build: build only.
set -e
cd "$(dirname "$0")"
[[ -d /Applications/Xcode.app ]] && export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"

# macOS only swaps an active dext for one with a different CFBundleVersion, so stamp every build with the time.
# It must be a valid kext version (major <= 9999, minor/patch <= 99): days since 2026-01-01 . hour . minute.
BUILD="$((($(date +%s) - 1767225600) / 86400)).$(date +%-H).$(date +%-M)"
xcodebuild -quiet -project TinyGPUDriverExtension.xcodeproj -scheme TinyGPU -configuration Debug \
  -derivedDataPath build/dd -allowProvisioningUpdates CURRENT_PROJECT_VERSION="$BUILD" build
APP=build/dd/Build/Products/Debug/TTGPU.app
codesign --verify --deep --strict "$APP"
echo "built $APP (build $(defaults read "$PWD/$APP/Contents/Info.plist" CFBundleVersion))"
[[ "$1" == "--build" ]] && exit 0

rm -rf /Applications/TTGPU.app
cp -R "$APP" /Applications/
/Applications/TTGPU.app/Contents/MacOS/TTGPU install
