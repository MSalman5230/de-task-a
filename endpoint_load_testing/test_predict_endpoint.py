"""
Load testing script for FastAPI /predict endpoint.
Runs for 1 minute and calculates requests per second (RPS).
"""
import asyncio
import time
import httpx
from typing import List, Dict
import statistics

# API endpoint configuration
API_URL = "http://localhost:8000/predict"
TEST_DURATION = 60  # 1 minute in seconds

# Sample payloads for testing
SAMPLE_PAYLOADS = [
    {
        "txn_count": 10.0,
        "total_debit": 5000.0,
        "total_credit": 3000.0,
        "avg_amount": 500.0,
        "kw_rent": 1,
        "kw_netflix": 0,
        "kw_tesco": 1,
        "kw_payroll": 1,
        "kw_bonus": 0
    },
    {
        "txn_count": 15.0,
        "total_debit": 8000.0,
        "total_credit": 5000.0,
        "avg_amount": 650.0,
        "kw_rent": 1,
        "kw_netflix": 1,
        "kw_tesco": 0,
        "kw_payroll": 1,
        "kw_bonus": 1
    },
    {
        "txn_count": 5.0,
        "total_debit": 2000.0,
        "total_credit": 1500.0,
        "avg_amount": 350.0,
        "kw_rent": 0,
        "kw_netflix": 1,
        "kw_tesco": 1,
        "kw_payroll": 0,
        "kw_bonus": 0
    },
    {
        "txn_count": 20.0,
        "total_debit": 12000.0,
        "total_credit": 8000.0,
        "avg_amount": 800.0,
        "kw_rent": 1,
        "kw_netflix": 0,
        "kw_tesco": 1,
        "kw_payroll": 1,
        "kw_bonus": 0
    },
    {
        "txn_count": 8.0,
        "total_debit": 3500.0,
        "total_credit": 2500.0,
        "avg_amount": 450.0,
        "kw_rent": 0,
        "kw_netflix": 1,
        "kw_tesco": 0,
        "kw_payroll": 1,
        "kw_bonus": 0
    }
]


class LoadTestResults:
    """Track load test results."""
    def __init__(self):
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.start_time = None
        self.end_time = None

    def add_success(self, response_time: float):
        """Record a successful request."""
        self.successful_requests += 1
        self.response_times.append(response_time)

    def add_failure(self, error: str):
        """Record a failed request."""
        self.failed_requests += 1
        self.errors.append(error)

    def get_stats(self) -> Dict:
        """Calculate and return statistics."""
        total_requests = self.successful_requests + self.failed_requests
        duration = self.end_time - self.start_time if self.end_time and self.start_time else TEST_DURATION
        
        stats = {
            "total_requests": total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "duration_seconds": duration,
            "requests_per_second": total_requests / duration if duration > 0 else 0,
            "successful_rps": self.successful_requests / duration if duration > 0 else 0,
        }
        
        if self.response_times:
            stats.update({
                "avg_response_time_ms": statistics.mean(self.response_times) * 1000,
                "min_response_time_ms": min(self.response_times) * 1000,
                "max_response_time_ms": max(self.response_times) * 1000,
                "median_response_time_ms": statistics.median(self.response_times) * 1000,
            })
            if len(self.response_times) > 1:
                stats["stddev_response_time_ms"] = statistics.stdev(self.response_times) * 1000
        else:
            stats.update({
                "avg_response_time_ms": 0,
                "min_response_time_ms": 0,
                "max_response_time_ms": 0,
                "median_response_time_ms": 0,
            })
        
        return stats


async def make_request(client: httpx.AsyncClient, payload: Dict) -> tuple[bool, float, str]:
    """Make a single request to the predict endpoint."""
    start = time.time()
    try:
        response = await client.post(API_URL, json=payload, timeout=30.0)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            return True, elapsed, ""
        else:
            return False, elapsed, f"HTTP {response.status_code}: {response.text[:100]}"
    except httpx.TimeoutException:
        elapsed = time.time() - start
        return False, elapsed, "Request timeout"
    except httpx.ConnectError:
        elapsed = time.time() - start
        return False, elapsed, "Connection error - is the API running?"
    except Exception as e:
        elapsed = time.time() - start
        return False, elapsed, f"Error: {str(e)}"


