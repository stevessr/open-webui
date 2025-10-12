use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct AppConfig {
    // Server configuration
    pub host: String,
    pub port: u16,
    
    // WebUI configuration
    pub webui_name: String,
    pub webui_url: String,
    pub webui_secret_key: String,
    
    // Authentication
    pub enable_signup: bool,
    pub enable_oauth: bool,
    pub enable_admin_export: bool,
    pub enable_community_sharing: bool,
    
    // Localization
    pub default_locale: String,
    
    // Database
    pub database_url: String,
    
    // Redis
    pub redis_url: Option<String>,
    
    // Ollama configuration
    pub ollama_base_url: String,
    pub ollama_base_urls: Vec<String>,
    
    // OpenAI configuration
    pub openai_api_key: Option<String>,
    pub openai_api_base_url: String,
    
    // Model configurations
    pub bypass_model_access_control: bool,
    pub bypass_admin_access_control: bool,
    
    // Task configuration
    pub task_model: Option<String>,
    pub task_model_external: Option<String>,
    pub title_generation_prompt_template: String,
    
    // RAG configuration
    pub enable_rag_web_search: bool,
    pub rag_embedding_engine: String,
    pub rag_embedding_model: String,
    
    // Image generation
    pub enable_image_generation: bool,
    pub image_generation_engine: String,
    
    // Audio
    pub audio_tts_engine: String,
    pub audio_tts_model: String,
    pub audio_stt_engine: String,
    pub audio_stt_model: String,
    
    // File upload
    pub upload_dir: String,
    pub file_max_size: usize,
    
    // Cache
    pub enable_base_models_cache: bool,
    
    // Logging
    pub log_level: String,
}

impl AppConfig {
    pub fn from_env() -> Result<Self, envy::Error> {
        dotenv::dotenv().ok();
        
        Ok(AppConfig {
            // Server defaults
            host: env::var("HOST").unwrap_or_else(|_| "0.0.0.0".to_string()),
            port: env::var("PORT")
                .unwrap_or_else(|_| "8080".to_string())
                .parse()
                .unwrap_or(8080),
            
            // WebUI defaults
            webui_name: env::var("WEBUI_NAME").unwrap_or_else(|_| "Open WebUI".to_string()),
            webui_url: env::var("WEBUI_URL").unwrap_or_else(|_| "http://localhost:3000".to_string()),
            webui_secret_key: env::var("WEBUI_SECRET_KEY")
                .unwrap_or_else(|_| Self::generate_secret_key()),
            
            // Authentication defaults
            enable_signup: env::var("ENABLE_SIGNUP")
                .unwrap_or_else(|_| "true".to_string())
                .parse()
                .unwrap_or(true),
            enable_oauth: env::var("ENABLE_OAUTH")
                .unwrap_or_else(|_| "false".to_string())
                .parse()
                .unwrap_or(false),
            enable_admin_export: env::var("ENABLE_ADMIN_EXPORT")
                .unwrap_or_else(|_| "true".to_string())
                .parse()
                .unwrap_or(true),
            enable_community_sharing: env::var("ENABLE_COMMUNITY_SHARING")
                .unwrap_or_else(|_| "true".to_string())
                .parse()
                .unwrap_or(true),
            
            // Localization
            default_locale: env::var("DEFAULT_LOCALE").unwrap_or_else(|_| "en-US".to_string()),
            
            // Database
            database_url: env::var("DATABASE_URL")
                .unwrap_or_else(|_| "sqlite:./data/webui.db".to_string()),
            
            // Redis
            redis_url: env::var("REDIS_URL").ok(),
            
            // Ollama defaults
            ollama_base_url: env::var("OLLAMA_BASE_URL")
                .unwrap_or_else(|_| "http://localhost:11434".to_string()),
            ollama_base_urls: env::var("OLLAMA_BASE_URLS")
                .unwrap_or_else(|_| "".to_string())
                .split(',')
                .filter(|s| !s.is_empty())
                .map(|s| s.to_string())
                .collect(),
            
            // OpenAI defaults
            openai_api_key: env::var("OPENAI_API_KEY").ok(),
            openai_api_base_url: env::var("OPENAI_API_BASE_URL")
                .unwrap_or_else(|_| "https://api.openai.com/v1".to_string()),
            
            // Model access control
            bypass_model_access_control: env::var("BYPASS_MODEL_ACCESS_CONTROL")
                .unwrap_or_else(|_| "false".to_string())
                .parse()
                .unwrap_or(false),
            bypass_admin_access_control: env::var("BYPASS_ADMIN_ACCESS_CONTROL")
                .unwrap_or_else(|_| "false".to_string())
                .parse()
                .unwrap_or(false),
            
            // Task configuration
            task_model: env::var("TASK_MODEL").ok(),
            task_model_external: env::var("TASK_MODEL_EXTERNAL").ok(),
            title_generation_prompt_template: env::var("TITLE_GENERATION_PROMPT_TEMPLATE")
                .unwrap_or_else(|_| "Generate a concise title for this conversation".to_string()),
            
            // RAG defaults
            enable_rag_web_search: env::var("ENABLE_RAG_WEB_SEARCH")
                .unwrap_or_else(|_| "false".to_string())
                .parse()
                .unwrap_or(false),
            rag_embedding_engine: env::var("RAG_EMBEDDING_ENGINE")
                .unwrap_or_else(|_| "".to_string()),
            rag_embedding_model: env::var("RAG_EMBEDDING_MODEL")
                .unwrap_or_else(|_| "".to_string()),
            
            // Image generation defaults
            enable_image_generation: env::var("ENABLE_IMAGE_GENERATION")
                .unwrap_or_else(|_| "false".to_string())
                .parse()
                .unwrap_or(false),
            image_generation_engine: env::var("IMAGE_GENERATION_ENGINE")
                .unwrap_or_else(|_| "".to_string()),
            
            // Audio defaults
            audio_tts_engine: env::var("AUDIO_TTS_ENGINE")
                .unwrap_or_else(|_| "".to_string()),
            audio_tts_model: env::var("AUDIO_TTS_MODEL")
                .unwrap_or_else(|_| "".to_string()),
            audio_stt_engine: env::var("AUDIO_STT_ENGINE")
                .unwrap_or_else(|_| "".to_string()),
            audio_stt_model: env::var("AUDIO_STT_MODEL")
                .unwrap_or_else(|_| "".to_string()),
            
            // File upload
            upload_dir: env::var("UPLOAD_DIR")
                .unwrap_or_else(|_| "./data/uploads".to_string()),
            file_max_size: env::var("FILE_MAX_SIZE")
                .unwrap_or_else(|_| "10485760".to_string()) // 10MB default
                .parse()
                .unwrap_or(10485760),
            
            // Cache
            enable_base_models_cache: env::var("ENABLE_BASE_MODELS_CACHE")
                .unwrap_or_else(|_| "false".to_string())
                .parse()
                .unwrap_or(false),
            
            // Logging
            log_level: env::var("LOG_LEVEL").unwrap_or_else(|_| "info".to_string()),
        })
    }
    
    fn generate_secret_key() -> String {
        use uuid::Uuid;
        Uuid::new_v4().to_string()
    }
}
