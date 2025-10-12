// Routers module - API endpoints
pub mod auth;
pub mod users;
pub mod chats;
pub mod models;
pub mod ollama;

// Re-export routers
pub use auth::router as auth_router;
pub use users::router as users_router;
pub use chats::router as chats_router;
pub use models::router as models_router;
pub use ollama::router as ollama_router;
