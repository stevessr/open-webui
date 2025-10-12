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
pub mod rag;
pub mod knowledge;
pub mod tasks;
pub mod memory;
pub mod evaluations;
pub mod pipelines;
pub mod functions;

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
pub use rag::router as rag_router;
pub use knowledge::router as knowledge_router;
pub use tasks::router as tasks_router;
pub use memory::router as memory_router;
pub use evaluations::router as evaluations_router;
pub use pipelines::router as pipelines_router;
pub use functions::router as functions_router;
