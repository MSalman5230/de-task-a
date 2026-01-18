package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"sync"
	"sync/atomic"
	"time"
)

// Configuration
var (
	apiURL      = "http://localhost:8000/predict"
	testDuration = 60 * time.Second
	numWorkers   = 10
)

// Sample payloads for testing
var samplePayloads = []map[string]interface{}{
	{
		"txn_count":    10.0,
		"total_debit":  5000.0,
		"total_credit": 3000.0,
		"avg_amount":  500.0,
		"kw_rent":      1,
		"kw_netflix":   0,
		"kw_tesco":     1,
		"kw_payroll":   1,
		"kw_bonus":     0,
	},
	{
		"txn_count":    15.0,
		"total_debit":  8000.0,
		"total_credit": 5000.0,
		"avg_amount":  650.0,
		"kw_rent":      1,
		"kw_netflix":   1,
		"kw_tesco":     0,
		"kw_payroll":   1,
		"kw_bonus":     1,
	},
	{
		"txn_count":    5.0,
		"total_debit":  2000.0,
		"total_credit": 1500.0,
		"avg_amount":  350.0,
		"kw_rent":      0,
		"kw_netflix":   1,
		"kw_tesco":     1,
		"kw_payroll":   0,
		"kw_bonus":     0,
	},
	{
		"txn_count":    20.0,
		"total_debit":  12000.0,
		"total_credit": 8000.0,
		"avg_amount":  800.0,
		"kw_rent":      1,
		"kw_netflix":   0,
		"kw_tesco":     1,
		"kw_payroll":   1,
		"kw_bonus":     0,
	},
	{
		"txn_count":    8.0,
		"total_debit":  3500.0,
		"total_credit": 2500.0,
		"avg_amount":  450.0,
		"kw_rent":      0,
		"kw_netflix":   1,
		"kw_tesco":     0,
		"kw_payroll":   1,
		"kw_bonus":     0,
	},
}

// Statistics tracking
type Stats struct {
	successfulRequests int64
	failedRequests     int64
	responseTimes      []time.Duration
	responseTimesMutex sync.Mutex
	errors             []string
	errorsMutex        sync.Mutex
	startTime          time.Time
	endTime            time.Time
}

func (s *Stats) addSuccess(responseTime time.Duration) {
	atomic.AddInt64(&s.successfulRequests, 1)
	s.responseTimesMutex.Lock()
	s.responseTimes = append(s.responseTimes, responseTime)
	s.responseTimesMutex.Unlock()
}

func (s *Stats) addFailure(errorMsg string) {
	atomic.AddInt64(&s.failedRequests, 1)
	s.errorsMutex.Lock()
	if len(s.errors) < 10 {
		s.errors = append(s.errors, errorMsg)
	}
	s.errorsMutex.Unlock()
}

func (s *Stats) getResults() map[string]interface{} {
	totalRequests := s.successfulRequests + s.failedRequests
	duration := s.endTime.Sub(s.startTime).Seconds()

	results := map[string]interface{}{
		"total_requests":      totalRequests,
		"successful_requests": s.successfulRequests,
		"failed_requests":     s.failedRequests,
		"duration_seconds":    duration,
	}

	if totalRequests > 0 {
		results["success_rate"] = float64(s.successfulRequests) / float64(totalRequests) * 100
		results["requests_per_second"] = float64(totalRequests) / duration
		results["successful_rps"] = float64(s.successfulRequests) / duration
	} else {
		results["success_rate"] = 0.0
		results["requests_per_second"] = 0.0
		results["successful_rps"] = 0.0
	}

	s.responseTimesMutex.Lock()
	if len(s.responseTimes) > 0 {
		var total time.Duration
		min := s.responseTimes[0]
		max := s.responseTimes[0]
		for _, rt := range s.responseTimes {
			total += rt
			if rt < min {
				min = rt
			}
			if rt > max {
				max = rt
			}
		}
		avg := total / time.Duration(len(s.responseTimes))
		results["avg_response_time_ms"] = float64(avg.Nanoseconds()) / 1e6
		results["min_response_time_ms"] = float64(min.Nanoseconds()) / 1e6
		results["max_response_time_ms"] = float64(max.Nanoseconds()) / 1e6
		results["median_response_time_ms"] = float64(s.responseTimes[len(s.responseTimes)/2].Nanoseconds()) / 1e6
	} else {
		results["avg_response_time_ms"] = 0.0
		results["min_response_time_ms"] = 0.0
		results["max_response_time_ms"] = 0.0
		results["median_response_time_ms"] = 0.0
	}
	s.responseTimesMutex.Unlock()

	return results
}

