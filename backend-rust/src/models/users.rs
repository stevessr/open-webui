use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;
use sqlx::FromRow;

/// User role enum matching Python backend
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, sqlx::Type)]
#[sqlx(type_name = "text")]
#[serde(rename_all = "lowercase")]
pub enum UserRole {
    #[sqlx(rename = "admin")]
    Admin,
    #[sqlx(rename = "user")]
    User,
    #[sqlx(rename = "pending")]
    Pending,
}

impl Default for UserRole {
    fn default() -> Self {
        UserRole::Pending
    }
}

/// User model matching Python backend's User model
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct User {
    pub id: String,
    pub name: String,
    pub email: String,
    pub role: UserRole,
    pub profile_image_url: String,
    
    #[serde(with = "chrono::serde::ts_seconds")]
    pub timestamp: DateTime<Utc>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub api_key: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub settings: Option<serde_json::Value>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub info: Option<serde_json::Value>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub oauth_sub: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub last_active_at: Option<DateTime<Utc>>,
}

/// New user creation struct
#[derive(Debug, Clone, Deserialize)]
pub struct NewUser {
    pub name: String,
    pub email: String,
    pub password: String,
    #[serde(default)]
    pub role: UserRole,
    #[serde(default = "default_profile_image")]
    pub profile_image_url: String,
}

fn default_profile_image() -> String {
    "/user.png".to_string()
}

/// User update struct
#[derive(Debug, Clone, Deserialize)]
pub struct UpdateUser {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub email: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub profile_image_url: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub password: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub settings: Option<serde_json::Value>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub info: Option<serde_json::Value>,
}

/// User response struct (without sensitive data)
#[derive(Debug, Clone, Serialize)]
pub struct UserResponse {
    pub id: String,
    pub name: String,
    pub email: String,
    pub role: UserRole,
    pub profile_image_url: String,
    pub timestamp: DateTime<Utc>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub settings: Option<serde_json::Value>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub info: Option<serde_json::Value>,
}

impl From<User> for UserResponse {
    fn from(user: User) -> Self {
        UserResponse {
            id: user.id,
            name: user.name,
            email: user.email,
            role: user.role,
            profile_image_url: user.profile_image_url,
            timestamp: user.timestamp,
            settings: user.settings,
            info: user.info,
        }
    }
}

/// User model implementation
impl User {
    pub fn new(
        name: String,
        email: String,
        role: UserRole,
        profile_image_url: String,
    ) -> Self {
        User {
            id: Uuid::new_v4().to_string(),
            name,
            email,
            role,
            profile_image_url,
            timestamp: Utc::now(),
            api_key: None,
            settings: None,
            info: None,
            oauth_sub: None,
            last_active_at: None,
        }
    }
    
    pub fn generate_api_key(&mut self) {
        self.api_key = Some(format!("sk-{}", Uuid::new_v4()));
    }
}
