#!/bin/bash
### COMMON SETUP; DO NOT MODIFY ###
set -e

# --- CONFIGURE THIS SECTION ---
# Replace this with your command to run all tests
run_all_tests() {
  echo "Running all tests..."

  # Baseline stub for the "before" run. When the harness runs the test
  # suite before injecting codebase.zip, /app has no fluenthttp package,
  # so `go test` would fail at the compile stage and emit zero
  # --- PASS/FAIL/SKIP lines. To give every test a concrete FAILED
  # status on the baseline, drop a stub package into /app if and only
  # if no real fluenthttp.go is already present. Every test entry point
  # (StartServer and NewClient) calls t.Fatalf so tests fail cleanly
  # through the standard testing API — no panics, no stack traces, just
  # `--- FAIL:` lines that parsing.py records as FAILED. Other stub
  # methods are never reached because t.Fatalf terminates the goroutine.
  # When codebase.zip is later extracted, unzip -o overwrites these
  # stub files with the agent's real implementation.
  if [ ! -f /app/fluenthttp.go ]; then
    cat > /app/go.mod <<'GOMOD'
module fluenthttp

go 1.21
GOMOD
    cat > /app/fluenthttp.go <<'GOSTUB'
package fluenthttp

import (
	"net/http"
	"testing"
)

type TestServer struct{ URL string }

func (s *TestServer) Close() {}

type Client struct{}

func StartServer(t *testing.T, h http.Handler) (*TestServer, *Client) {
	t.Fatalf("fluenthttp: stub — not implemented")
	return nil, nil
}

func NewClient(t *testing.T, baseURL string) *Client {
	t.Fatalf("fluenthttp: stub — not implemented")
	return nil
}

type Request struct{}

func (c *Client) Get(path string) *Request    { return nil }
func (c *Client) Post(path string) *Request   { return nil }
func (c *Client) Put(path string) *Request    { return nil }
func (c *Client) Patch(path string) *Request  { return nil }
func (c *Client) Delete(path string) *Request { return nil }

func (r *Request) WithHeader(key, value string) *Request { return nil }
func (r *Request) WithCookie(c *http.Cookie) *Request    { return nil }
func (r *Request) WithBody(body any) *Request            { return nil }
func (r *Request) Expect() *Expectation                  { return nil }

type Expectation struct{}

func (e *Expectation) Status(code int) *Expectation                   { return nil }
func (e *Expectation) HeaderMatches(key, pattern string) *Expectation { return nil }
func (e *Expectation) Cookie(name, value string) *Expectation         { return nil }
func (e *Expectation) BodyMatches(pattern string) *Expectation        { return nil }
func (e *Expectation) JSON() *JSONAssertion                           { return nil }

type JSONAssertion struct{}

func (j *JSONAssertion) HasField(path string) *JSONAssertion               { return nil }
func (j *JSONAssertion) FieldEquals(path string, value any) *JSONAssertion { return nil }
func (j *JSONAssertion) FieldMatches(path, pattern string) *JSONAssertion  { return nil }
func (j *JSONAssertion) IsArray() *JSONAssertion                           { return nil }
func (j *JSONAssertion) Length(n int) *JSONAssertion                       { return nil }
GOSTUB
  fi

  # The fluenthttp codebase lives at /app and the test suite lives at
  # /eval_assets. We create a throw-away Go module inside /eval_assets whose
  # sole purpose is to provide a compilation unit for the *_test.go files
  # shipped in tests.zip while pulling the package under test from /app via
  # a local replace directive. This lets the test files import "fluenthttp"
  # even though the code under test sits in a separate directory, and it
  # keeps /app completely free of any test files.
  cd /eval_assets

  if [ ! -f go.mod ]; then
    cat > go.mod <<'GOMOD'
module fluenthttp_tests

go 1.21

require fluenthttp v0.0.0-00010101000000-000000000000

replace fluenthttp => /app
GOMOD
  fi

  # Run the full Go test suite. We intentionally tolerate a non-zero exit so
  # the harness can capture output even when individual tests fail or when
  # the codebase hasn't been injected yet (the "before" run).
  go test -v ./... || true
}
# --- END CONFIGURATION SECTION ---

### COMMON EXECUTION; DO NOT MODIFY ###
run_all_tests
