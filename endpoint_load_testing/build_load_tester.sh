#!/bin/bash
# Build script for load tester - creates binaries for all platforms

echo "Building load tester for all platforms..."

# Create build directory
mkdir -p build

# Build for Windows (amd64)
echo "Building for Windows (amd64)..."
GOOS=windows GOARCH=amd64 go build -o build/test_predict_endpoint_windows_amd64.exe test_predict_endpoint.go

# Build for Windows (arm64)
echo "Building for Windows (arm64)..."
GOOS=windows GOARCH=arm64 go build -o build/test_predict_endpoint_windows_arm64.exe test_predict_endpoint.go

# Build for Linux (amd64)
echo "Building for Linux (amd64)..."
GOOS=linux GOARCH=amd64 go build -o build/test_predict_endpoint_linux_amd64 test_predict_endpoint.go

# Build for Linux (arm64)
echo "Building for Linux (arm64)..."
GOOS=linux GOARCH=arm64 go build -o build/test_predict_endpoint_linux_arm64 test_predict_endpoint.go

# Build for macOS (amd64)
echo "Building for macOS (amd64)..."
GOOS=darwin GOARCH=amd64 go build -o build/test_predict_endpoint_darwin_amd64 test_predict_endpoint.go

# Build for macOS (arm64 - Apple Silicon)
echo "Building for macOS (arm64 - Apple Silicon)..."
GOOS=darwin GOARCH=arm64 go build -o build/test_predict_endpoint_darwin_arm64 test_predict_endpoint.go

echo ""
echo "✅ Build complete! Binaries are in the 'build' directory:"
ls -lh build/
