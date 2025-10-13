// OpenAI integration router
use axum::{
    Router,
    routing::post,
    response::{IntoResponse, Json},
    extract::State,
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
        .route("/chat/completions", post(chat_completions))
        .route("/v1/chat/completions", post(chat_completions))
        .route("/embeddings", post(create_embeddings))
        .route("/v1/embeddings", post(create_embeddings))
}

#[derive(Debug, Serialize, Deserialize)]
struct ChatCompletionRequest {
    model: String,
    messages: Vec<ChatMessage>,
    #[serde(default)]
    temperature: Option<f32>,
    #[serde(default)]
    max_tokens: Option<i32>,
    #[serde(default)]
    stream: bool,
    #[serde(flatten)]
    other: Option<Value>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ChatMessage {
    role: String,
    content: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct EmbeddingRequest {
    model: String,
    input: EmbeddingInput,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(untagged)]
enum EmbeddingInput {
    Single(String),
    Multiple(Vec<String>),
}

/// Chat completions endpoint (OpenAI compatible)
async fn chat_completions(
    State(state): State<AppState>,
    Extension(_claims): Extension<Claims>,
    Json(payload): Json<ChatCompletionRequest>,
) -> Result<Json<Value>, AppError> {
    // Check if we should use OpenAI or fallback to Ollama
    let api_key = state.config.openai_api_key.as_ref();
    
    if let Some(key) = api_key {
        // Use OpenAI
        let url = format!("{}/v1/chat/completions", state.config.openai_api_base_url);
        
        let client = reqwest::Client::new();
        let response = client
            .post(&url)
            .header("Authorization", format!("Bearer {}", key))
            .header("Content-Type", "application/json")
            .json(&payload)
            .send()
            .await
            .map_err(|e| AppError::InternalError(format!("Failed to connect to OpenAI: {}", e)))?;
        
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
            return Err(AppError::InternalError(format!(
                "OpenAI returned error {}: {}",
                status, error_text
            )));
        }
        
        let data: Value = response
            .json()
            .await
            .map_err(|e| AppError::InternalError(format!("Failed to parse OpenAI response: {}", e)))?;
        
        Ok(Json(data))
    } else {
        // Fallback to Ollama
        Err(AppError::BadRequest(
            "OpenAI API key not configured. Please set OPENAI_API_KEY.".to_string()
        ))
    }
}

/// Embeddings endpoint (OpenAI compatible)
async fn create_embeddings(
    State(state): State<AppState>,
    Extension(_claims): Extension<Claims>,
    Json(payload): Json<EmbeddingRequest>,
) -> Result<Json<Value>, AppError> {
    let api_key = state.config.openai_api_key.as_ref();
    
    if let Some(key) = api_key {
        // Use OpenAI
        let url = format!("{}/v1/embeddings", state.config.openai_api_base_url);
        
        let client = reqwest::Client::new();
        let response = client
            .post(&url)
            .header("Authorization", format!("Bearer {}", key))
            .header("Content-Type", "application/json")
            .json(&payload)
            .send()
            .await
            .map_err(|e| AppError::InternalError(format!("Failed to connect to OpenAI: {}", e)))?;
        
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
            return Err(AppError::InternalError(format!(
                "OpenAI returned error {}: {}",
                status, error_text
            )));
        }
        
        let data: Value = response
            .json()
            .await
            .map_err(|e| AppError::InternalError(format!("Failed to parse OpenAI response: {}", e)))?;
        
        Ok(Json(data))
    } else {
        // Fallback message
        Err(AppError::BadRequest(
            "OpenAI API key not configured. Please set OPENAI_API_KEY.".to_string()
        ))
    }
}
