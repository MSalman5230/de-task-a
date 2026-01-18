# Load Tester for FastAPI Predict Endpoint

A high-performance load testing tool written in Go that can test your FastAPI `/predict` endpoint and measure requests per second (RPS). Also includes a Python version for comparison.

## Why Go?

- **Fast**: Much faster than Python for concurrent HTTP requests
- **Single Binary**: No dependencies, just one executable file
- **Easy Distribution**: Cross-compile to all platforms easily
- **Zero Dependencies**: Uses only Go standard library

## Quick Start

### Option 1: Use Pre-built Binary

1. Download the binary for your platform from the `build/` directory
2. Run it:
   ```bash
   # Windows (default: 10 workers, 60 seconds)
   test_predict_endpoint_windows_amd64.exe
   
   # Linux (default: 10 workers, 60 seconds)
   ./test_predict_endpoint_linux_amd64
   
   # macOS (default: 10 workers, 60 seconds)
   ./test_predict_endpoint_darwin_arm64
   
   # With custom arguments (50 workers, 120 seconds)
   test_predict_endpoint_windows_amd64.exe -workers 50 -duration 30 -url http://localhost:8000/predict
   ```

### Option 2: Build from Source

1. **Install Go** (if not already installed):
   - Download from: https://go.dev/dl/
   - Or use package manager: `brew install go`, `apt install golang`, etc.

2. **Build for your platform**:
   ```bash
   # Windows
   go build -o test_predict_endpoint.exe test_predict_endpoint.go
   
   # Linux/macOS
   go build -o test_predict_endpoint test_predict_endpoint.go
   ```

3. **Build for all platforms** (cross-compilation):
   ```bash
   # On Windows
   build_load_tester.bat
   
   # On Linux/macOS
   chmod +x build_load_tester.sh
   ./build_load_tester.sh
   ```

## Usage

### Go Version (Recommended)

```bash
# Default: 10 workers, 60 seconds, http://localhost:8000/predict
./test_predict_endpoint

# Custom options
./test_predict_endpoint -workers 50 -duration 120 -url http://localhost:8000/predict
```

### Python Version

```bash
# Default: 10 workers, 60 seconds
python test_predict_endpoint.py

# Custom number of workers
python test_predict_endpoint.py 50

# Custom workers and URL
python test_predict_endpoint.py 50 http://localhost:8000/predict
```

### Command Line Flags (Go version)
- `-workers <number>`: Number of concurrent workers (default: 10)
- `-duration <seconds>`: Test duration in seconds (default: 60)
- `-url <url>`: API endpoint URL (default: http://localhost:8000/predict)

## Example Output

```
Starting load test...
API URL: http://localhost:8000/predict
Test duration: 60 seconds
Number of concurrent workers: 10
------------------------------------------------------------
✓ API health check passed

Running load test...

============================================================
LOAD TEST RESULTS
============================================================

📊 Overall Statistics:
  Total Requests:        125,430
  Successful Requests:   125,430
  Failed Requests:       0
  Success Rate:          100.00%
  Test Duration:         60.12 seconds

⚡ Performance Metrics:
  Requests Per Second (RPS):     2085.83
  Successful RPS:                2085.83

⏱️  Response Time Statistics:
  Average Response Time:      4.78 ms
  Median Response Time:       4.52 ms
  Min Response Time:          2.15 ms
  Max Response Time:          45.32 ms

============================================================
✅ The API can handle approximately 2085.83 requests per second
============================================================
```

## Performance Comparison

- **Python version**: ~300-350 RPS (limited by GIL and async overhead)
- **Go version**: ~2000-2300 RPS (depending on API response time) Limited by Unicorn.
                  ~21000-22000 RPS with Gunicorn 4 worker with 13900k

## Success Criteria

A request is considered successful only if:
1. HTTP status code is 200
2. Response is valid JSON
3. JSON contains a `"prediction"` field
4. `"prediction"` value is exactly `0` or `1`

## Requirements

- Go 1.19+ (only if building Go version from source)
- Python 3.8+ with httpx (only if using Python version)
- FastAPI server running on the target endpoint

## Cross-Compilation

Go makes it extremely easy to build binaries for all platforms from a single machine:

```bash
# Windows (amd64)
GOOS=windows GOARCH=amd64 go build -o test_predict_endpoint_windows.exe test_predict_endpoint.go

# Linux (amd64)
GOOS=linux GOARCH=amd64 go build -o test_predict_endpoint_linux test_predict_endpoint.go

# macOS (arm64 - Apple Silicon)
GOOS=darwin GOARCH=arm64 go build -o test_predict_endpoint_macos test_predict_endpoint.go
```

The build scripts (`build_load_tester.sh` and `build_load_tester.bat`) automate this for all common platforms.

## Files

- `test_predict_endpoint.go` - Go load tester (recommended)
- `test_predict_endpoint.py` - Python load tester
- `build_load_tester.sh` - Build script for Linux/macOS
- `build_load_tester.bat` - Build script for Windows
- `README.md` - This file

## Notes

- The tool sends requests as fast as possible (no artificial delays)
- It uses connection pooling for better performance
- All statistics are thread-safe and accurate
- The tool will check API health before starting the test
- The Go version includes a pause at the end so you can see results before the window closes
