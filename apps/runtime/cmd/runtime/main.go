package main

import (
	"log"
	"os"
	"strconv"
	"time"

	"github.com/your-org/dsl-hub-runtime/internal/scheduler"
)

func main() {
	inbox := getenv("RUNTIME_INBOX", "/queue/inbox")
	outbox := getenv("RUNTIME_OUTBOX", "/queue/outbox")
	poll := getenvInt("POLL_INTERVAL_MS", 500)

	rt := scheduler.New(inbox, outbox, time.Duration(poll)*time.Millisecond)
	if err := rt.Run(); err != nil {
		log.Fatalf("runtime error: %v", err)
	}
}

func getenv(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}
func getenvInt(k string, def int) int {
	if v := os.Getenv(k); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			return n
		}
	}
	return def
}
