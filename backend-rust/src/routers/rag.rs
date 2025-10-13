// RAG (Retrieval Augmented Generation) router
use axum::{
    Router,
    routing::{get, post},
    response::Json,
    extract::{State, Path},
    Extension,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

use crate::AppState;
use crate::utils::jwt::Claims;
use crate::utils::errors::{AppError, Result};

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/query", post(query_knowledge))
        .route("/embed", post(embed_documents))
}

#[derive(Debug, Serialize, Deserialize)]
struct QueryRequest {
    query: String,
    #[serde(default = "default_top_k")]
    top_k: usize,
    #[serde(default)]
    filter: Option<Value>,
}

#[derive(Debug, Serialize, Deserialize)]
struct EmbedRequest {
    documents: Vec<String>,
    #[serde(default)]
    metadata: Option<Vec<Value>>,
}

#[derive(Debug, Serialize)]
struct QueryResponse {
    results: Vec<SearchResult>,
}

#[derive(Debug, Serialize)]
struct SearchResult {
    document: String,
    score: f32,
    #[serde(skip_serializing_if = "Option::is_none")]
    metadata: Option<Value>,
}

fn default_top_k() -> usize { 5 }

/// Query knowledge base with semantic search
async fn query_knowledge(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Json(payload): Json<QueryRequest>,
) -> Result<Json<QueryResponse>> {
    // Generate embedding for the query
    let embedding = generate_embedding(&state, &payload.query).await?;
    
    // Perform vector similarity search
    // TODO: Implement actual vector database search (e.g., Qdrant, Weaviate, Pinecone)
    // For now, return placeholder
    
    let results = vec![
        SearchResult {
            document: "Sample document 1 content...".to_string(),
            score: 0.92,
            metadata: Some(json!({"source": "doc1.pdf", "page": 1})),
        },
        SearchResult {
            document: "Sample document 2 content...".to_string(),
            score: 0.87,
            metadata: Some(json!({"source": "doc2.pdf", "page": 5})),
        },
    ];
    
    Ok(Json(QueryResponse { results }))
}

/// Embed documents and store in vector database
async fn embed_documents(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Json(payload): Json<EmbedRequest>,
) -> Result<Json<Value>> {
    let mut embeddings = Vec::new();
    
    // Generate embeddings for all documents
    for doc in &payload.documents {
        let embedding = generate_embedding(&state, doc).await?;
        embeddings.push(embedding);
    }
    
    // TODO: Store embeddings in vector database
    // For now, just return success
    
    Ok(Json(json!({
        "status": "success",
        "count": embeddings.len(),
        "message": "Documents embedded successfully (not yet persisted - vector DB integration pending)"
    })))
}

/// Generate embedding using configured engine
async fn generate_embedding(state: &AppState, text: &str) -> Result<Vec<f32>> {
    let engine = &state.config.rag_embedding_engine;
    let model = &state.config.rag_embedding_model;
    
    match engine.as_str() {
        "ollama" => generate_embedding_ollama(state, text, model).await,
        "openai" => generate_embedding_openai(state, text, model).await,
        _ => Err(AppError::BadRequest(format!(
            "Unsupported embedding engine: {}. Supported: ollama, openai",
            engine
        ))),
    }
}

/// Generate embedding using Ollama
async fn generate_embedding_ollama(
    state: &AppState,
    text: &str,
    model: &str,
) -> Result<Vec<f32>> {
    let url = format!("{}/api/embeddings", state.config.ollama_base_url);
    
    let payload = json!({
        "model": model,
        "prompt": text,
    });
    
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
        .map_err(|e| AppError::InternalError(format!("Failed to parse response: {}", e)))?;
    
    // Extract embedding vector
    let embedding = data["embedding"]
        .as_array()
        .ok_or_else(|| AppError::InternalError("No embedding in response".to_string()))?
        .iter()
        .filter_map(|v| v.as_f64().map(|f| f as f32))
        .collect();
    
    Ok(embedding)
}

/// Generate embedding using OpenAI
async fn generate_embedding_openai(
    state: &AppState,
    text: &str,
    model: &str,
) -> Result<Vec<f32>> {
    let api_key = state.config.openai_api_key.as_ref()
        .ok_or_else(|| AppError::BadRequest("OpenAI API key not configured".to_string()))?;
    
    let url = format!("{}/v1/embeddings", state.config.openai_api_base_url);
    
    let payload = json!({
        "model": model,
        "input": text,
    });
    
    let client = reqwest::Client::new();
    let response = client
        .post(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .json(&payload)
        .send()
        .await
        .map_err(|e| AppError::InternalError(format!("Failed to connect to OpenAI: {}", e)))?;
    
    if !response.status().is_success() {
        return Err(AppError::InternalError(format!(
            "OpenAI returned error: {}",
            response.status()
        )));
    }
    
    let data: Value = response
        .json()
        .await
        .map_err(|e| AppError::InternalError(format!("Failed to parse response: {}", e)))?;
    
    // Extract embedding vector from first data item
    let embedding = data["data"][0]["embedding"]
        .as_array()
        .ok_or_else(|| AppError::InternalError("No embedding in response".to_string()))?
        .iter()
        .filter_map(|v| v.as_f64().map(|f| f as f32))
        .collect();
    
    Ok(embedding)
}