func makeRequest(client *http.Client, payload map[string]interface{}) (bool, time.Duration, string) {
	start := time.Now()
	
	jsonData, err := json.Marshal(payload)
	if err != nil {
		return false, time.Since(start), fmt.Sprintf("JSON marshal error: %v", err)
	}

	req, err := http.NewRequest("POST", apiURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return false, time.Since(start), fmt.Sprintf("Request creation error: %v", err)
	}
	
	req.Header.Set("Content-Type", "application/json")

	resp, err := client.Do(req)
	elapsed := time.Since(start)
	
	if err != nil {
		return false, elapsed, fmt.Sprintf("Request error: %v", err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	
	if resp.StatusCode == 200 {
		// Parse JSON response and validate it contains "prediction": 0 or 1
		var result map[string]interface{}
		if err := json.Unmarshal(body, &result); err != nil {
			return false, elapsed, fmt.Sprintf("Invalid JSON response: %v", err)
		}
		
		// Check if prediction field exists and is 0 or 1
		if prediction, ok := result["prediction"]; ok {
			// Handle both float64 (from JSON) and int types
			var predValue float64
			switch v := prediction.(type) {
			case float64:
				predValue = v
			case int:
				predValue = float64(v)
			case int64:
				predValue = float64(v)
			default:
				return false, elapsed, fmt.Sprintf("Invalid prediction type: %T", prediction)
			}
			
			if predValue == 0 || predValue == 1 {
				return true, elapsed, ""
			}
			return false, elapsed, fmt.Sprintf("Prediction value is %v, expected 0 or 1", predValue)
		}
		return false, elapsed, "Response missing 'prediction' field"
	}
	
	bodyStr := string(body)
	if len(bodyStr) > 100 {
		bodyStr = bodyStr[:100]
	}
	return false, elapsed, fmt.Sprintf("HTTP %d: %s", resp.StatusCode, bodyStr)
}

func worker(client *http.Client, stats *Stats, stopChan <-chan struct{}, wg *sync.WaitGroup) {
	defer wg.Done()
	
	payloadIndex := 0
	
	for {
		select {
		case <-stopChan:
			return
		default:
			payload := samplePayloads[payloadIndex%len(samplePayloads)]
			payloadIndex++
			
			success, responseTime, errorMsg := makeRequest(client, payload)
			
			if success {
				stats.addSuccess(responseTime)
			} else {
				stats.addFailure(errorMsg)
			}
		}
	}
}

func checkHealth() bool {
	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Get("http://localhost:8000/health")
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	return resp.StatusCode == 200
}

func main() {
	flag.StringVar(&apiURL, "url", "http://localhost:8000/predict", "API endpoint URL")
	flag.IntVar(&numWorkers, "workers", 10, "Number of concurrent workers")
	durationFlag := flag.Int("duration", 60, "Test duration in seconds")
	flag.Parse()
	
	testDuration = time.Duration(*durationFlag) * time.Second

	fmt.Println("Starting load test...")
	fmt.Printf("API URL: %s\n", apiURL)
	fmt.Printf("Test duration: %.0f seconds\n", testDuration.Seconds())
	fmt.Printf("Number of concurrent workers: %d\n", numWorkers)
	fmt.Println("------------------------------------------------------------")

	if !checkHealth() {
		fmt.Println("❌ Error connecting to API")
		fmt.Println("Make sure the API is running: uvicorn api.app:app --host 0.0.0.0 --port 8000")
		return
	}
	fmt.Println("✓ API health check passed")

	fmt.Println("\nRunning load test...")
	fmt.Println("\nWait for", testDuration.Seconds(), "seconds to finish the test...")
	
	stats := &Stats{
		startTime: time.Now(),
	}
	
	client := &http.Client{
		Timeout: 30 * time.Second,
		Transport: &http.Transport{
			MaxIdleConns:        100,
			MaxIdleConnsPerHost: 100,
			IdleConnTimeout:     90 * time.Second,
		},
	}
	
	stopChan := make(chan struct{})
	var wg sync.WaitGroup
	
	// Start workers
	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go worker(client, stats, stopChan, &wg)
	}
	
	// Run for test duration
	time.Sleep(testDuration)
	
	// Stop all workers
	close(stopChan)
	wg.Wait()
	
	stats.endTime = time.Now()
	
	// Print results
	fmt.Println("\n" + "============================================================")
	fmt.Println("LOAD TEST RESULTS")
	fmt.Println("============================================================")
	
	results := stats.getResults()
	
	fmt.Printf("\n📊 Overall Statistics:\n")
	fmt.Printf("  Total Requests:        %d\n", int64(results["total_requests"].(int64)))
	fmt.Printf("  Successful Requests:   %d\n", int64(results["successful_requests"].(int64)))
	fmt.Printf("  Failed Requests:       %d\n", int64(results["failed_requests"].(int64)))
	fmt.Printf("  Success Rate:          %.2f%%\n", results["success_rate"].(float64))
	fmt.Printf("  Test Duration:         %.2f seconds\n", results["duration_seconds"].(float64))
	
	fmt.Printf("\n⚡ Performance Metrics:\n")
	fmt.Printf("  Requests Per Second (RPS):     %.2f\n", results["requests_per_second"].(float64))
	fmt.Printf("  Successful RPS:                %.2f\n", results["successful_rps"].(float64))
	
	if stats.successfulRequests > 0 {
		fmt.Printf("\n⏱️  Response Time Statistics:\n")
		fmt.Printf("  Average Response Time:      %.2f ms\n", results["avg_response_time_ms"].(float64))
		fmt.Printf("  Median Response Time:       %.2f ms\n", results["median_response_time_ms"].(float64))
		fmt.Printf("  Min Response Time:          %.2f ms\n", results["min_response_time_ms"].(float64))
		fmt.Printf("  Max Response Time:          %.2f ms\n", results["max_response_time_ms"].(float64))
	}
	
	if len(stats.errors) > 0 {
		fmt.Printf("\n❌ Error Summary (showing first 10):\n")
		errorCounts := make(map[string]int)
		for _, err := range stats.errors {
			errorType := err
			if idx := len(err); idx > 50 {
				errorType = err[:50]
			}
			errorCounts[errorType]++
		}
		for errorType, count := range errorCounts {
			fmt.Printf("  %s: %d\n", errorType, count)
		}
	}
	
	fmt.Println("\n" + "============================================================")
	fmt.Printf("✅ The API can handle approximately %.2f requests per second\n", results["successful_rps"].(float64))
	fmt.Println("============================================================")
	
	// Pause before closing (so user can see results)
	fmt.Print("\nPress Enter to exit...")
	bufio.NewReader(os.Stdin).ReadBytes('\n')
}
