// Image generation router
use axum::{
    Router,
    routing::post,
    response::Json,
    extract::State,
    Extension,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use reqwest;

use crate::AppState;
use crate::utils::jwt::Claims;
use crate::utils::errors::{AppError, Result};

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/generate", post(generate_image))
}

#[derive(Debug, Serialize, Deserialize)]
struct ImageGenerationRequest {
    prompt: String,
    #[serde(default)]
    negative_prompt: Option<String>,
    #[serde(default = "default_steps")]
    steps: u32,
    #[serde(default = "default_width")]
    width: u32,
    #[serde(default = "default_height")]
    height: u32,
    #[serde(default = "default_n")]
    n: u32,
    #[serde(default)]
    model: Option<String>,
    #[serde(flatten)]
    other: Option<Value>,
}

fn default_steps() -> u32 { 20 }
fn default_width() -> u32 { 512 }
fn default_height() -> u32 { 512 }
fn default_n() -> u32 { 1 }

#[derive(Debug, Serialize)]
struct ImageGenerationResponse {
    images: Vec<String>,
}

/// Generate image based on prompt
async fn generate_image(
    State(state): State<AppState>,
    Extension(_claims): Extension<Claims>,
    Json(payload): Json<ImageGenerationRequest>,
) -> Result<Json<Value>> {
    let engine = &state.config.image_generation_engine;
    
    match engine.as_str() {
        "automatic1111" => generate_with_automatic1111(&state, payload).await,
        "comfyui" => generate_with_comfyui(&state, payload).await,
        "openai" => generate_with_openai(&state, payload).await,
        _ => Err(AppError::BadRequest(format!(
            "Unsupported image generation engine: {}. Supported: automatic1111, comfyui, openai",
            engine
        ))),
    }
}

/// Generate image using AUTOMATIC1111 Stable Diffusion WebUI
async fn generate_with_automatic1111(
    state: &AppState,
    payload: ImageGenerationRequest,
) -> Result<Json<Value>> {
    let base_url = std::env::var("AUTOMATIC1111_BASE_URL")
        .unwrap_or_else(|_| "http://localhost:7860".to_string());
    
    let url = format!("{}/sdapi/v1/txt2img", base_url);
    
    let request_body = json!({
        "prompt": payload.prompt,
        "negative_prompt": payload.negative_prompt.unwrap_or_default(),
        "steps": payload.steps,
        "width": payload.width,
        "height": payload.height,
        "n_iter": payload.n,
    });
    
    let client = reqwest::Client::new();
    let response = client
        .post(&url)
        .json(&request_body)
        .send()
        .await
        .map_err(|e| AppError::InternalError(format!(
            "Failed to connect to AUTOMATIC1111: {}", e
        )))?;
    
    if !response.status().is_success() {
        let status = response.status();
        let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
        return Err(AppError::InternalError(format!(
            "AUTOMATIC1111 returned error {}: {}",
            status, error_text
        )));
    }
    
    let data: Value = response
        .json()
        .await
        .map_err(|e| AppError::InternalError(format!(
            "Failed to parse AUTOMATIC1111 response: {}", e
        )))?;
    
    Ok(Json(data))
}

/// Generate image using ComfyUI
async fn generate_with_comfyui(
    state: &AppState,
    payload: ImageGenerationRequest,
) -> Result<Json<Value>> {
    let base_url = std::env::var("COMFYUI_BASE_URL")
        .unwrap_or_else(|_| "http://localhost:8188".to_string());
    
    // ComfyUI has a more complex workflow-based API
    // This is a simplified version
    Err(AppError::InternalError(
        "ComfyUI integration not yet implemented".to_string()
    ))
}

/// Generate image using OpenAI DALL-E
async fn generate_with_openai(
    state: &AppState,
    payload: ImageGenerationRequest,
) -> Result<Json<Value>> {
    let api_key = state.config.openai_api_key.as_ref()
        .ok_or_else(|| AppError::BadRequest(
            "OpenAI API key not configured".to_string()
        ))?;
    
    let url = format!("{}/v1/images/generations", state.config.openai_api_base_url);
    
    let model = payload.model.unwrap_or_else(|| "dall-e-3".to_string());
    let size = format!("{}x{}", payload.width, payload.height);
    
    let request_body = json!({
        "model": model,
        "prompt": payload.prompt,
        "n": payload.n,
        "size": size,
    });
    
    let client = reqwest::Client::new();
    let response = client
        .post(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .header("Content-Type", "application/json")
        .json(&request_body)
        .send()
        .await
        .map_err(|e| AppError::InternalError(format!(
            "Failed to connect to OpenAI: {}", e
        )))?;
    
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
        .map_err(|e| AppError::InternalError(format!(
            "Failed to parse OpenAI response: {}", e
        )))?;
    
    Ok(Json(data))
}
