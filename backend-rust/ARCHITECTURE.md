# Rust Backend Architecture

## Overview

This document describes the architecture of the Open WebUI Rust backend, designed to be a high-performance, memory-safe alternative to the Python backend.

## Design Principles

1. **API Compatibility**: Maintain 100% compatibility with existing Python backend API
2. **Performance**: Optimize for speed and low memory usage
3. **Safety**: Leverage Rust's type system and memory safety guarantees
4. **Maintainability**: Clear separation of concerns and modular design
5. **Testability**: Easy to test individual components

## Architecture Layers

### 1. HTTP Server Layer (Axum)

**Location**: `src/main.rs`

The entry point of the application, responsible for:
- Server initialization
- Route registration
- Middleware setup
- Application state management
- Error handling

**Key Components**:
- `AppState`: Shared application state (config, database pool, Redis connection)
- Router: Main router combining all sub-routers
- Middleware: CORS, compression, authentication

### 2. Router Layer

**Location**: `src/routers/*`

Implements API endpoints organized by functional area:

- `auth.rs`: Authentication endpoints (signin, signup, signout)
- `users.rs`: User management endpoints
- `chats.rs`: Chat operations
- `models.rs`: Model management
- `ollama.rs`: Ollama integration (to be implemented)
- `openai.rs`: OpenAI integration (to be implemented)
- ... more to come

**Responsibilities**:
- Request validation
- Business logic orchestration
- Response formatting
- Error handling

**Pattern**:
```rust
async fn endpoint_handler(
    State(state): State<AppState>,
    Path(id): Path<String>,
    Json(payload): Json<RequestType>,
    Extension(claims): Extension<Claims>,  // For authenticated routes
) -> Result<Json<ResponseType>, AppError> {
    // 1. Validate input
    // 2. Call business logic
    // 3. Format response
}
```

### 3. Model Layer

**Location**: `src/models/*`

Defines data structures and database schemas:

- `users.rs`: User and related structures
- `auth.rs`: Authentication structures
- `chats.rs`: Chat structures
- `messages.rs`: Message structures
- `models.rs`: Model structures

**Responsibilities**:
- Data structure definitions
- Serialization/deserialization
- Database mapping
- Business logic methods

**Pattern**:
```rust
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Model {
    pub id: String,
    // ... fields
}

impl Model {
    pub fn new(...) -> Self { ... }
    pub fn validate(&self) -> Result<()> { ... }
}
```

### 4. Database Layer

**Location**: To be implemented in `src/database.rs`

Handles all database interactions:

- Connection pooling
- Query execution
- Transaction management
- Migration support

**Pattern**:
```rust
pub async fn get_user_by_id(
    pool: &PgPool,
    id: &str,
) -> Result<Option<User>> {
    sqlx::query_as::<_, User>(
        "SELECT * FROM users WHERE id = $1"
    )
    .bind(id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::DatabaseError(e.to_string()))
}
```

### 5. Utility Layer

**Location**: `src/utils/*`

Common utility functions:

- `jwt.rs`: JWT token creation and validation
- `password.rs`: Password hashing and verification
- `errors.rs`: Error types and handling

**Pattern**:
```rust
pub fn utility_function(input: &str) -> Result<Output> {
    // Implementation
}
```

### 6. Middleware Layer

**Location**: `src/middleware/*`

Request/response processing:

- `auth.rs`: Authentication middleware

**Pattern**:
```rust
pub async fn middleware(
    State(state): State<AppState>,
    mut req: Request,
    next: Next,
) -> Result<Response, StatusCode> {
    // Pre-processing
    let response = next.run(req).await;
    // Post-processing
    Ok(response)
}
```

## Data Flow

### Request Processing Flow

```
Client Request
    ↓
[HTTP Server] - Receives request
    ↓
[Middleware] - Authentication, logging, etc.
    ↓
[Router] - Routes to appropriate handler
    ↓
[Handler] - Validates request, extracts data
    ↓
[Business Logic] - Processes request
    ↓
[Database Layer] - Reads/writes data
    ↓
[Response] - Formats and returns response
    ↓
Client
```

### Authentication Flow

```
Client Request with Token
    ↓
[Auth Middleware]
    ↓
Extract Bearer token from headers
    ↓
[JWT Utility] - Verify token
    ↓
Extract Claims (user_id, email, role)
    ↓
Add Claims to request extensions
    ↓
[Handler] - Access Claims via Extension
    ↓
Process authenticated request
```

## State Management

### Application State

