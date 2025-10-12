use axum::{
    Router,
    routing::{get, post},
    http::StatusCode,
    response::{IntoResponse, Json},
    extract::State,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tower_http::cors::CorsLayer;
use tracing::{info, error};
use tracing_subscriber;

mod config;
mod models;
mod routers;
mod utils;
mod middleware;

use config::AppConfig;

#[derive(Clone)]
pub struct AppState {
    config: Arc<AppConfig>,
    // Database pool will be added here
    // db: sqlx::PgPool,
}

#[tokio::main]
async fn main() {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_target(false)
        .compact()
        .init();

    info!("Starting Open WebUI Rust Backend");

    // Load configuration
    let config = match AppConfig::from_env() {
        Ok(cfg) => Arc::new(cfg),
        Err(e) => {
            error!("Failed to load configuration: {}", e);
            std::process::exit(1);
        }
    };

    // Initialize application state
    let state = AppState {
        config: config.clone(),
    };

    // Build the application router
    let app = Router::new()
        // Health check endpoint
        .route("/health", get(health_check))
        .route("/api/health", get(health_check))
        
        // Version endpoint
        .route("/api/version", get(get_version))
        .route("/api/v1/version", get(get_version))
        
        // Config endpoint
        .route("/api/config", get(get_config))
        
        // Mount sub-routers (to be implemented)
        // .nest("/api/auth", routers::auth::router())
        // .nest("/api/users", routers::users::router())
        // .nest("/api/chats", routers::chats::router())
        // .nest("/api/models", routers::models::router())
        
        .with_state(state)
        .layer(CorsLayer::permissive()); // Configure CORS properly in production

    let addr = format!("{}:{}", config.host, config.port);
    let listener = tokio::net::TcpListener::bind(&addr)
        .await
        .expect("Failed to bind to address");

    info!("Server listening on http://{}", addr);

    axum::serve(listener, app)
        .await
        .expect("Server error");
}

// Health check endpoint
async fn health_check() -> impl IntoResponse {
    StatusCode::OK
}

#[derive(Serialize)]
struct VersionResponse {
    version: String,
    build: String,
}

// Version endpoint
async fn get_version() -> impl IntoResponse {
    Json(VersionResponse {
        version: env!("CARGO_PKG_VERSION").to_string(),
        build: option_env!("BUILD_HASH").unwrap_or("dev-build").to_string(),
    })
}

#[derive(Serialize)]
struct ConfigResponse {
    version: String,
    #[serde(rename = "WEBUI_NAME")]
    webui_name: String,
    #[serde(rename = "ENABLE_SIGNUP")]
    enable_signup: bool,
    #[serde(rename = "DEFAULT_LOCALE")]
    default_locale: String,
}

// Config endpoint
async fn get_config(State(state): State<AppState>) -> impl IntoResponse {
    Json(ConfigResponse {
        version: env!("CARGO_PKG_VERSION").to_string(),
        webui_name: state.config.webui_name.clone(),
        enable_signup: state.config.enable_signup,
        default_locale: state.config.default_locale.clone(),
    })
}
