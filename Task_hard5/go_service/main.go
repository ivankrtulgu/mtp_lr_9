package main

import (
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"os"
	"strconv"
)

// Response represents the JSON response
type Response struct {
	Count uint64 `json:"count"`
}

// ErrorResponse represents an error response
type ErrorResponse struct {
	Error string `json:"error"`
}

// isPrime checks if a number is prime using trial division up to sqrt(n)
func isPrime(n uint64) bool {
	if n < 2 {
		return false
	}
	if n == 2 {
		return true
	}
	if n%2 == 0 {
		return false
	}

	limit := uint64(math.Sqrt(float64(n)))
	for i := uint64(3); i <= limit; i += 2 {
		if n%i == 0 {
			return false
		}
	}
	return true
}

// countPrimes counts prime numbers in range [2, n]
func countPrimes(n uint64) uint64 {
	var count uint64 = 0
	for num := uint64(2); num <= n; num++ {
		if isPrime(num) {
			count++
		}
	}
	return count
}

// handleCount handles the /count endpoint
func handleCount(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusMethodNotAllowed)
		json.NewEncoder(w).Encode(ErrorResponse{Error: "Method not allowed"})
		return
	}

	// Parse query parameter n
	nStr := r.URL.Query().Get("n")
	if nStr == "" {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(ErrorResponse{Error: "Missing required parameter 'n'"})
		return
	}

	n, err := strconv.ParseUint(nStr, 10, 64)
	if err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(ErrorResponse{Error: "Invalid parameter 'n': " + err.Error()})
		return
	}

	result := countPrimes(n)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(Response{Count: result})
}

// handleHealth handles the /health endpoint
func handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	http.HandleFunc("/count", handleCount)
	http.HandleFunc("/health", handleHealth)

	addr := ":" + port
	fmt.Printf("Go server starting on %s\n", addr)
	fmt.Printf("Endpoint: GET http://localhost:%s/count?n=1000000\n", port)

	if err := http.ListenAndServe(addr, nil); err != nil {
		fmt.Fprintf(os.Stderr, "Server error: %v\n", err)
		os.Exit(1)
	}
}
