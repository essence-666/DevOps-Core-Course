package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"runtime"
	"time"
)

var startTime = time.Now()

// Structs for JSON response
type Service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Language    string `json:"language"`
}

type System struct {
	Hostname     string `json:"hostname"`
	Platform     string `json:"platform"`
	Architecture string `json:"architecture"`
	CPUCount     int    `json:"cpu_count"`
	GoVersion    string `json:"go_version"`
}

type RuntimeInfo struct {
	UptimeSeconds int64  `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

type RequestInfo struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

type MainResponse struct {
	Service   Service     `json:"service"`
	System    System      `json:"system"`
	Runtime   RuntimeInfo `json:"runtime"`
	Request   RequestInfo `json:"request"`
	Endpoints []Endpoint  `json:"endpoints"`
}

type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int64  `json:"uptime_seconds"`
}

type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
}

// Helpers
func humanDuration(d time.Duration) string {
	h := int(d.Hours())
	m := int(d.Minutes()) % 60
	s := int(d.Seconds()) % 60
	return fmt.Sprintf("%d hour(s), %d minute(s), %d second(s)", h, m, s)
}

// Logging middleware for JSON structured logging
func loggingMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Wrap response writer to capture status code
		wrapped := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}

		// Call the next handler
		next(wrapped, r)

		// Determine log level based on status code
		level := "INFO"
		if wrapped.statusCode >= 500 {
			level = "ERROR"
		} else if wrapped.statusCode >= 400 {
			level = "WARNING"
		}

		// Log the request in JSON format
		duration := time.Since(start)
		logEntry := map[string]interface{}{
			"timestamp":   time.Now().UTC().Format(time.RFC3339),
			"level":       level,
			"service":     "devops-go",
			"method":      r.Method,
			"path":        r.URL.Path,
			"status_code": wrapped.statusCode,
			"duration_ms": duration.Milliseconds(),
			"client_ip":   r.RemoteAddr,
		}

		jsonLog, _ := json.Marshal(logEntry)
		fmt.Println(string(jsonLog))
	}
}

type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// Handlers
func rootHandler(w http.ResponseWriter, r *http.Request) {
	now := time.Now()
	uptime := now.Sub(startTime)

	resp := MainResponse{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Language:    "Go",
		},
		System: System{
			Hostname:     getHostname(),
			Platform:     runtime.GOOS,
			Architecture: runtime.GOARCH,
			CPUCount:     runtime.NumCPU(),
			GoVersion:    runtime.Version(),
		},
		Runtime: RuntimeInfo{
			UptimeSeconds: int64(uptime.Seconds()),
			UptimeHuman:   humanDuration(uptime),
			CurrentTime:   now.UTC().Format(time.RFC3339),
			Timezone:      "UTC",
		},
		Request: RequestInfo{
			ClientIP:  r.RemoteAddr,
			UserAgent: r.UserAgent(),
			Method:    r.Method,
			Path:      r.URL.Path,
		},
		Endpoints: []Endpoint{
			{Path: "/", Method: "GET", Description: "Service information"},
			{Path: "/health", Method: "GET", Description: "Health check"},
			{Path: "/error", Method: "GET", Description: "Test endpoint that returns 500 error"},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	now := time.Now()
	uptime := now.Sub(startTime)

	resp := HealthResponse{
		Status:        "healthy",
		Timestamp:     now.UTC().Format(time.RFC3339),
		UptimeSeconds: int64(uptime.Seconds()),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func errorHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusInternalServerError)
	resp := ErrorResponse{
		Error:   "Internal Server Error",
		Message: "Test endpoint triggered - for error logging testing",
	}
	json.NewEncoder(w).Encode(resp)
}

// Utility
func getHostname() string {
	name, err := os.Hostname()
	if err != nil {
		return "unknown"
	}
	return name
}

// Main
func main() {
	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8001"
	}

	// Register handlers with logging middleware
	http.HandleFunc("/", loggingMiddleware(rootHandler))
	http.HandleFunc("/health", loggingMiddleware(healthHandler))
	http.HandleFunc("/error", loggingMiddleware(errorHandler))

	// Log startup in JSON format
	startupLog := map[string]interface{}{
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"level":     "INFO",
		"service":   "devops-go",
		"message":   "Starting server",
		"host":      host,
		"port":      port,
	}
	jsonLog, _ := json.Marshal(startupLog)
	fmt.Println(string(jsonLog))

	err := http.ListenAndServe(host+":"+port, nil)
	if err != nil {
		log.Printf("Server error: %v\n", err)
	}
}
