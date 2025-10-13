# Migration Guide: Python to Rust Backend

This guide provides detailed instructions for continuing the migration of the Open WebUI backend from Python to Rust.

## Overview

The Python backend consists of approximately:
- 188 Python files
- ~60,000 lines of code
- Multiple routers (audio, images, ollama, openai, retrieval, pipelines, tasks, etc.)
- Extensive model definitions
- Complex utility functions
- WebSocket support
- Database migrations

This guide outlines the systematic approach to complete the migration.

## Migration Strategy

### 1. Incremental Migration

Rather than attempting to migrate everything at once, follow this incremental approach:

1. **Core Infrastructure** (✅ Complete)
   - Project setup
   - Configuration management
   - Basic models
   - Authentication utilities
   - Error handling

2. **Database Layer** (Next Priority)
   - SQLx connection pool
   - Model implementations with database operations
   - Query builders
   - Transaction support
   - Migration system

3. **Authentication System**
   - Complete auth endpoints
   - JWT token management
   - OAuth providers
   - API key system
   - Session management

4. **Router-by-Router Migration**
   - Start with simpler routers (users, configs)
   - Progress to complex routers (chat completions, RAG)
   - Test each router thoroughly before moving on

### 2. Python to Rust Equivalents

#### Web Framework
- **Python**: FastAPI
- **Rust**: Axum
- **Key Differences**: 
  - Axum uses extractors instead of dependency injection
  - Routes are composed rather than decorated
  - Middleware is function-based

#### Database ORM
- **Python**: Peewee/SQLAlchemy
- **Rust**: SQLx
- **Key Differences**:
  - SQLx is compile-time checked
  - More explicit query building
  - Async/await native support

#### Type System
- **Python**: Pydantic models
- **Rust**: Serde + structs
- **Key Differences**:
  - Rust types are compile-time checked
  - More explicit handling of Optional values
  - No runtime type coercion

## Detailed Migration Steps

### Step 1: Database Setup

1. Create database connection pool in `src/database.rs`:
```rust
use sqlx::{PgPool, SqlitePool};

pub async fn create_pool(database_url: &str) -> Result<PgPool, sqlx::Error> {
    PgPool::connect(database_url).await
}
```

2. Add pool to AppState in `main.rs`

3. Implement database operations for each model

### Step 2: Complete User Management

Priority order:
1. User CRUD operations
2. User authentication
3. User permissions
4. User settings

Reference Python files:
- `backend/open_webui/models/users.py`
- `backend/open_webui/routers/users.py`

### Step 3: Complete Authentication

Priority order:
1. Login/Signup endpoints
2. JWT token generation and validation
3. OAuth integration
4. API key management

Reference Python files:
- `backend/open_webui/models/auths.py`
- `backend/open_webui/routers/auths.py`
- `backend/open_webui/utils/auth.py`

### Step 4: Chat System

Priority order:
1. Chat CRUD operations
2. Message handling
3. Chat sharing
4. Chat archival/pinning

Reference Python files:
- `backend/open_webui/models/chats.py`
- `backend/open_webui/models/messages.py`
- `backend/open_webui/routers/chats.py`

### Step 5: Model Management

Priority order:
1. Model listing
2. Model CRUD operations
3. Access control
4. Model configurations

Reference Python files:
- `backend/open_webui/models/models.py`
- `backend/open_webui/routers/models.py`

### Step 6: Ollama Integration

Reference Python files:
- `backend/open_webui/routers/ollama.py`

Key components:
- Model listing from Ollama
- Completion endpoints
- Chat endpoints
- Embeddings
- Model pulling/deletion

### Step 7: OpenAI Integration

Reference Python files:
- `backend/open_webui/routers/openai.py`

Key components:
- Chat completions
- Embeddings
- Azure OpenAI support
- Streaming responses

### Step 8: Additional Routers

Migrate remaining routers in order of complexity:

1. **Simple routers** (1-2 days each):
   - configs
   - utils
   - folders
   - prompts
   - notes

2. **Medium routers** (3-5 days each):
   - files
   - functions
   - tools
   - memories
   - knowledge

3. **Complex routers** (1-2 weeks each):
   - tasks (completions, generations)
   - retrieval (RAG, embeddings)
   - pipelines
   - audio (TTS/STT)
   - images (generation)
   - evaluations
   - channels
   - groups
   - scim

### Step 9: WebSocket Support

Reference Python files:
- `backend/open_webui/socket/main.py`
- `backend/open_webui/socket/utils.py`

