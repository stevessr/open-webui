// Database module - Connection pool and operations
use sqlx::{PgPool, SqlitePool, Pool, Sqlite, Postgres};
use sqlx::migrate::MigrateDatabase;
use std::str::FromStr;

use crate::utils::errors::{AppError, Result};
use crate::config::AppConfig;

/// Database pool enum to support both PostgreSQL and SQLite
#[derive(Clone)]
pub enum Database {
    Postgres(PgPool),
    Sqlite(SqlitePool),
}

impl Database {
    /// Create a new database connection pool based on the database URL
    pub async fn new(config: &AppConfig) -> Result<Self> {
        let database_url = &config.database_url;
        
        if database_url.starts_with("postgresql://") || database_url.starts_with("postgres://") {
            let pool = PgPool::connect(database_url)
                .await
                .map_err(|e| AppError::DatabaseError(format!("Failed to connect to PostgreSQL: {}", e)))?;
            
            Ok(Database::Postgres(pool))
        } else if database_url.starts_with("sqlite:") {
            // Ensure database file exists
            let db_path = database_url.strip_prefix("sqlite:").unwrap_or(database_url);
            if !Sqlite::database_exists(database_url).await.unwrap_or(false) {
                tracing::info!("Creating database at {}", db_path);
                Sqlite::create_database(database_url)
                    .await
                    .map_err(|e| AppError::DatabaseError(format!("Failed to create SQLite database: {}", e)))?;
            }
            
            let pool = SqlitePool::connect(database_url)
                .await
                .map_err(|e| AppError::DatabaseError(format!("Failed to connect to SQLite: {}", e)))?;
            
            Ok(Database::Sqlite(pool))
        } else {
            Err(AppError::DatabaseError(
                "Unsupported database URL. Use postgresql:// or sqlite:".to_string()
            ))
        }
    }
    
    /// Run database migrations
    pub async fn migrate(&self) -> Result<()> {
        match self {
            Database::Postgres(pool) => {
                sqlx::migrate!("./migrations")
                    .run(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(format!("Migration failed: {}", e)))?;
            }
            Database::Sqlite(pool) => {
                sqlx::migrate!("./migrations")
                    .run(pool)
                    .await
                    .map_err(|e| AppError::DatabaseError(format!("Migration failed: {}", e)))?;
            }
        }
        Ok(())
    }
    
    /// Get PostgreSQL pool (panics if not PostgreSQL)
    pub fn pg_pool(&self) -> &PgPool {
        match self {
            Database::Postgres(pool) => pool,
            _ => panic!("Database is not PostgreSQL"),
        }
    }
    
    /// Get SQLite pool (panics if not SQLite)
    pub fn sqlite_pool(&self) -> &SqlitePool {
        match self {
            Database::Sqlite(pool) => pool,
            _ => panic!("Database is not SQLite"),
        }
    }
    
    /// Check if database is PostgreSQL
    pub fn is_postgres(&self) -> bool {
        matches!(self, Database::Postgres(_))
    }
    
    /// Check if database is SQLite
    pub fn is_sqlite(&self) -> bool {
        matches!(self, Database::Sqlite(_))
    }
}
