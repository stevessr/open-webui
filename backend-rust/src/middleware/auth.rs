use axum::{
    extract::{Request, State},
    middleware::Next,
    response::Response,
    http::{header, StatusCode},
};

use crate::utils::jwt::verify_token;
use crate::AppState;

/// Authentication middleware
pub async fn auth_middleware(
    State(state): State<AppState>,
    mut req: Request,
    next: Next,
) -> Result<Response, StatusCode> {
    // Extract the authorization header
    let auth_header = req
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|h| h.to_str().ok());
    
    if let Some(auth_header) = auth_header {
        // Check if it's a Bearer token
        if let Some(token) = auth_header.strip_prefix("Bearer ") {
            // Verify the token
            match verify_token(token, &state.config.webui_secret_key) {
                Ok(claims) => {
                    // Add user information to request extensions
                    req.extensions_mut().insert(claims);
                    return Ok(next.run(req).await);
                }
                Err(_) => {
                    return Err(StatusCode::UNAUTHORIZED);
                }
            }
        }
    }
    
    // No valid authentication found
    Err(StatusCode::UNAUTHORIZED)
}

/// Optional authentication middleware (doesn't fail if no auth is present)
pub async fn optional_auth_middleware(
    State(state): State<AppState>,
    mut req: Request,
    next: Next,
) -> Response {
    // Extract the authorization header
    let auth_header = req
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|h| h.to_str().ok());
    
    if let Some(auth_header) = auth_header {
        if let Some(token) = auth_header.strip_prefix("Bearer ") {
            if let Ok(claims) = verify_token(token, &state.config.webui_secret_key) {
                req.extensions_mut().insert(claims);
            }
        }
    }
    
    next.run(req).await
}
