use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use sqlx::FromRow;

/// Chat model matching Python backend's Chat model
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Chat {
    pub id: String,
    pub user_id: String,
    pub title: String,
    pub chat: serde_json::Value,
    
    #[serde(with = "chrono::serde::ts_seconds")]
    pub created_at: DateTime<Utc>,
    
    #[serde(with = "chrono::serde::ts_seconds")]
    pub updated_at: DateTime<Utc>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub share_id: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub archived: Option<bool>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pinned: Option<bool>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub meta: Option<serde_json::Value>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub folder_id: Option<String>,
}

/// New chat creation struct
#[derive(Debug, Clone, Deserialize)]
pub struct NewChat {
    pub id: String,
    pub user_id: String,
    pub title: String,
    #[serde(default)]
    pub chat: serde_json::Value,
}

/// Update chat struct
#[derive(Debug, Clone, Deserialize)]
pub struct UpdateChat {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub title: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub chat: Option<serde_json::Value>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub archived: Option<bool>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pinned: Option<bool>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub meta: Option<serde_json::Value>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub folder_id: Option<String>,
}