Components:
- Connection management
- Event emitters
- Usage tracking
- Real-time updates

### Step 10: Advanced Features

- Background tasks
- Caching with Redis
- Rate limiting
- Monitoring and metrics
- Health checks

## Code Conversion Patterns

### Pattern 1: FastAPI Route to Axum Handler

**Python (FastAPI):**
```python
@router.get("/users/{user_id}")
async def get_user(user_id: str, user=Depends(get_verified_user)):
    user_data = Users.get_user_by_id(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    return user_data
```

**Rust (Axum):**
```rust
async fn get_user(
    State(state): State<AppState>,
    Path(user_id): Path<String>,
    Extension(claims): Extension<Claims>,
) -> Result<Json<UserResponse>, AppError> {
    let user = get_user_by_id(&state.db, &user_id).await?
        .ok_or(AppError::NotFound("User not found".to_string()))?;
    Ok(Json(user.into()))
}
```

### Pattern 2: Pydantic Model to Serde Struct

**Python (Pydantic):**
```python
class UserForm(BaseModel):
    name: str
    email: EmailStr
    role: Optional[str] = "user"
```

**Rust (Serde):**
```rust
#[derive(Deserialize, Validate)]
struct UserForm {
    name: String,
    #[validate(email)]
    email: String,
    #[serde(default = "default_role")]
    role: String,
}

fn default_role() -> String {
    "user".to_string()
}
```

### Pattern 3: Database Query

**Python (Peewee):**
```python
users = User.select().where(User.role == "admin").order_by(User.created_at.desc())
```

**Rust (SQLx):**
```rust
let users = sqlx::query_as::<_, User>(
    "SELECT * FROM users WHERE role = $1 ORDER BY created_at DESC"
)
.bind("admin")
.fetch_all(&pool)
.await?;
```

### Pattern 4: Error Handling

**Python:**
```python
try:
    result = do_something()
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

**Rust:**
```rust
let result = do_something()
    .await
    .map_err(|e| AppError::InternalError(e.to_string()))?;
```

## Testing Strategy

### Unit Tests
- Test each function in isolation
- Mock database calls
- Test error conditions

### Integration Tests
- Test complete API endpoints
- Use test database
- Verify response formats

### Compatibility Tests
- Compare responses with Python backend
- Ensure API compatibility
- Test edge cases

## Performance Optimization

After migration, focus on:

1. **Database queries**: Use prepared statements, connection pooling
2. **Serialization**: Optimize JSON serialization with serde
3. **Concurrency**: Leverage Tokio for parallel operations
4. **Memory**: Use references where possible, avoid unnecessary clones
5. **Caching**: Implement Redis caching for frequently accessed data

## Common Pitfalls

1. **Async/Await**: Rust async is different from Python
   - Must use `.await` explicitly
   - Can't use blocking operations in async functions

2. **Error Handling**: Rust requires explicit error handling
   - Use `?` operator for propagation
   - Implement `From` traits for error conversions

3. **Ownership**: Rust's ownership system requires careful planning
   - Use `Arc` for shared state
   - Clone when necessary

4. **Type System**: Rust is strictly typed
   - No implicit conversions
   - Use `Option<T>` for nullable fields

5. **Lifetimes**: May need lifetime annotations
   - Usually in struct definitions with references
   - Compiler will guide you

## Resources

- [Axum Documentation](https://docs.rs/axum/latest/axum/)
- [SQLx Documentation](https://docs.rs/sqlx/latest/sqlx/)
- [Tokio Tutorial](https://tokio.rs/tokio/tutorial)
- [Rust Book](https://doc.rust-lang.org/book/)
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/)

## Getting Help

When stuck:
1. Check Rust compiler errors carefully - they're very helpful
2. Use `cargo clippy` for additional suggestions
3. Review existing Rust web applications for patterns
4. Consult Rust community forums

## Timeline Estimate

Based on complexity:

- **Phase 2** (Authentication & User Management): 2-3 weeks
- **Phase 3** (Core Features): 4-6 weeks
- **Phase 4** (Integrations): 6-8 weeks
- **Phase 5** (Advanced Features): 4-6 weeks
- **Phase 6** (Production Ready): 2-4 weeks

**Total Estimated Time**: 4-6 months with 1-2 developers working full-time

## Conclusion

This migration is a substantial undertaking but will result in a more performant, safer, and maintainable backend. Follow this guide systematically, test thoroughly, and maintain API compatibility throughout the process.
