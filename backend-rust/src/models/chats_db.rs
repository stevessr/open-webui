// Chat database operations
use chrono::Utc;

use crate::database::Database;
use crate::models::chats::{Chat, NewChat, UpdateChat};
use crate::utils::errors::{AppError, Result};

impl Chat {
    /// Create a new chat
    pub async fn create(db: &Database, new_chat: NewChat) -> Result<Chat> {
        let timestamp = Utc::now();
        
        let chat = Chat {
            id: new_chat.id.clone(),
            user_id: new_chat.user_id.clone(),
            title: new_chat.title.clone(),
            chat: new_chat.chat.clone(),
            created_at: timestamp,
            updated_at: timestamp,
            share_id: None,
            archived: Some(false),
            pinned: Some(false),
            meta: None,
            folder_id: None,
        };
        
        match db {
            Database::Postgres(pool) => {
                sqlx::query(
                    "INSERT INTO chat (id, user_id, title, chat, created_at, updated_at, archived, pinned) 
                     VALUES ($1, $2, $3, $4, $5, $6, $7, $8)"
                )
                .bind(&chat.id)
                .bind(&chat.user_id)
                .bind(&chat.title)
                .bind(chat.chat.to_string())
                .bind(timestamp.timestamp())
                .bind(timestamp.timestamp())
                .bind(false)
                .bind(false)
                .execute(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
            Database::Sqlite(pool) => {
                sqlx::query(
                    "INSERT INTO chat (id, user_id, title, chat, created_at, updated_at, archived, pinned) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                )
                .bind(&chat.id)
                .bind(&chat.user_id)
                .bind(&chat.title)
                .bind(chat.chat.to_string())
                .bind(timestamp.timestamp())
                .bind(timestamp.timestamp())
                .bind(false)
                .bind(false)
                .execute(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
        }
        
        Ok(chat)
    }
    
    /// Get chat by ID
    pub async fn get_by_id(db: &Database, chat_id: &str) -> Result<Option<Chat>> {
        let chat = match db {
            Database::Postgres(pool) => {
                sqlx::query_as::<_, Chat>(
                    "SELECT id, user_id, title, chat, created_at, updated_at, 
                            share_id, archived, pinned, meta, folder_id 
                     FROM chat WHERE id = $1"
                )
                .bind(chat_id)
                .fetch_optional(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
            Database::Sqlite(pool) => {
                sqlx::query_as::<_, Chat>(
                    "SELECT id, user_id, title, chat, created_at, updated_at, 
                            share_id, archived, pinned, meta, folder_id 
                     FROM chat WHERE id = ?"
                )
                .bind(chat_id)
                .fetch_optional(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
        };
        
        Ok(chat)
    }
    
    /// Get all chats for a user
    pub async fn get_by_user(db: &Database, user_id: &str) -> Result<Vec<Chat>> {
        let chats = match db {
            Database::Postgres(pool) => {
                sqlx::query_as::<_, Chat>(
                    "SELECT id, user_id, title, chat, created_at, updated_at, 
                            share_id, archived, pinned, meta, folder_id 
                     FROM chat 
                     WHERE user_id = $1 
                     ORDER BY updated_at DESC"
                )
                .bind(user_id)
                .fetch_all(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
            Database::Sqlite(pool) => {
                sqlx::query_as::<_, Chat>(
                    "SELECT id, user_id, title, chat, created_at, updated_at, 
                            share_id, archived, pinned, meta, folder_id 
                     FROM chat 
                     WHERE user_id = ? 
                     ORDER BY updated_at DESC"
                )
                .bind(user_id)
                .fetch_all(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
        };
        
        Ok(chats)
    }
    
    /// Update chat
    pub async fn update(db: &Database, chat_id: &str, update: UpdateChat) -> Result<Chat> {
        let timestamp = Utc::now();
        
        // For simplicity, only update title if provided
        if let Some(title) = &update.title {
            match db {
                Database::Postgres(pool) => {
                    sqlx::query(
                        "UPDATE chat SET title = $1, updated_at = $2 WHERE id = $3"
                    )
                    .bind(title)
                    .bind(timestamp.timestamp())
                    .bind(chat_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?;
                }
                Database::Sqlite(pool) => {
                    sqlx::query(
                        "UPDATE chat SET title = ?, updated_at = ? WHERE id = ?"
                    )
                    .bind(title)
                    .bind(timestamp.timestamp())
                    .bind(chat_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?;
                }
            }
        }
        
        Chat::get_by_id(db, chat_id)
            .await?
            .ok_or(AppError::NotFound("Chat not found".to_string()))
    }
    
    /// Delete chat
    pub async fn delete(db: &Database, chat_id: &str) -> Result<()> {
        match db {
            Database::Postgres(pool) => {
                sqlx::query("DELETE FROM chat WHERE id = $1")
                    .bind(chat_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
            Database::Sqlite(pool) => {
                sqlx::query("DELETE FROM chat WHERE id = ?")
                    .bind(chat_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
        }
        
        Ok(())
    }
    
    /// Archive/unarchive chat
    pub async fn set_archived(db: &Database, chat_id: &str, archived: bool) -> Result<()> {
        match db {
            Database::Postgres(pool) => {
                sqlx::query("UPDATE chat SET archived = $1, updated_at = $2 WHERE id = $3")
                    .bind(archived)
                    .bind(Utc::now().timestamp())
                    .bind(chat_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
            Database::Sqlite(pool) => {
                sqlx::query("UPDATE chat SET archived = ?, updated_at = ? WHERE id = ?")
                    .bind(archived)
                    .bind(Utc::now().timestamp())
                    .bind(chat_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
        }
        
        Ok(())
    }
}
