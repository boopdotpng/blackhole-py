#!/bin/bash
set -e

# Check SIP status if not building only
if [[ "$1" != "--build" ]]; then
  SIP_STATUS=$(csrutil status 2>&1)
  if [[ "$SIP_STATUS" == *"enabled"* ]]; then
    echo "ERROR: System Integrity Protection (SIP) is enabled."
    echo "This dev build requires SIP to be disabled to load unsigned dexts."
    echo ""
    echo "To disable SIP:"
    echo "  1. Restart and hold Power button (M1+) or Cmd+R (Intel)"
    echo "  2. Open Terminal from Recovery menu"
    echo "  3. Run: csrutil disable"
    echo "  4. Restart"
    exit 1
  fi
fi

echo "SIP is disabled, proceeding with dev build..."

cd "$(dirname "$0")"
[[ -d /Applications/Xcode.app ]] && export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"

# Build without code signing
xcodebuild clean build CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO -alltargets -configuration Debug build

APP_PATH="./build/Debug/TTGPU.app"
DEXT_PATH="$APP_PATH/Contents/Library/SystemExtensions/com.boopapps.ttgpu.driver.dext"

# Ad-hoc sign with dev entitlements (matches any GPU)
codesign --sign - --entitlements ./TinyGPUDriverExtension/TinyGPUDriver.NoSIP.entitlements --force --timestamp --verbose "$DEXT_PATH"
codesign --sign - --entitlements ./macOS/macOS.entitlements --force --timestamp --verbose "$APP_PATH"

echo "Build complete: $APP_PATH"

if [[ "$1" == "--build" ]]; then
  exit 0
fi

# Install
echo "Installing to /Applications..."

if [ -d "/Applications/TTGPU.app" ]; then
  echo "Removing existing /Applications/TTGPU.app..."
  rm -rf "/Applications/TTGPU.app"
fi

cp -r "$APP_PATH" /Applications/
echo "Installed to /Applications/TTGPU.app"

echo "Activating driver extension..."
/Applications/TTGPU.app/Contents/MacOS/TTGPU install
