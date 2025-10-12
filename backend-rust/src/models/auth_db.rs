// Auth database operations
use chrono::Utc;

use crate::database::Database;
use crate::models::auth::Auth;
use crate::utils::errors::{AppError, Result};

impl Auth {
    /// Create a new auth record
    pub async fn create(db: &Database, user_id: String, email: String, password_hash: String) -> Result<Auth> {
        let created_at = Utc::now();
        
        let auth = Auth {
            id: user_id.clone(),
            email: email.clone(),
            password: password_hash.clone(),
            active: true,
            created_at,
        };
        
        match db {
            Database::Postgres(pool) => {
                sqlx::query(
                    "INSERT INTO auth (id, email, password, active, created_at) 
                     VALUES ($1, $2, $3, $4, $5)"
                )
                .bind(&auth.id)
                .bind(&auth.email)
                .bind(&auth.password)
                .bind(auth.active)
                .bind(created_at.timestamp())
                .execute(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
            Database::Sqlite(pool) => {
                sqlx::query(
                    "INSERT INTO auth (id, email, password, active, created_at) 
                     VALUES (?, ?, ?, ?, ?)"
                )
                .bind(&auth.id)
                .bind(&auth.email)
                .bind(&auth.password)
                .bind(auth.active)
                .bind(created_at.timestamp())
                .execute(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
        }
        
        Ok(auth)
    }
    
    /// Get auth by email
    pub async fn get_by_email(db: &Database, email: &str) -> Result<Option<Auth>> {
        let auth = match db {
            Database::Postgres(pool) => {
                sqlx::query_as::<_, Auth>(
                    "SELECT id, email, password, active, created_at 
                     FROM auth WHERE email = $1"
                )
                .bind(email)
                .fetch_optional(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
            Database::Sqlite(pool) => {
                sqlx::query_as::<_, Auth>(
                    "SELECT id, email, password, active, created_at 
                     FROM auth WHERE email = ?"
                )
                .bind(email)
                .fetch_optional(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
        };
        
        Ok(auth)
    }
    
    /// Update password
    pub async fn update_password(db: &Database, user_id: &str, new_password_hash: String) -> Result<()> {
        match db {
            Database::Postgres(pool) => {
                sqlx::query("UPDATE auth SET password = $1 WHERE id = $2")
                    .bind(new_password_hash)
                    .bind(user_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
            Database::Sqlite(pool) => {
                sqlx::query("UPDATE auth SET password = ? WHERE id = ?")
                    .bind(new_password_hash)
                    .bind(user_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
        }
        
        Ok(())
    }
}