```rust
#[derive(Clone)]
pub struct AppState {
    config: Arc<AppConfig>,
    db: PgPool,              // To be added
    redis: RedisPool,        // To be added
}
```

- `Arc<AppConfig>`: Shared, immutable configuration
- `PgPool`: Database connection pool (thread-safe)
- `RedisPool`: Redis connection pool (thread-safe)

### Request State

- **Extensions**: Store per-request data (e.g., authenticated user claims)
- **Path/Query Parameters**: Extracted by Axum
- **Request Body**: Deserialized into structs

## Error Handling

### Error Types

```rust
pub enum AppError {
    DatabaseError(String),
    AuthError(String),
    TokenError(String),
    ValidationError(String),
    NotFound(String),
    Forbidden(String),
    InternalError(String),
    BadRequest(String),
}
```

### Error Flow

1. Error occurs in business logic or database
2. Convert to `AppError` using `?` operator or `map_err`
3. `AppError` implements `IntoResponse`
4. Automatically converted to HTTP response

## Configuration Management

### Environment Variables

Configuration loaded from:
1. `.env` file (development)
2. Environment variables (production)
3. Default values (fallback)

### Configuration Structure

```rust
pub struct AppConfig {
    // Server
    pub host: String,
    pub port: u16,
    
    // Authentication
    pub webui_secret_key: String,
    pub enable_signup: bool,
    
    // Database
    pub database_url: String,
    
    // External services
    pub ollama_base_url: String,
    pub openai_api_key: Option<String>,
    
    // ... more fields
}
```

## Database Schema

The Rust backend uses the same database schema as the Python backend, ensuring compatibility.

### Key Tables

- `user`: User accounts
- `auth`: Authentication credentials
- `chat`: Chat conversations
- `message`: Chat messages
- `model`: Model configurations
- `file`: Uploaded files
- `prompt`: Saved prompts
- ... and more

## Security Considerations

### Authentication

- JWT tokens with expiration
- Secure password hashing (Argon2)
- Token validation on protected routes

### Input Validation

- Type checking at compile time
- Runtime validation for complex rules
- SQL injection prevention (parameterized queries)

### CORS

- Configurable CORS policy
- Restricted in production

## Performance Optimizations

### Async/Await

- Non-blocking I/O operations
- Efficient concurrency with Tokio

### Connection Pooling

- Database connection pooling with SQLx
- Redis connection pooling

### Serialization

- Fast JSON serialization with Serde
- Zero-copy deserialization where possible

### Memory Management

- Efficient memory usage with Rust's ownership
- Minimal allocations
- Stack allocation for small types

## Testing Strategy

### Unit Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_function() {
        // Test implementation
    }
}
```

### Integration Tests

```rust
#[tokio::test]
async fn test_endpoint() {
    // Setup test server
    // Make request
    // Assert response
}
```

### Test Database

- Use in-memory SQLite for tests
- Mock external services
- Isolated test data

## Deployment

### Docker

```dockerfile
# Multi-stage build
FROM rust:1.75-slim as builder
# Build application
FROM debian:bookworm-slim
# Runtime
```

### Environment Variables

Required:
- `DATABASE_URL`: Database connection string
- `WEBUI_SECRET_KEY`: JWT secret

Optional:
- `REDIS_URL`: Redis connection
- `OLLAMA_BASE_URL`: Ollama API
- `OPENAI_API_KEY`: OpenAI API

## Migration from Python

### Compatibility

The Rust backend maintains API compatibility:
- Same endpoints
- Same request/response formats
- Same database schema

### Gradual Migration

1. Start with core endpoints
2. Add features incrementally
3. Run both backends in parallel
4. Gradually shift traffic to Rust
5. Deprecate Python backend

## Monitoring and Logging

### Logging

```rust
use tracing::{info, warn, error};

info!("Server started on {}", addr);
error!("Failed to connect to database: {}", err);
```

### Metrics

To be implemented:
- Request count
- Response times
- Error rates
- Database query times

## Future Enhancements

1. **Metrics**: Prometheus metrics endpoint
2. **Tracing**: OpenTelemetry integration
3. **Caching**: Redis caching layer
4. **Rate Limiting**: Per-user rate limits
5. **WebSocket**: Real-time updates
6. **Streaming**: Efficient streaming responses
7. **Background Jobs**: Task queue system

## Resources

- [Axum Documentation](https://docs.rs/axum/)
- [SQLx Documentation](https://docs.rs/sqlx/)
- [Tokio Tutorial](https://tokio.rs/tokio/tutorial)
- [Rust Book](https://doc.rust-lang.org/book/)
