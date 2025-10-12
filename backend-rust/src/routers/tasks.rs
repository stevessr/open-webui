// Tasks management router
use axum::{
    Router,
    routing::{get, post},
    response::Json,
    extract::{State, Path},
    Extension,
    http::StatusCode,
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use chrono::Utc;

use crate::AppState;
use crate::utils::jwt::Claims;
use crate::utils::errors::{AppError, Result};

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/", get(list_tasks))
        .route("/", post(create_task))
        .route("/:id", get(get_task))
        .route("/:id/stop", post(stop_task))
        .route("/chat/:chat_id", get(list_tasks_by_chat))
}

#[derive(Debug, Serialize, Deserialize)]
struct Task {
    id: String,
    user_id: String,
    chat_id: Option<String>,
    task_type: TaskType,
    status: TaskStatus,
    progress: f32,
    result: Option<serde_json::Value>,
    error: Option<String>,
    created_at: i64,
    updated_at: i64,
    started_at: Option<i64>,
    completed_at: Option<i64>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "snake_case")]
enum TaskType {
    TitleGeneration,
    TagGeneration,
    FollowUpGeneration,
    QueryGeneration,
    ImageGeneration,
    AudioTranscription,
    DocumentProcessing,
    EmbeddingGeneration,
    Custom(String),
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
#[serde(rename_all = "snake_case")]
enum TaskStatus {
    Pending,
    Running,
    Completed,
    Failed,
    Cancelled,
}

#[derive(Debug, Deserialize)]
struct CreateTaskRequest {
    task_type: TaskType,
    chat_id: Option<String>,
    params: Option<serde_json::Value>,
}

/// List user's tasks
async fn list_tasks(
    State(_state): State<AppState>,
    Extension(claims): Extension<Claims>,
) -> Result<Json<Vec<Task>>> {
    // TODO: Query database for user's tasks
    Ok(Json(vec![]))
}

/// Create new task
async fn create_task(
    State(_state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Json(payload): Json<CreateTaskRequest>,
) -> Result<Json<Task>> {
    let now = Utc::now().timestamp();
    let task_id = uuid::Uuid::new_v4().to_string();
    
    let task = Task {
        id: task_id.clone(),
        user_id: claims.sub.clone(),
        chat_id: payload.chat_id,
        task_type: payload.task_type,
        status: TaskStatus::Pending,
        progress: 0.0,
        result: None,
        error: None,
        created_at: now,
        updated_at: now,
        started_at: None,
        completed_at: None,
    };
    
    // TODO: Store in database
    // TODO: Queue task for background processing
    
    Ok(Json(task))
}

/// Get task by ID
async fn get_task(
    State(_state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Path(id): Path<String>,
) -> Result<Json<Task>> {
    // TODO: Query database for task
    // Verify ownership
    
    Err(AppError::NotFound("Task not found".to_string()))
}

/// Stop/cancel a running task
async fn stop_task(
    State(_state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Path(id): Path<String>,
) -> Result<Json<serde_json::Value>> {
    // TODO: Query database for task
    // Verify ownership
    // Send cancellation signal to background worker
    // Update task status to Cancelled
    
    Ok(Json(json!({
        "status": "cancelled",
        "message": "Task cancellation requested"
    })))
}

/// List tasks for a specific chat
async fn list_tasks_by_chat(
    State(_state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Path(chat_id): Path<String>,
) -> Result<Json<Vec<Task>>> {
    // TODO: Query database for tasks by chat_id
    // Verify user has access to the chat
    
    Ok(Json(vec![]))
}
