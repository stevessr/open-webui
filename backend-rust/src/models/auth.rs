use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use sqlx::FromRow;

/// Auth model matching Python backend's Auth model
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Auth {
    pub id: String,
    pub email: String,
    pub password: String,
    pub active: bool,
    
    #[serde(with = "chrono::serde::ts_seconds")]
    pub created_at: DateTime<Utc>,
}

/// New auth creation struct
#[derive(Debug, Clone, Deserialize)]
pub struct NewAuth {
    pub id: String,
    pub email: String,
    pub password: String,
}

impl Auth {
    pub fn new(id: String, email: String, password_hash: String) -> Self {
        Auth {
            id,
            email,
            password: password_hash,
            active: true,
            created_at: Utc::now(),
        }
    }
}

/// Login request
#[derive(Debug, Deserialize)]
pub struct LoginRequest {
    pub email: String,
    pub password: String,
}

/// Signup request
#[derive(Debug, Deserialize)]
pub struct SignupRequest {
    pub name: String,
    pub email: String,
    pub password: String,
}

/// Token response
#[derive(Debug, Serialize)]
pub struct TokenResponse {
    pub token: String,
    pub token_type: String,
}
