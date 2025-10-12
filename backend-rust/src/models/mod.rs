// Models module - Database models and schemas
pub mod users;
pub mod chats;
pub mod messages;
pub mod models;
pub mod auth;

// Re-export commonly used types
pub use users::{User, UserRole, NewUser};
pub use auth::{Auth, NewAuth};
