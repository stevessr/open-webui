use axum::{
    Router,
    routing::{post, get},
    http::StatusCode,
    response::{IntoResponse, Json},
    extract::State,
};
use serde_json::json;

use crate::AppState;
use crate::models::auth::{LoginRequest, SignupRequest, TokenResponse};
use crate::models::users::{User, UserRole, NewUser};
use crate::models::auth::Auth;
use crate::utils::{password, jwt};
use crate::utils::errors::AppError;

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/signin", post(signin))
        .route("/signup", post(signup))
        .route("/signout", post(signout))
}

/// Sign in endpoint
async fn signin(
    State(state): State<AppState>,
    Json(payload): Json<LoginRequest>,
) -> Result<Json<TokenResponse>, AppError> {
    // Get auth by email
    let auth = Auth::get_by_email(&state.db, &payload.email)
        .await?
        .ok_or(AppError::AuthError("Invalid email or password".to_string()))?;
    
    // Verify password
    let valid = password::verify_password(&payload.password, &auth.password)?;
    if !valid {
        return Err(AppError::AuthError("Invalid email or password".to_string()));
    }
    
    // Get user info
    let user = User::get_by_id(&state.db, &auth.id)
        .await?
        .ok_or(AppError::AuthError("User not found".to_string()))?;
    
    // Create JWT token
    let token = jwt::create_token(
        user.id.clone(),
        user.email.clone(),
        user.role.to_string(),
        &state.config.webui_secret_key,
    )?;
    
    Ok(Json(TokenResponse {
        token,
        token_type: "Bearer".to_string(),
    }))
}

/// Sign up endpoint
async fn signup(
    State(state): State<AppState>,
    Json(payload): Json<SignupRequest>,
) -> Result<Json<TokenResponse>, AppError> {
    // Check if signup is enabled
    if !state.config.enable_signup {
        return Err(AppError::Forbidden("Signup is disabled".to_string()));
    }
    
    // Check if user already exists
    if let Some(_) = User::get_by_email(&state.db, &payload.email).await? {
        return Err(AppError::ValidationError("User with this email already exists".to_string()));
    }
    
    // Check if this is the first user (make them admin)
    let user_count = User::count(&state.db).await?;
    let role = if user_count == 0 {
        UserRole::Admin
    } else {
        UserRole::User
    };
    
    // Hash password
    let password_hash = password::hash_password(&payload.password)?;
    
    // Create user
    let new_user = NewUser {
        name: payload.name.clone(),
        email: payload.email.clone(),
        password: payload.password.clone(), // Not stored, just for validation
        role,
        profile_image_url: "/user.png".to_string(),
    };
    
    let user = User::create(&state.db, new_user, password_hash).await?;
    
    // Create JWT token
    let token = jwt::create_token(
        user.id.clone(),
        user.email.clone(),
        user.role.to_string(),
        &state.config.webui_secret_key,
    )?;
    
    Ok(Json(TokenResponse {
        token,
        token_type: "Bearer".to_string(),
    }))
}

/// Sign out endpoint
async fn signout(
    State(_state): State<AppState>,
) -> impl IntoResponse {
    // In a stateless JWT system, signout is handled client-side
    // The client should remove the token
    // For a more secure implementation, consider token blacklisting with Redis
    
    Json(json!({
        "message": "Signed out successfully"
    }))
}
