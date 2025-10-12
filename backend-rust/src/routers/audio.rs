// Audio processing router (TTS and STT)
use axum::{
    Router,
    routing::post,
    response::Json,
    extract::{State, Multipart},
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
        .route("/speech", post(text_to_speech))
        .route("/transcriptions", post(speech_to_text))
}

#[derive(Debug, Serialize, Deserialize)]
struct TTSRequest {
    input: String,
    #[serde(default)]
    model: Option<String>,
    #[serde(default)]
    voice: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct STTRequest {
    model: Option<String>,
    language: Option<String>,
}

/// Text-to-Speech endpoint
async fn text_to_speech(
    State(state): State<AppState>,
    Extension(_claims): Extension<Claims>,
    Json(payload): Json<TTSRequest>,
) -> Result<Json<Value>> {
    let engine = &state.config.audio_tts_engine;
    
    match engine.as_str() {
        "openai" => tts_openai(&state, payload).await,
        "elevenlabs" => tts_elevenlabs(&state, payload).await,
        "local" => tts_local(&state, payload).await,
        _ => Err(AppError::BadRequest(format!(
            "Unsupported TTS engine: {}. Supported: openai, elevenlabs, local",
            engine
        ))),
    }
}

/// Speech-to-Text endpoint
async fn speech_to_text(
    State(state): State<AppState>,
    Extension(_claims): Extension<Claims>,
    mut multipart: Multipart,
) -> Result<Json<Value>> {
    let engine = &state.config.audio_stt_engine;
    
    // Extract audio file from multipart
    let mut audio_data: Option<Vec<u8>> = None;
    let mut model: Option<String> = None;
    let mut language: Option<String> = None;
    
    while let Some(field) = multipart.next_field().await
        .map_err(|e| AppError::BadRequest(format!("Failed to read multipart: {}", e)))? {
        
        let name = field.name().unwrap_or("").to_string();
        
        match name.as_str() {
            "file" => {
                let data = field.bytes().await
                    .map_err(|e| AppError::BadRequest(format!("Failed to read audio file: {}", e)))?;
                audio_data = Some(data.to_vec());
            }
            "model" => {
                let text = field.text().await
                    .map_err(|e| AppError::BadRequest(format!("Failed to read model: {}", e)))?;
                model = Some(text);
            }
            "language" => {
                let text = field.text().await
                    .map_err(|e| AppError::BadRequest(format!("Failed to read language: {}", e)))?;
                language = Some(text);
            }
            _ => {}
        }
    }
    
    let audio_data = audio_data
        .ok_or_else(|| AppError::BadRequest("No audio file provided".to_string()))?;
    
    match engine.as_str() {
        "openai" => stt_openai(&state, audio_data, model, language).await,
        "whisper" => stt_whisper(&state, audio_data, model, language).await,
        _ => Err(AppError::BadRequest(format!(
            "Unsupported STT engine: {}. Supported: openai, whisper",
            engine
        ))),
    }
}

/// TTS using OpenAI
async fn tts_openai(
    state: &AppState,
    payload: TTSRequest,
) -> Result<Json<Value>> {
    let api_key = state.config.openai_api_key.as_ref()
        .ok_or_else(|| AppError::BadRequest("OpenAI API key not configured".to_string()))?;
    
    let url = format!("{}/v1/audio/speech", state.config.openai_api_base_url);
    let model = payload.model.unwrap_or_else(|| "tts-1".to_string());
    let voice = payload.voice.unwrap_or_else(|| "alloy".to_string());
    
    let request_body = json!({
        "model": model,
        "input": payload.input,
        "voice": voice,
    });
    
    let client = reqwest::Client::new();
    let response = client
        .post(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .json(&request_body)
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
    
    // Return audio data as base64
    let audio_bytes = response.bytes().await
        .map_err(|e| AppError::InternalError(format!("Failed to read audio: {}", e)))?;
    
    use base64::{Engine as _, engine::general_purpose};
    let audio_base64 = general_purpose::STANDARD.encode(&audio_bytes);
    
    Ok(Json(json!({
        "audio": audio_base64,
        "format": "mp3"
    })))
}

/// TTS using ElevenLabs
async fn tts_elevenlabs(
    _state: &AppState,
    _payload: TTSRequest,
) -> Result<Json<Value>> {
    Err(AppError::InternalError("ElevenLabs TTS not yet implemented".to_string()))
}

/// TTS using local engine
async fn tts_local(
    _state: &AppState,
    _payload: TTSRequest,
) -> Result<Json<Value>> {
    Err(AppError::InternalError("Local TTS not yet implemented".to_string()))
}

/// STT using OpenAI Whisper API
async fn stt_openai(
    state: &AppState,
    audio_data: Vec<u8>,
    model: Option<String>,
    language: Option<String>,
) -> Result<Json<Value>> {
    let api_key = state.config.openai_api_key.as_ref()
        .ok_or_else(|| AppError::BadRequest("OpenAI API key not configured".to_string()))?;
    
    let url = format!("{}/v1/audio/transcriptions", state.config.openai_api_base_url);
    let model = model.unwrap_or_else(|| "whisper-1".to_string());
    
    // Create multipart form
    let part = reqwest::multipart::Part::bytes(audio_data)
        .file_name("audio.mp3");
    
    let mut form = reqwest::multipart::Form::new()
        .part("file", part)
        .text("model", model);
    
    if let Some(lang) = language {
        form = form.text("language", lang);
    }
    
    let client = reqwest::Client::new();
    let response = client
        .post(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .multipart(form)
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
    
    let data: Value = response.json().await
        .map_err(|e| AppError::InternalError(format!("Failed to parse response: {}", e)))?;
    
    Ok(Json(data))
}

/// STT using local Whisper
async fn stt_whisper(
    _state: &AppState,
    _audio_data: Vec<u8>,
    _model: Option<String>,
    _language: Option<String>,
) -> Result<Json<Value>> {
    Err(AppError::InternalError("Local Whisper STT not yet implemented".to_string()))
}
