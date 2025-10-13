#!/bin/bash

# Build script for Rust backend with frontend
# This script builds the frontend and then the Rust backend with the frontend bundled

set -e

echo "==> Building Open WebUI Rust Backend with Frontend"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "==> Step 1: Building frontend..."
cd "$REPO_ROOT"
npm ci --force
npm run build

echo "==> Step 2: Copying frontend build to backend..."
mkdir -p "$SCRIPT_DIR/static"
cp -r "$REPO_ROOT/build/"* "$SCRIPT_DIR/static/"

echo "==> Step 3: Building Rust backend..."
cd "$SCRIPT_DIR"
cargo build --release

echo "==> Build complete!"
echo "==> Binary location: $SCRIPT_DIR/target/release/open-webui-backend"
echo "==> Frontend files: $SCRIPT_DIR/static/"
echo ""
echo "To run the backend:"
echo "  cd $SCRIPT_DIR"
echo "  STATIC_DIR=./static ./target/release/open-webui-backend"
