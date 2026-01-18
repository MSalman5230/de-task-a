# Load Tester for FastAPI Predict Endpoint

A high-performance load testing tool written in Go that can test your FastAPI `/predict` endpoint and measure requests per second (RPS). Also includes a Python version for comparison (Python version not fast enough to call high request per sec).


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
   ### Command Line Flags (Go version)
- `-workers <number>`: Number of concurrent workers (default: 10)
- `-duration <seconds>`: Test duration in seconds (default: 60)
- `-url <url>`: API endpoint URL (default: http://localhost:8000/predict)






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






