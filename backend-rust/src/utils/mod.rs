// Utilities module
pub mod jwt;
pub mod password;
pub mod errors;

// Re-export commonly used utilities
pub use jwt::{create_token, verify_token, Claims};
pub use password::{hash_password, verify_password};
pub use errors::{AppError, Result};
