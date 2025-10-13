use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use sqlx::FromRow;

/// Message model matching Python backend's Message model
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Message {
    pub id: String,
    pub chat_id: String,
    pub user_id: String,
    pub role: String,
    pub content: String,
    
    #[serde(with = "chrono::serde::ts_seconds")]
    pub created_at: DateTime<Utc>,
    
    #[serde(with = "chrono::serde::ts_seconds")]
    pub updated_at: DateTime<Utc>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub parent_id: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_calls: Option<serde_json::Value>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_call_id: Option<String>,
}

/// New message creation struct
#[derive(Debug, Clone, Deserialize)]
pub struct NewMessage {
    pub id: String,
    pub chat_id: String,
    pub user_id: String,
    pub role: String,
    pub content: String,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub parent_id: Option<String>,
}