async def worker(client: httpx.AsyncClient, results: LoadTestResults, stop_event: asyncio.Event):
    """Worker coroutine that continuously makes requests until stop event is set."""
    import random
    payload_index = 0
    
    while not stop_event.is_set():
        # Rotate through sample payloads
        payload = SAMPLE_PAYLOADS[payload_index % len(SAMPLE_PAYLOADS)]
        payload_index += 1
        
        success, response_time, error = await make_request(client, payload)
        
        if success:
            results.add_success(response_time)
        else:
            results.add_failure(error)


async def run_load_test(num_workers: int = 10):
    """Run the load test for TEST_DURATION seconds."""
    print(f"Starting load test...")
    print(f"API URL: {API_URL}")
    print(f"Test duration: {TEST_DURATION} seconds")
    print(f"Number of concurrent workers: {num_workers}")
    print("-" * 60)
    
    results = LoadTestResults()
    stop_event = asyncio.Event()
    
    # First, check if API is accessible
    try:
        async with httpx.AsyncClient() as client:
            health_response = await client.get("http://localhost:8000/health", timeout=5.0)
            if health_response.status_code != 200:
                print(f"⚠️  Warning: Health check returned {health_response.status_code}")
            else:
                print("✓ API health check passed")
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        print("Make sure the API is running: uvicorn api.app:app --host 0.0.0.0 --port 8000")
        return
    
    print("\nRunning load test...")
    results.start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        # Create and start worker tasks
        tasks = [asyncio.create_task(worker(client, results, stop_event)) for _ in range(num_workers)]
        
        # Run for TEST_DURATION seconds (workers run concurrently during this time)
        await asyncio.sleep(TEST_DURATION)
        
        # Stop all workers
        stop_event.set()
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
    
    results.end_time = time.time()
    
    # Print results
    print("\n" + "=" * 60)
    print("LOAD TEST RESULTS")
    print("=" * 60)
    
    stats = results.get_stats()
    
    print(f"\n📊 Overall Statistics:")
    print(f"  Total Requests:        {stats['total_requests']:,}")
    print(f"  Successful Requests:   {stats['successful_requests']:,}")
    print(f"  Failed Requests:       {stats['failed_requests']:,}")
    print(f"  Success Rate:          {stats['success_rate']:.2f}%")
    print(f"  Test Duration:         {stats['duration_seconds']:.2f} seconds")
    
    print(f"\n⚡ Performance Metrics:")
    print(f"  Requests Per Second (RPS):     {stats['requests_per_second']:.2f}")
    print(f"  Successful RPS:                {stats['successful_rps']:.2f}")
    
    if stats['successful_requests'] > 0:
        print(f"\n⏱️  Response Time Statistics:")
        print(f"  Average Response Time:      {stats['avg_response_time_ms']:.2f} ms")
        print(f"  Median Response Time:       {stats['median_response_time_ms']:.2f} ms")
        print(f"  Min Response Time:           {stats['min_response_time_ms']:.2f} ms")
        print(f"  Max Response Time:           {stats['max_response_time_ms']:.2f} ms")
        if 'stddev_response_time_ms' in stats:
            print(f"  Std Dev Response Time:       {stats['stddev_response_time_ms']:.2f} ms")
    
    if results.errors:
        print(f"\n❌ Error Summary (showing first 10):")
        error_counts = {}
        for error in results.errors[:10]:
            error_type = error.split(':')[0] if ':' in error else error
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        for error_type, count in error_counts.items():
            print(f"  {error_type}: {count}")
    
    print("\n" + "=" * 60)
    print(f"✅ The API can handle approximately {stats['successful_rps']:.2f} requests per second")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    # Allow customizing number of workers via command line
    num_workers = 10
    if len(sys.argv) > 1:
        try:
            num_workers = int(sys.argv[1])
        except ValueError:
            print("Invalid number of workers. Using default: 10")
    
    # Allow customizing API URL via environment variable or command line
    if len(sys.argv) > 2:
        API_URL = sys.argv[2]
    
    asyncio.run(run_load_test(num_workers))
