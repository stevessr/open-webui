use axum::{
    Router,
    routing::{get, post, delete},
    http::StatusCode,
    response::{IntoResponse, Json},
    extract::{State, Path},
    Extension,
};
use serde_json::json;

use crate::AppState;
use crate::models::users::{UpdateUser, UserResponse, User};
use crate::utils::jwt::Claims;
use crate::utils::errors::AppError;

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/", get(get_users))
        .route("/:id", get(get_user_by_id))
        .route("/:id", post(update_user_by_id))
        .route("/:id", delete(delete_user_by_id))
}

/// Get all users (admin only)
async fn get_users(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
) -> Result<Json<Vec<UserResponse>>, AppError> {
    // Check if user is admin
    if claims.role != "admin" {
        return Err(AppError::Forbidden("Admin access required".to_string()));
    }
    
    let users = User::get_all(&state.db).await?;
    let response: Vec<UserResponse> = users.into_iter().map(|u| u.into()).collect();
    
    Ok(Json(response))
}

/// Get user by ID
async fn get_user_by_id(
    State(state): State<AppState>,
    Path(id): Path<String>,
    Extension(claims): Extension<Claims>,
) -> Result<Json<UserResponse>, AppError> {
    // Users can only view their own profile unless they're admin
    if claims.sub != id && claims.role != "admin" {
        return Err(AppError::Forbidden("Access denied".to_string()));
    }
    
    let user = User::get_by_id(&state.db, &id)
        .await?
        .ok_or(AppError::NotFound("User not found".to_string()))?;
    
    Ok(Json(user.into()))
}

/// Update user by ID
async fn update_user_by_id(
    State(state): State<AppState>,
    Path(id): Path<String>,
    Extension(claims): Extension<Claims>,
    Json(payload): Json<UpdateUser>,
) -> Result<Json<UserResponse>, AppError> {
    // Users can only update their own profile unless they're admin
    if claims.sub != id && claims.role != "admin" {
        return Err(AppError::Forbidden("Access denied".to_string()));
    }
    
    let user = User::update(&state.db, &id, payload).await?;
    
    Ok(Json(user.into()))
}

/// Delete user by ID (admin only)
async fn delete_user_by_id(
    State(state): State<AppState>,
    Path(id): Path<String>,
    Extension(claims): Extension<Claims>,
) -> Result<Json<serde_json::Value>, AppError> {
    // Only admins can delete users
    if claims.role != "admin" {
        return Err(AppError::Forbidden("Admin access required".to_string()));
    }
    
    // Don't allow deleting yourself
    if claims.sub == id {
        return Err(AppError::ValidationError("Cannot delete your own account".to_string()));
    }
    
    User::delete(&state.db, &id).await?;
    
    Ok(Json(json!({
        "message": "User deleted successfully"
    })))
}
