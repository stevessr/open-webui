# Testing the Rust Backend

This document describes how to test the Rust backend implementation.

## Quick Start

### 1. Build the Project

```bash
cd backend-rust
cargo build --release
```

### 2. Run Tests

```bash
cargo test
```

### 3. Start the Server

```bash
./start.sh
# Or manually:
cargo run --release
```

The server will start on `http://0.0.0.0:8080` by default.

## Testing Endpoints

### Health Check

```bash
curl http://localhost:8080/health
# Expected: 200 OK (empty response)

curl http://localhost:8080/api/health
# Expected: 200 OK (empty response)
```

### Version

```bash
curl http://localhost:8080/api/version
# Expected:
# {
#   "version": "0.1.0",
#   "build": "dev-build"
# }
```

### Configuration

```bash
curl http://localhost:8080/api/config
# Expected:
# {
#   "version": "0.1.0",
#   "WEBUI_NAME": "Open WebUI",
#   "ENABLE_SIGNUP": true,
#   "DEFAULT_LOCALE": "en-US"
# }
```

## Unit Tests

### Running All Tests

```bash
cargo test
```

### Running Specific Tests

```bash
# Test JWT utilities
cargo test jwt::tests

# Test password utilities
cargo test password::tests
```

### Test Coverage

```bash
# Install tarpaulin
cargo install cargo-tarpaulin

# Generate coverage report
cargo tarpaulin --out Html
```

## Integration Tests

### Authentication Flow (To be implemented)

```bash
# 1. Sign up
curl -X POST http://localhost:8080/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "password123"
  }'

# 2. Sign in
curl -X POST http://localhost:8080/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Expected: JWT token
# {
#   "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "Bearer"
# }
```

### User Management (To be implemented)

```bash
# Get all users (requires authentication)
TOKEN="your-jwt-token-here"
curl http://localhost:8080/api/users \
  -H "Authorization: Bearer $TOKEN"

# Get specific user
curl http://localhost:8080/api/users/user-id \
  -H "Authorization: Bearer $TOKEN"
```

## Performance Testing

### Using Apache Bench

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test health endpoint
ab -n 10000 -c 100 http://localhost:8080/health

# Test version endpoint
ab -n 10000 -c 100 http://localhost:8080/api/version
```

### Using wrk

```bash
# Install wrk
sudo apt-get install wrk

# Test health endpoint
wrk -t4 -c100 -d30s http://localhost:8080/health

# Test version endpoint
wrk -t4 -c100 -d30s http://localhost:8080/api/version
```

### Expected Performance

For simple endpoints (health, version):
- **Latency**: < 1ms (p50), < 5ms (p99)
- **Throughput**: > 50,000 req/s (on modern hardware)
- **Memory**: < 50MB (idle)

## Load Testing

### Using Gatling

Create `load-test.scala`:

```scala
import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

class LoadTest extends Simulation {
  val httpProtocol = http
    .baseUrl("http://localhost:8080")
    
  val scn = scenario("API Load Test")
    .exec(http("health")
      .get("/health")
      .check(status.is(200)))
    .exec(http("version")
      .get("/api/version")
      .check(status.is(200)))
    
  setUp(
    scn.inject(
      rampUsers(1000).during(30.seconds)
    )
  ).protocols(httpProtocol)
}
```

Run:
```bash
gatling.sh -s LoadTest
```

## Stress Testing

### Memory Leak Detection

```bash
# Run with valgrind
valgrind --leak-check=full ./target/release/open-webui-backend

# Or use heaptrack
heaptrack ./target/release/open-webui-backend
```

### CPU Profiling

```bash
# Install perf
sudo apt-get install linux-tools-generic

# Profile CPU usage
sudo perf record -F 99 -g ./target/release/open-webui-backend
sudo perf report
```

## Security Testing

### SQL Injection (SQLx protects against this)

```bash
# Try SQL injection in user input
curl -X POST http://localhost:8080/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com'\'' OR 1=1--",
    "password": "anything"
  }'

# Should fail safely (not return unauthorized data)
```

### JWT Token Validation

```bash
# Try invalid token
curl http://localhost:8080/api/users \
  -H "Authorization: Bearer invalid-token"

# Expected: 401 Unauthorized

# Try expired token
curl http://localhost:8080/api/users \
  -H "Authorization: Bearer expired-token"

# Expected: 401 Unauthorized
```

## Compatibility Testing

### API Compatibility with Python Backend

Test that Rust backend returns same responses as Python backend:

```bash
# Python backend
curl http://localhost:8000/api/version > python-response.json

# Rust backend
curl http://localhost:8080/api/version > rust-response.json

# Compare
diff python-response.json rust-response.json
# Should be identical
```

## Automated Testing

### CI/CD Pipeline

Add to `.github/workflows/rust-backend.yml`:

```yaml
name: Rust Backend CI

on:
  push:
    paths:
      - 'backend-rust/**'
  pull_request:
    paths:
      - 'backend-rust/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Rust
        uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
          
      - name: Run tests
        working-directory: backend-rust
        run: cargo test
        
      - name: Build
        working-directory: backend-rust
        run: cargo build --release
        
      - name: Run clippy
        working-directory: backend-rust
        run: cargo clippy -- -D warnings
```

## Monitoring in Production

### Health Checks

```bash
# Kubernetes liveness probe
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 3
  periodSeconds: 3

# Readiness probe
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Metrics (To be implemented)

```bash
# Prometheus metrics endpoint
curl http://localhost:8080/metrics

# Expected metrics:
# - http_requests_total
# - http_request_duration_seconds
# - database_connections_active
# - memory_usage_bytes
```

## Debugging

### Logging

Set log level:
```bash
RUST_LOG=debug cargo run
```

Levels:
- `error`: Only errors
- `warn`: Warnings and errors
- `info`: General information (default)
- `debug`: Detailed debugging
- `trace`: Very detailed tracing

### Common Issues

#### Port Already in Use
```bash
# Check what's using port 8080
lsof -i :8080

# Kill the process
kill -9 <PID>
```

#### Database Connection Error
```bash
# Check database URL
echo $DATABASE_URL

# Test database connection
sqlite3 ../backend/data/webui.db ".tables"
```

#### Compilation Errors
```bash
# Clean build artifacts
cargo clean

# Rebuild
cargo build
```

## Test Checklist

Before considering implementation complete:

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] API compatibility verified
- [ ] Performance benchmarks meet targets
- [ ] Load testing shows no memory leaks
- [ ] Security testing finds no vulnerabilities
- [ ] Error handling works correctly
- [ ] Logging provides useful information
- [ ] Documentation is up to date

## Next Steps

1. Implement database operations
2. Complete authentication endpoints
3. Add comprehensive integration tests
4. Set up CI/CD pipeline
5. Deploy to staging environment
6. Monitor and iterate

## Resources

- [Rust Testing Documentation](https://doc.rust-lang.org/book/ch11-00-testing.html)
- [Axum Testing Examples](https://github.com/tokio-rs/axum/tree/main/examples)
- [SQLx Testing](https://docs.rs/sqlx/latest/sqlx/#testing)
- [Performance Testing Tools](https://github.com/wg/wrk)
