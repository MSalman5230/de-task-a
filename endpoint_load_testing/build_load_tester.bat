@echo off
REM Build script for load tester - creates binaries for all platforms (Windows)

echo Building load tester for all platforms...

REM Create build directory
if not exist build mkdir build

REM Build for Windows (amd64)
echo Building for Windows (amd64)...
set GOOS=windows
set GOARCH=amd64
go build -o build\test_predict_endpoint_windows_amd64.exe test_predict_endpoint.go

REM Build for Windows (arm64)
echo Building for Windows (arm64)...
set GOOS=windows
set GOARCH=arm64
go build -o build\test_predict_endpoint_windows_arm64.exe test_predict_endpoint.go

REM Build for Linux (amd64)
echo Building for Linux (amd64)...
set GOOS=linux
set GOARCH=amd64
go build -o build\test_predict_endpoint_linux_amd64 test_predict_endpoint.go

REM Build for Linux (arm64)
echo Building for Linux (arm64)...
set GOOS=linux
set GOARCH=arm64
go build -o build\test_predict_endpoint_linux_arm64 test_predict_endpoint.go

REM Build for macOS (amd64)
echo Building for macOS (amd64)...
set GOOS=darwin
set GOARCH=amd64
go build -o build\test_predict_endpoint_darwin_amd64 test_predict_endpoint.go

REM Build for macOS (arm64 - Apple Silicon)
echo Building for macOS (arm64 - Apple Silicon)...
set GOOS=darwin
set GOARCH=arm64
go build -o build\test_predict_endpoint_darwin_arm64 test_predict_endpoint.go

echo.
echo Build complete! Binaries are in the 'build' directory:
dir build
