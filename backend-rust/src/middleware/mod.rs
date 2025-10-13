// Middleware module
pub mod auth;

// Re-export commonly used middleware
pub use auth::auth_middleware;
