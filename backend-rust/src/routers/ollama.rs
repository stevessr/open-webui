// Ollama integration router
use axum::{
    Router,
    routing::{get, post},
    http::StatusCode,
    response::{IntoResponse, Json},
    extract::{State, Path},
    body::Body,
    Extension,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use reqwest;

use crate::AppState;
use crate::utils::jwt::Claims;
use crate::utils::errors::AppError;

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/api/tags", get(list_models))
        .route("/api/generate", post(generate_completion))
        .route("/api/chat", post(chat_completion))
        .route("/api/embeddings", post(generate_embeddings))
}

#[derive(Debug, Serialize, Deserialize)]
struct GenerateRequest {
    model: String,
    prompt: String,
    #[serde(default)]
    stream: bool,
    #[serde(flatten)]
    options: Option<Value>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ChatRequest {
    model: String,
    messages: Vec<ChatMessage>,
    #[serde(default)]
    stream: bool,
    #[serde(flatten)]
    options: Option<Value>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ChatMessage {
    role: String,
    content: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct EmbeddingsRequest {
    model: String,
    prompt: String,
}

/// List available models from Ollama
async fn list_models(
    State(state): State<AppState>,
    Extension(_claims): Extension<Claims>,
) -> Result<Json<Value>, AppError> {
    let ollama_url = &state.config.ollama_base_url;
    let url = format!("{}/api/tags", ollama_url);
    
    let client = reqwest::Client::new();
    let response = client
        .get(&url)
        .send()
        .await
        .map_err(|e| AppError::InternalError(format!("Failed to connect to Ollama: {}", e)))?;
    
    if !response.status().is_success() {
        return Err(AppError::InternalError(format!(
            "Ollama returned error: {}",
            response.status()
        )));
    }
    
    let data: Value = response
        .json()
        .await
        .map_err(|e| AppError::InternalError(format!("Failed to parse Ollama response: {}", e)))?;
    
    Ok(Json(data))
}

/// Generate completion using Ollama
async fn generate_completion(
    State(state): State<AppState>,
    Extension(_claims): Extension<Claims>,
    Json(payload): Json<GenerateRequest>,
) -> Result<Json<Value>, AppError> {
    let ollama_url = &state.config.ollama_base_url;
    let url = format!("{}/api/generate", ollama_url);
    
    let client = reqwest::Client::new();
    let response = client
        .post(&url)
        .json(&payload)
        .send()
        .await
        .map_err(|e| AppError::InternalError(format!("Failed to connect to Ollama: {}", e)))?;
    
    if !response.status().is_success() {
        return Err(AppError::InternalError(format!(
            "Ollama returned error: {}",
            response.status()
        )));
    }
    
    let data: Value = response
        .json()
        .await
        .map_err(|e| AppError::InternalError(format!("Failed to parse Ollama response: {}", e)))?;
    
    Ok(Json(data))
}

/// Chat completion using Ollama
async fn chat_completion(
    State(state): State<AppState>,
    Extension(_claims): Extension<Claims>,
    Json(payload): Json<ChatRequest>,
) -> Result<Json<Value>, AppError> {
    let ollama_url = &state.config.ollama_base_url;
    let url = format!("{}/api/chat", ollama_url);
    
    let client = reqwest::Client::new();
    let response = client
        .post(&url)
        .json(&payload)
        .send()
        .await
        .map_err(|e| AppError::InternalError(format!("Failed to connect to Ollama: {}", e)))?;
    
    if !response.status().is_success() {
        return Err(AppError::InternalError(format!(
            "Ollama returned error: {}",
            response.status()
        )));
    }
    
    let data: Value = response
        .json()
        .await
        .map_err(|e| AppError::InternalError(format!("Failed to parse Ollama response: {}", e)))?;
    
    Ok(Json(data))
}

/// Generate embeddings using Ollama
async fn generate_embeddings(
    State(state): State<AppState>,
    Extension(_claims): Extension<Claims>,
    Json(payload): Json<EmbeddingsRequest>,
) -> Result<Json<Value>, AppError> {
    let ollama_url = &state.config.ollama_base_url;
    let url = format!("{}/api/embeddings", ollama_url);
    
    let client = reqwest::Client::new();
    let response = client
        .post(&url)
        .json(&payload)
        .send()
        .await
        .map_err(|e| AppError::InternalError(format!("Failed to connect to Ollama: {}", e)))?;
    
    if !response.status().is_success() {
        return Err(AppError::InternalError(format!(
            "Ollama returned error: {}",
            response.status()
        )));
    }
    
    let data: Value = response
        .json()
        .await
        .map_err(|e| AppError::InternalError(format!("Failed to parse Ollama response: {}", e)))?;
    
    Ok(Json(data))
}
