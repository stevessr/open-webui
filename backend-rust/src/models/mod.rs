// Models module - Database models and schemas
pub mod users;
pub mod users_db;
pub mod chats;
pub mod messages;
pub mod models;
pub mod auth;
pub mod auth_db;

// Re-export commonly used types
pub use users::{User, UserRole, NewUser};
pub use auth::{Auth, NewAuth};
