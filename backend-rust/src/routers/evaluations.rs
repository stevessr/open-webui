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
pub struct Evaluation {
    pub id: String,
    pub user_id: String,
    pub model_id: String,
    pub dataset_id: Option<String>,
    pub metrics: serde_json::Value,
    pub results: serde_json::Value,
    pub status: String,
    pub created_at: i64,
    pub updated_at: i64,
}

#[derive(Debug, Deserialize)]
pub struct CreateEvaluationRequest {
    pub model_id: String,
    pub dataset_id: Option<String>,
    pub metrics: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct RunEvaluationRequest {
    pub prompt: String,
    pub expected_output: Option<String>,
}

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/", get(list_evaluations).post(create_evaluation))
        .route("/:id", get(get_evaluation).delete(delete_evaluation))
        .route("/:id/run", post(run_evaluation))
        .route("/:id/results", get(get_evaluation_results))
}

/// List all evaluations
async fn list_evaluations(
    State(_state): State<AppState>,
) -> impl IntoResponse {
    let evaluations: Vec<Evaluation> = vec![];
    Json(evaluations)
}

/// Create new evaluation
async fn create_evaluation(
    State(_state): State<AppState>,
    Json(_payload): Json<CreateEvaluationRequest>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "Evaluation creation not yet implemented"
        }))
    )
}

/// Get evaluation by ID
async fn get_evaluation(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "Evaluation retrieval not yet implemented"
        }))
    )
}

/// Delete evaluation
async fn delete_evaluation(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
) -> impl IntoResponse {
    Json(json!({
        "success": true,
        "message": "Evaluation deleted"
    }))
}

/// Run evaluation
async fn run_evaluation(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
    Json(_payload): Json<RunEvaluationRequest>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "Evaluation run not yet implemented"
        }))
    )
}

/// Get evaluation results
async fn get_evaluation_results(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
) -> impl IntoResponse {
    (
        StatusCode::NOT_IMPLEMENTED,
        Json(json!({
            "detail": "Evaluation results not yet implemented"
        }))
    )
}
