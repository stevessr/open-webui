use axum::{
    Router,
    routing::{get, post, delete},
    http::StatusCode,
    response::{IntoResponse, Json},
    extract::{State, Path},
};
use serde_json::json;

use crate::AppState;
use crate::models::models::{NewModel, UpdateModel};

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/", get(get_models))
        .route("/", post(create_model))
        .route("/:id", get(get_model_by_id))
        .route("/:id", post(update_model_by_id))
        .route("/:id", delete(delete_model_by_id))
}

/// Get all models
async fn get_models(
    State(_state): State<AppState>,
) -> impl IntoResponse {
    // TODO: Implement model listing
    // 1. Query database for all models
    // 2. Filter based on user permissions
    // 3. Return list
    
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "Model listing not yet implemented"
        }))
    )
}

/// Create new model
async fn create_model(
    State(_state): State<AppState>,
    Json(_payload): Json<NewModel>,
) -> impl IntoResponse {
    // TODO: Implement model creation
    // 1. Validate authorization (admin only)
    // 2. Create model in database
    // 3. Return created model
    
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "Model creation not yet implemented"
        }))
    )
}

/// Get model by ID
async fn get_model_by_id(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
) -> impl IntoResponse {
    // TODO: Implement model retrieval
    // 1. Query database for model
    // 2. Check user permissions
    // 3. Return model or 404
    
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "Model retrieval not yet implemented"
        }))
    )
}

/// Update model by ID
async fn update_model_by_id(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
    Json(_payload): Json<UpdateModel>,
) -> impl IntoResponse {
    // TODO: Implement model update
    // 1. Validate authorization (admin or owner)
    // 2. Update model in database
    // 3. Return updated model
    
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "Model update not yet implemented"
        }))
    )
}

/// Delete model by ID
async fn delete_model_by_id(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
) -> impl IntoResponse {
    // TODO: Implement model deletion
    // 1. Validate authorization (admin or owner)
    // 2. Delete model from database
    // 3. Return success message
    
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "Model deletion not yet implemented"
        }))
    )
}
