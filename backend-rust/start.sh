#!/bin/bash
# Quick start script for Rust backend

set -e

echo "🦀 Starting Open WebUI Rust Backend..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and set WEBUI_SECRET_KEY before running in production!"
fi

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "❌ Cargo not found. Please install Rust from https://rustup.rs/"
    exit 1
fi

# Build in release mode
echo "🔨 Building in release mode..."
cargo build --release

# Run the server
echo "🚀 Starting server..."
./target/release/open-webui-backend
