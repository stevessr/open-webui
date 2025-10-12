use axum::{
    Router,
    routing::{get, post, delete},
    http::StatusCode,
    response::{IntoResponse, Json},
    extract::{State, Path},
};
use serde_json::json;

use crate::AppState;
use crate::models::users::{UpdateUser, UserResponse};

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/", get(get_users))
        .route("/:id", get(get_user_by_id))
        .route("/:id", post(update_user_by_id))
        .route("/:id", delete(delete_user_by_id))
}

/// Get all users
async fn get_users(
    State(_state): State<AppState>,
) -> impl IntoResponse {
    // TODO: Implement user listing
    // 1. Query database for all users
    // 2. Convert to UserResponse
    // 3. Return list
    
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "User listing not yet implemented"
        }))
    )
}

/// Get user by ID
async fn get_user_by_id(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
) -> impl IntoResponse {
    // TODO: Implement user retrieval
    // 1. Query database for user by id
    // 2. Convert to UserResponse
    // 3. Return user or 404
    
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "User retrieval not yet implemented"
        }))
    )
}

/// Update user by ID
async fn update_user_by_id(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
    Json(_payload): Json<UpdateUser>,
) -> impl IntoResponse {
    // TODO: Implement user update
    // 1. Validate authorization
    // 2. Update user in database
    // 3. Return updated user
    
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "User update not yet implemented"
        }))
    )
}

/// Delete user by ID
async fn delete_user_by_id(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
) -> impl IntoResponse {
    // TODO: Implement user deletion
    // 1. Validate authorization (admin only)
    // 2. Delete user from database
    // 3. Return success message
    
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "User deletion not yet implemented"
        }))
    )
}
