use axum::{
    Router,
    routing::{get, post, delete},
    http::StatusCode,
    response::{IntoResponse, Json},
    extract::{State, Path},
};
use serde::{Deserialize, Serialize};
use serde_json::json;

use crate::AppState;

#[derive(Debug, Serialize, Deserialize)]
pub struct Function {
    pub id: String,
    pub user_id: String,
    pub name: String,
    pub description: Option<String>,
    pub content: String,
    pub is_active: bool,
    pub is_global: bool,
    pub data: serde_json::Value,
    pub created_at: i64,
    pub updated_at: i64,
}

#[derive(Debug, Deserialize)]
pub struct CreateFunctionRequest {
    pub id: String,
    pub name: String,
    pub description: Option<String>,
    pub content: String,
    pub is_active: bool,
    pub is_global: bool,
}

#[derive(Debug, Deserialize)]
pub struct ExecuteFunctionRequest {
    pub args: serde_json::Value,
}

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/", get(list_functions).post(create_function))
        .route("/:id", get(get_function).post(update_function).delete(delete_function))
        .route("/:id/execute", post(execute_function))
        .route("/:id/toggle", post(toggle_function))
}

/// List all functions
async fn list_functions(
    State(_state): State<AppState>,
) -> impl IntoResponse {
    let functions: Vec<Function> = vec![];
    Json(functions)
}

/// Create new function
async fn create_function(
    State(_state): State<AppState>,
    Json(_payload): Json<CreateFunctionRequest>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "Function creation not yet implemented"
        }))
    )
}

/// Get function by ID
async fn get_function(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "Function retrieval not yet implemented"
        }))
    )
}

/// Update function
async fn update_function(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
    Json(_payload): Json<CreateFunctionRequest>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "Function update not yet implemented"
        }))
    )
}

/// Delete function
async fn delete_function(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
) -> impl IntoResponse {
    Json(json!({
        "success": true,
        "message": "Function deleted"
    }))
}

/// Execute function
async fn execute_function(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
    Json(_payload): Json<ExecuteFunctionRequest>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "Function execution not yet implemented"
        }))
    )
}

/// Toggle function active state
async fn toggle_function(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "Function toggle not yet implemented"
        }))
    )
}
