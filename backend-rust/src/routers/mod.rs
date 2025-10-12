// Routers module - API endpoints
pub mod auth;
pub mod users;
pub mod chats;
pub mod models;
pub mod ollama;
pub mod openai;
pub mod files;
pub mod images;
pub mod audio;

// Re-export routers
pub use auth::router as auth_router;
pub use users::router as users_router;
pub use chats::router as chats_router;
pub use models::router as models_router;
pub use ollama::router as ollama_router;
pub use openai::router as openai_router;
pub use files::router as files_router;
pub use images::router as images_router;
pub use audio::router as audio_router;
