use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use sqlx::FromRow;

/// Model model matching Python backend's Models model
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Model {
    pub id: String,
    pub user_id: String,
    pub base_model_id: Option<String>,
    pub name: String,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub params: Option<serde_json::Value>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub meta: Option<serde_json::Value>,
    
    #[serde(with = "chrono::serde::ts_seconds")]
    pub created_at: DateTime<Utc>,
    
    #[serde(with = "chrono::serde::ts_seconds")]
    pub updated_at: DateTime<Utc>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_active: Option<bool>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub access_control: Option<serde_json::Value>,
}

/// New model creation struct
#[derive(Debug, Clone, Deserialize)]
pub struct NewModel {
    pub id: String,
    pub user_id: String,
    pub name: String,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub base_model_id: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub params: Option<serde_json::Value>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub meta: Option<serde_json::Value>,
}

/// Update model struct
#[derive(Debug, Clone, Deserialize)]
pub struct UpdateModel {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub params: Option<serde_json::Value>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub meta: Option<serde_json::Value>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_active: Option<bool>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub access_control: Option<serde_json::Value>,
}
