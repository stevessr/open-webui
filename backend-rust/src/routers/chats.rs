use axum::{
    Router,
    routing::{get, post, delete},
    http::StatusCode,
    response::{IntoResponse, Json},
    extract::{State, Path},
    Extension,
};
use serde_json::json;
use uuid::Uuid;

use crate::AppState;
use crate::models::chats::{NewChat, UpdateChat, Chat};
use crate::utils::jwt::Claims;
use crate::utils::errors::AppError;

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/", get(get_chats))
        .route("/", post(create_chat))
        .route("/:id", get(get_chat_by_id))
        .route("/:id", post(update_chat_by_id))
        .route("/:id", delete(delete_chat_by_id))
        .route("/:id/archive", post(archive_chat))
}

/// Get all chats for current user
async fn get_chats(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
) -> Result<Json<Vec<Chat>>, AppError> {
    let chats = Chat::get_by_user(&state.db, &claims.sub).await?;
    Ok(Json(chats))
}

/// Create new chat
async fn create_chat(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Json(payload): Json<NewChat>,
) -> Result<Json<Chat>, AppError> {
    // Ensure user_id matches authenticated user
    if payload.user_id != claims.sub {
        return Err(AppError::Forbidden("Cannot create chat for another user".to_string()));
    }
    
    let chat = Chat::create(&state.db, payload).await?;
    Ok(Json(chat))
}

/// Get chat by ID
async fn get_chat_by_id(
    State(state): State<AppState>,
    Path(id): Path<String>,
    Extension(claims): Extension<Claims>,
) -> Result<Json<Chat>, AppError> {
    let chat = Chat::get_by_id(&state.db, &id)
        .await?
        .ok_or(AppError::NotFound("Chat not found".to_string()))?;
    
    // Verify ownership
    if chat.user_id != claims.sub && claims.role != "admin" {
        return Err(AppError::Forbidden("Access denied".to_string()));
    }
    
    Ok(Json(chat))
}

/// Update chat by ID
async fn update_chat_by_id(
    State(state): State<AppState>,
    Path(id): Path<String>,
    Extension(claims): Extension<Claims>,
    Json(payload): Json<UpdateChat>,
) -> Result<Json<Chat>, AppError> {
    // Verify ownership
    let existing = Chat::get_by_id(&state.db, &id)
        .await?
        .ok_or(AppError::NotFound("Chat not found".to_string()))?;
    
    if existing.user_id != claims.sub && claims.role != "admin" {
        return Err(AppError::Forbidden("Access denied".to_string()));
    }
    
    let chat = Chat::update(&state.db, &id, payload).await?;
    Ok(Json(chat))
}

/// Delete chat by ID
async fn delete_chat_by_id(
    State(state): State<AppState>,
    Path(id): Path<String>,
    Extension(claims): Extension<Claims>,
) -> Result<Json<serde_json::Value>, AppError> {
    // Verify ownership
    let existing = Chat::get_by_id(&state.db, &id)
        .await?
        .ok_or(AppError::NotFound("Chat not found".to_string()))?;
    
    if existing.user_id != claims.sub && claims.role != "admin" {
        return Err(AppError::Forbidden("Access denied".to_string()));
    }
    
    Chat::delete(&state.db, &id).await?;
    
    Ok(Json(json!({
        "message": "Chat deleted successfully"
    })))
}

/// Archive chat
async fn archive_chat(
    State(state): State<AppState>,
    Path(id): Path<String>,
    Extension(claims): Extension<Claims>,
) -> Result<Json<serde_json::Value>, AppError> {
    // Verify ownership
    let existing = Chat::get_by_id(&state.db, &id)
        .await?
        .ok_or(AppError::NotFound("Chat not found".to_string()))?;
    
    if existing.user_id != claims.sub && claims.role != "admin" {
        return Err(AppError::Forbidden("Access denied".to_string()));
    }
    
    Chat::set_archived(&state.db, &id, true).await?;
    
    Ok(Json(json!({
        "message": "Chat archived successfully"
    })))
}
