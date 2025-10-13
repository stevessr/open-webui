use jsonwebtoken::{encode, decode, Header, Validation, EncodingKey, DecodingKey};
use serde::{Deserialize, Serialize};
use chrono::{Utc, Duration};

use super::errors::{AppError, Result};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,  // User ID
    pub email: String,
    pub role: String,
    pub exp: i64,     // Expiration time
    pub iat: i64,     // Issued at
}

impl Claims {
    pub fn new(user_id: String, email: String, role: String, expires_in_days: i64) -> Self {
        let now = Utc::now();
        let expiration = now + Duration::days(expires_in_days);
        
        Claims {
            sub: user_id,
            email,
            role,
            exp: expiration.timestamp(),
            iat: now.timestamp(),
        }
    }
}

/// Create a JWT token for a user
pub fn create_token(user_id: String, email: String, role: String, secret: &str) -> Result<String> {
    let claims = Claims::new(user_id, email, role, 7); // 7 days expiration
    
    encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(secret.as_bytes()),
    )
    .map_err(|e| AppError::TokenError(format!("Failed to create token: {}", e)))
}

/// Verify and decode a JWT token
pub fn verify_token(token: &str, secret: &str) -> Result<Claims> {
    decode::<Claims>(
        token,
        &DecodingKey::from_secret(secret.as_bytes()),
        &Validation::default(),
    )
    .map(|data| data.claims)
    .map_err(|e| AppError::TokenError(format!("Invalid token: {}", e)))
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_create_and_verify_token() {
        let secret = "test-secret-key";
        let user_id = "user123".to_string();
        let email = "test@example.com".to_string();
        let role = "user".to_string();
        
        let token = create_token(user_id.clone(), email.clone(), role.clone(), secret)
            .expect("Failed to create token");
        
        let claims = verify_token(&token, secret)
            .expect("Failed to verify token");
        
        assert_eq!(claims.sub, user_id);
        assert_eq!(claims.email, email);
        assert_eq!(claims.role, role);
    }
}
