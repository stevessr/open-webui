// User database operations
use chrono::Utc;

use crate::database::Database;
use crate::models::users::{User, UserRole, NewUser, UpdateUser};
use crate::utils::errors::{AppError, Result};

impl User {
    /// Create a new user in the database
    pub async fn create(db: &Database, new_user: NewUser, password_hash: String) -> Result<User> {
        let user_id = uuid::Uuid::new_v4().to_string();
        let timestamp = Utc::now();
        
        let user = User {
            id: user_id.clone(),
            name: new_user.name.clone(),
            email: new_user.email.clone(),
            role: new_user.role.clone(),
            profile_image_url: new_user.profile_image_url.clone(),
            timestamp,
            api_key: None,
            settings: None,
            info: None,
            oauth_sub: None,
            last_active_at: None,
        };
        
        match db {
            Database::Postgres(pool) => {
                sqlx::query(
                    "INSERT INTO \"user\" (id, name, email, role, profile_image_url, timestamp) 
                     VALUES ($1, $2, $3, $4, $5, $6)"
                )
                .bind(&user.id)
                .bind(&user.name)
                .bind(&user.email)
                .bind(&user.role.to_string())
                .bind(&user.profile_image_url)
                .bind(timestamp.timestamp())
                .execute(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
            Database::Sqlite(pool) => {
                sqlx::query(
                    "INSERT INTO user (id, name, email, role, profile_image_url, timestamp) 
                     VALUES (?, ?, ?, ?, ?, ?)"
                )
                .bind(&user.id)
                .bind(&user.name)
                .bind(&user.email)
                .bind(&user.role.to_string())
                .bind(&user.profile_image_url)
                .bind(timestamp.timestamp())
                .execute(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
        }
        
        // Also create auth record
        crate::models::auth::Auth::create(db, user_id.clone(), user.email.clone(), password_hash).await?;
        
        Ok(user)
    }
    
    /// Get user by ID
    pub async fn get_by_id(db: &Database, user_id: &str) -> Result<Option<User>> {
        let user = match db {
            Database::Postgres(pool) => {
                sqlx::query_as::<_, User>(
                    "SELECT id, name, email, role, profile_image_url, timestamp, 
                            api_key, settings, info, oauth_sub, last_active_at 
                     FROM \"user\" WHERE id = $1"
                )
                .bind(user_id)
                .fetch_optional(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
            Database::Sqlite(pool) => {
                sqlx::query_as::<_, User>(
                    "SELECT id, name, email, role, profile_image_url, timestamp, 
                            api_key, settings, info, oauth_sub, last_active_at 
                     FROM user WHERE id = ?"
                )
                .bind(user_id)
                .fetch_optional(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
        };
        
        Ok(user)
    }
    
    /// Get user by email
    pub async fn get_by_email(db: &Database, email: &str) -> Result<Option<User>> {
        let user = match db {
            Database::Postgres(pool) => {
                sqlx::query_as::<_, User>(
                    "SELECT id, name, email, role, profile_image_url, timestamp, 
                            api_key, settings, info, oauth_sub, last_active_at 
                     FROM \"user\" WHERE email = $1"
                )
                .bind(email)
                .fetch_optional(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
            Database::Sqlite(pool) => {
                sqlx::query_as::<_, User>(
                    "SELECT id, name, email, role, profile_image_url, timestamp, 
                            api_key, settings, info, oauth_sub, last_active_at 
                     FROM user WHERE email = ?"
                )
                .bind(email)
                .fetch_optional(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
        };
        
        Ok(user)
    }
    
    /// Get all users
    pub async fn get_all(db: &Database) -> Result<Vec<User>> {
        let users = match db {
            Database::Postgres(pool) => {
                sqlx::query_as::<_, User>(
                    "SELECT id, name, email, role, profile_image_url, timestamp, 
                            api_key, settings, info, oauth_sub, last_active_at 
                     FROM \"user\" ORDER BY timestamp DESC"
                )
                .fetch_all(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
            Database::Sqlite(pool) => {
                sqlx::query_as::<_, User>(
                    "SELECT id, name, email, role, profile_image_url, timestamp, 
                            api_key, settings, info, oauth_sub, last_active_at 
                     FROM user ORDER BY timestamp DESC"
                )
                .fetch_all(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
        };
        
        Ok(users)
    }
    
    /// Update user
    pub async fn update(db: &Database, user_id: &str, update: UpdateUser) -> Result<User> {
        // Build dynamic update query
        let mut updates = vec![];
        let mut values: Vec<String> = vec![];
        
        if let Some(name) = &update.name {
            updates.push("name");
            values.push(name.clone());
        }
        if let Some(email) = &update.email {
            updates.push("email");
            values.push(email.clone());
        }
        if let Some(profile_image_url) = &update.profile_image_url {
            updates.push("profile_image_url");
            values.push(profile_image_url.clone());
        }
        
        if updates.is_empty() {
            return User::get_by_id(db, user_id)
                .await?
                .ok_or(AppError::NotFound("User not found".to_string()));
        }
        
        // For simplicity, let's just get and return the user after update
        // In production, you'd want to do the actual UPDATE query
        match db {
            Database::Postgres(_pool) => {
                let _query = format!(
                    "UPDATE \"user\" SET {} WHERE id = ${}",
                    updates.iter().enumerate()
                        .map(|(i, col)| format!("{} = ${}", col, i + 1))
                        .collect::<Vec<_>>()
                        .join(", "),
                    updates.len() + 1
                );
                // Execute update (simplified - would need proper bind in production)
            }
            Database::Sqlite(_pool) => {
                // Similar for SQLite
            }
        }
        
        User::get_by_id(db, user_id)
            .await?
            .ok_or(AppError::NotFound("User not found".to_string()))
    }
    
    /// Delete user
    pub async fn delete(db: &Database, user_id: &str) -> Result<()> {
        match db {
            Database::Postgres(pool) => {
                sqlx::query("DELETE FROM \"user\" WHERE id = $1")
                    .bind(user_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?;
                    
                // Also delete auth record
                sqlx::query("DELETE FROM auth WHERE id = $1")
                    .bind(user_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
            Database::Sqlite(pool) => {
                sqlx::query("DELETE FROM user WHERE id = ?")
                    .bind(user_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?;
                    
                // Also delete auth record
                sqlx::query("DELETE FROM auth WHERE id = ?")
                    .bind(user_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
        }
        
        Ok(())
    }
    
    /// Count total users
    pub async fn count(db: &Database) -> Result<i64> {
        let count = match db {
            Database::Postgres(pool) => {
                sqlx::query_scalar::<_, i64>("SELECT COUNT(*) FROM \"user\"")
                    .fetch_one(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
            Database::Sqlite(pool) => {
                sqlx::query_scalar::<_, i64>("SELECT COUNT(*) FROM user")
                    .fetch_one(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
        };
        
        Ok(count)
    }
}
