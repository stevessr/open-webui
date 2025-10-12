// Message database operations
use chrono::Utc;

use crate::database::Database;
use crate::models::messages::{Message, NewMessage};
use crate::utils::errors::{AppError, Result};

impl Message {
    /// Create a new message
    pub async fn create(db: &Database, new_message: NewMessage) -> Result<Message> {
        let timestamp = Utc::now();
        
        let message = Message {
            id: new_message.id.clone(),
            chat_id: new_message.chat_id.clone(),
            user_id: new_message.user_id.clone(),
            role: new_message.role.clone(),
            content: new_message.content.clone(),
            created_at: timestamp,
            updated_at: timestamp,
            model: new_message.model.clone(),
            parent_id: new_message.parent_id.clone(),
            tool_calls: None,
            tool_call_id: None,
        };
        
        match db {
            Database::Postgres(pool) => {
                sqlx::query(
                    "INSERT INTO message (id, chat_id, user_id, role, content, created_at, updated_at, model, parent_id) 
                     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)"
                )
                .bind(&message.id)
                .bind(&message.chat_id)
                .bind(&message.user_id)
                .bind(&message.role)
                .bind(&message.content)
                .bind(timestamp.timestamp())
                .bind(timestamp.timestamp())
                .bind(&message.model)
                .bind(&message.parent_id)
                .execute(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
            Database::Sqlite(pool) => {
                sqlx::query(
                    "INSERT INTO message (id, chat_id, user_id, role, content, created_at, updated_at, model, parent_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                )
                .bind(&message.id)
                .bind(&message.chat_id)
                .bind(&message.user_id)
                .bind(&message.role)
                .bind(&message.content)
                .bind(timestamp.timestamp())
                .bind(timestamp.timestamp())
                .bind(&message.model)
                .bind(&message.parent_id)
                .execute(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
        }
        
        Ok(message)
    }
    
    /// Get message by ID
    pub async fn get_by_id(db: &Database, message_id: &str) -> Result<Option<Message>> {
        let message = match db {
            Database::Postgres(pool) => {
                sqlx::query_as::<_, Message>(
                    "SELECT id, chat_id, user_id, role, content, created_at, updated_at, 
                            model, parent_id, tool_calls, tool_call_id 
                     FROM message WHERE id = $1"
                )
                .bind(message_id)
                .fetch_optional(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
            Database::Sqlite(pool) => {
                sqlx::query_as::<_, Message>(
                    "SELECT id, chat_id, user_id, role, content, created_at, updated_at, 
                            model, parent_id, tool_calls, tool_call_id 
                     FROM message WHERE id = ?"
                )
                .bind(message_id)
                .fetch_optional(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
        };
        
        Ok(message)
    }
    
    /// Get all messages for a chat
    pub async fn get_by_chat(db: &Database, chat_id: &str) -> Result<Vec<Message>> {
        let messages = match db {
            Database::Postgres(pool) => {
                sqlx::query_as::<_, Message>(
                    "SELECT id, chat_id, user_id, role, content, created_at, updated_at, 
                            model, parent_id, tool_calls, tool_call_id 
                     FROM message 
                     WHERE chat_id = $1 
                     ORDER BY created_at ASC"
                )
                .bind(chat_id)
                .fetch_all(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
            Database::Sqlite(pool) => {
                sqlx::query_as::<_, Message>(
                    "SELECT id, chat_id, user_id, role, content, created_at, updated_at, 
                            model, parent_id, tool_calls, tool_call_id 
                     FROM message 
                     WHERE chat_id = ? 
                     ORDER BY created_at ASC"
                )
                .bind(chat_id)
                .fetch_all(pool)
                .await
                .map_err(|e| AppError::DatabaseError(e.to_string()))?
            }
        };
        
        Ok(messages)
    }
    
    /// Delete message
    pub async fn delete(db: &Database, message_id: &str) -> Result<()> {
        match db {
            Database::Postgres(pool) => {
                sqlx::query("DELETE FROM message WHERE id = $1")
                    .bind(message_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
            Database::Sqlite(pool) => {
                sqlx::query("DELETE FROM message WHERE id = ?")
                    .bind(message_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
        }
        
        Ok(())
    }
    
    /// Delete all messages for a chat
    pub async fn delete_by_chat(db: &Database, chat_id: &str) -> Result<()> {
        match db {
            Database::Postgres(pool) => {
                sqlx::query("DELETE FROM message WHERE chat_id = $1")
                    .bind(chat_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
            Database::Sqlite(pool) => {
                sqlx::query("DELETE FROM message WHERE chat_id = ?")
                    .bind(chat_id)
                    .execute(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(e.to_string()))?;
            }
        }
        
        Ok(())
    }
}
