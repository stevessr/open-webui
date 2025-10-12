// File upload and management router
use axum::{
    Router,
    routing::{get, post, delete},
    response::{IntoResponse, Json},
    extract::{State, Path, Multipart},
    Extension,
    http::StatusCode,
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::path::PathBuf;
use tokio::fs;
use tokio::io::AsyncWriteExt;
use uuid::Uuid;

use crate::AppState;
use crate::utils::jwt::Claims;
use crate::utils::errors::{AppError, Result};

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/", post(upload_file))
        .route("/", get(list_files))
        .route("/:id", get(get_file))
        .route("/:id", delete(delete_file))
}

#[derive(Debug, Serialize)]
struct FileInfo {
    id: String,
    filename: String,
    size: u64,
    content_type: Option<String>,
    created_at: i64,
}

#[derive(Debug, Serialize)]
struct UploadResponse {
    id: String,
    filename: String,
    url: String,
}

/// Upload a file
async fn upload_file(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    mut multipart: Multipart,
) -> Result<Json<UploadResponse>> {
    let upload_dir = PathBuf::from(&state.config.upload_dir);
    
    // Create upload directory if it doesn't exist
    fs::create_dir_all(&upload_dir)
        .await
        .map_err(|e| AppError::InternalError(format!("Failed to create upload directory: {}", e)))?;
    
    while let Some(field) = multipart.next_field().await
        .map_err(|e| AppError::BadRequest(format!("Failed to read multipart field: {}", e)))? {
        
        let name = field.name().unwrap_or("file").to_string();
        let filename = field.file_name()
            .ok_or_else(|| AppError::BadRequest("No filename provided".to_string()))?
            .to_string();
        
        let content_type = field.content_type()
            .map(|ct| ct.to_string());
        
        let data = field.bytes().await
            .map_err(|e| AppError::BadRequest(format!("Failed to read file data: {}", e)))?;
        
        // Check file size
        if data.len() > state.config.file_max_size {
            return Err(AppError::BadRequest(format!(
                "File size exceeds maximum allowed size of {} bytes",
                state.config.file_max_size
            )));
        }
        
        // Generate unique file ID
        let file_id = Uuid::new_v4().to_string();
        let file_ext = std::path::Path::new(&filename)
            .extension()
            .and_then(|s| s.to_str())
            .unwrap_or("");
        
        let stored_filename = if !file_ext.is_empty() {
            format!("{}_{}.{}", claims.sub, file_id, file_ext)
        } else {
            format!("{}_{}", claims.sub, file_id)
        };
        
        let file_path = upload_dir.join(&stored_filename);
        
        // Write file to disk
        let mut file = fs::File::create(&file_path)
            .await
            .map_err(|e| AppError::InternalError(format!("Failed to create file: {}", e)))?;
        
        file.write_all(&data)
            .await
            .map_err(|e| AppError::InternalError(format!("Failed to write file: {}", e)))?;
        
        // TODO: Store file metadata in database
        
        let url = format!("/api/files/{}", file_id);
        
        return Ok(Json(UploadResponse {
            id: file_id,
            filename: filename.clone(),
            url,
        }));
    }
    
    Err(AppError::BadRequest("No file uploaded".to_string()))
}

/// List user's files
async fn list_files(
    State(_state): State<AppState>,
    Extension(_claims): Extension<Claims>,
) -> Result<Json<Vec<FileInfo>>> {
    // TODO: Implement database query for user's files
    Ok(Json(vec![]))
}

/// Get file by ID
async fn get_file(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Path(file_id): Path<String>,
) -> Result<impl IntoResponse> {
    let upload_dir = PathBuf::from(&state.config.upload_dir);
    
    // TODO: Query database for file metadata and verify ownership
    // For now, we'll search for the file by pattern
    
    let pattern = format!("{}_{}.*", claims.sub, file_id);
    let mut entries = fs::read_dir(&upload_dir)
        .await
        .map_err(|e| AppError::InternalError(format!("Failed to read upload directory: {}", e)))?;
    
    while let Some(entry) = entries.next_entry()
        .await
        .map_err(|e| AppError::InternalError(format!("Failed to read directory entry: {}", e)))? {
        
        let filename = entry.file_name().to_string_lossy().to_string();
        
        if filename.starts_with(&format!("{}_{}", claims.sub, file_id)) {
            let file_path = entry.path();
            let content = fs::read(&file_path)
                .await
                .map_err(|e| AppError::InternalError(format!("Failed to read file: {}", e)))?;
            
            // Determine content type from extension
            let content_type = mime_guess::from_path(&file_path)
                .first_or_octet_stream()
                .to_string();
            
            return Ok((
                [(axum::http::header::CONTENT_TYPE, content_type)],
                content,
            ).into_response());
        }
    }
    
    Err(AppError::NotFound("File not found".to_string()))
}

/// Delete file by ID
async fn delete_file(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Path(file_id): Path<String>,
) -> Result<StatusCode> {
    let upload_dir = PathBuf::from(&state.config.upload_dir);
    
    // TODO: Query database for file metadata and verify ownership
    // For now, we'll search for the file by pattern
    
    let pattern = format!("{}_{}.*", claims.sub, file_id);
    let mut entries = fs::read_dir(&upload_dir)
        .await
        .map_err(|e| AppError::InternalError(format!("Failed to read upload directory: {}", e)))?;
    
    while let Some(entry) = entries.next_entry()
        .await
        .map_err(|e| AppError::InternalError(format!("Failed to read directory entry: {}", e)))? {
        
        let filename = entry.file_name().to_string_lossy().to_string();
        
        if filename.starts_with(&format!("{}_{}", claims.sub, file_id)) {
            let file_path = entry.path();
            fs::remove_file(&file_path)
                .await
                .map_err(|e| AppError::InternalError(format!("Failed to delete file: {}", e)))?;
            
            // TODO: Delete file metadata from database
            
            return Ok(StatusCode::NO_CONTENT);
        }
    }
    
    Err(AppError::NotFound("File not found".to_string()))
}
