use axum::{
    Router,
    routing::{get, post, put, patch, delete},
    http::StatusCode,
    response::{IntoResponse, Json},
    extract::{State, Path, Query},
};
use serde::{Deserialize, Serialize};
use serde_json::json;

use crate::AppState;

#[derive(Debug, Serialize, Deserialize)]
pub struct ScimUser {
    pub id: String,
    pub schemas: Vec<String>,
    pub user_name: String,
    pub name: ScimName,
    pub emails: Vec<ScimEmail>,
    pub active: bool,
    pub meta: ScimMeta,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ScimName {
    pub given_name: String,
    pub family_name: String,
    pub formatted: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ScimEmail {
    pub value: String,
    pub primary: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ScimMeta {
    pub resource_type: String,
    pub created: String,
    pub last_modified: String,
    pub location: String,
}

#[derive(Debug, Deserialize)]
pub struct ScimQuery {
    pub start_index: Option<u32>,
    pub count: Option<u32>,
    pub filter: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct CreateScimUserRequest {
    pub schemas: Vec<String>,
    pub user_name: String,
    pub name: ScimName,
    pub emails: Vec<ScimEmail>,
    pub active: Option<bool>,
}

pub fn router() -> Router<AppState> {
    Router::new()
        // Service Provider Config
        .route("/ServiceProviderConfig", get(get_service_provider_config))
        // Resource Types
        .route("/ResourceTypes", get(get_resource_types))
        // Schemas
        .route("/Schemas", get(get_schemas))
        // Users
        .route("/Users", get(list_users).post(create_user))
        .route("/Users/:id", get(get_user).put(update_user).patch(patch_user).delete(delete_user))
        // Groups
        .route("/Groups", get(list_groups).post(create_group))
        .route("/Groups/:id", get(get_group).put(update_group).patch(patch_group).delete(delete_group))
}

/// Get Service Provider Configuration
async fn get_service_provider_config(
    State(_state): State<AppState>,
) -> impl IntoResponse {
    Json(json!({
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
        "patch": {
            "supported": true
        },
        "bulk": {
            "supported": false
        },
        "filter": {
            "supported": true,
            "maxResults": 200
        },
        "changePassword": {
            "supported": true
        },
        "sort": {
            "supported": true
        },
        "etag": {
            "supported": false
        },
        "authenticationSchemes": [
            {
                "type": "oauthbearertoken",
                "name": "OAuth Bearer Token",
                "description": "Authentication scheme using the OAuth Bearer Token Standard",
                "specUri": "https://tools.ietf.org/html/rfc6750",
                "documentationUri": "https://example.com/help/oauth.html",
                "primary": true
            }
        ]
    }))
}

/// Get Resource Types
async fn get_resource_types(
    State(_state): State<AppState>,
) -> impl IntoResponse {
    Json(json!({
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "Resources": [
            {
                "id": "User",
                "name": "User",
                "endpoint": "/Users",
                "description": "User Account",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:User"
            },
            {
                "id": "Group",
                "name": "Group",
                "endpoint": "/Groups",
                "description": "Group",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:Group"
            }
        ]
    }))
}

/// Get Schemas
async fn get_schemas(
    State(_state): State<AppState>,
) -> impl IntoResponse {
    Json(json!({
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "Resources": [
            {
                "id": "urn:ietf:params:scim:schemas:core:2.0:User",
                "name": "User",
                "description": "User Account"
            },
            {
                "id": "urn:ietf:params:scim:schemas:core:2.0:Group",
                "name": "Group",
                "description": "Group"
            }
        ]
    }))
}

/// List Users
async fn list_users(
    State(_state): State<AppState>,
    Query(_query): Query<ScimQuery>,
) -> impl IntoResponse {
    let users: Vec<ScimUser> = vec![];
    Json(json!({
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": 0,
        "itemsPerPage": 0,
        "startIndex": 1,
        "Resources": users
    }))
}

/// Create User
async fn create_user(
    State(_state): State<AppState>,
    Json(_payload): Json<CreateScimUserRequest>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "SCIM user creation not yet implemented"
        }))
    )
}

/// Get User
async fn get_user(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "SCIM user retrieval not yet implemented"
        }))
    )
}

/// Update User (PUT)
async fn update_user(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
    Json(_payload): Json<CreateScimUserRequest>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "SCIM user update not yet implemented"
        }))
    )
}

/// Patch User
async fn patch_user(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
    Json(_payload): Json<serde_json::Value>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "SCIM user patch not yet implemented"
        }))
    )
}

/// Delete User
async fn delete_user(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
) -> impl IntoResponse {
    (StatusCode::NO_CONTENT, "")
}

/// List Groups
async fn list_groups(
    State(_state): State<AppState>,
    Query(_query): Query<ScimQuery>,
) -> impl IntoResponse {
    Json(json!({
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": 0,
        "itemsPerPage": 0,
        "startIndex": 1,
        "Resources": []
    }))
}

/// Create Group
async fn create_group(
    State(_state): State<AppState>,
    Json(_payload): Json<serde_json::Value>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "SCIM group creation not yet implemented"
        }))
    )
}

/// Get Group
async fn get_group(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "SCIM group retrieval not yet implemented"
        }))
    )
}

/// Update Group (PUT)
async fn update_group(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
    Json(_payload): Json<serde_json::Value>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "SCIM group update not yet implemented"
        }))
    )
}

/// Patch Group
async fn patch_group(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
    Json(_payload): Json<serde_json::Value>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "SCIM group patch not yet implemented"
        }))
    )
}

/// Delete Group
async fn delete_group(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
) -> impl IntoResponse {
    (StatusCode::NO_CONTENT, "")
}
