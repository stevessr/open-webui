# Multi-stage build for Open WebUI Rust Backend with Frontend
# Stage 1: Build frontend
FROM --platform=$BUILDPLATFORM node:22-alpine3.20 AS frontend-build
ARG BUILD_HASH=dev-build

WORKDIR /app

# Install git for build info
RUN apk add --no-cache git

# Copy package files from repo root
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci --force

# Copy frontend source
COPY . .

# Build frontend
ENV APP_BUILD_HASH=${BUILD_HASH}
RUN npm run build

# Stage 2: Build Rust backend
FROM rust:1.75-slim as backend-builder

# Install dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy manifests
COPY backend-rust/Cargo.toml ./

# Create a dummy main.rs to build dependencies
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# Copy source code
COPY backend-rust/src ./src

# Build for release
RUN cargo build --release

# Stage 3: Runtime
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy binary from builder
COPY --from=backend-builder /app/target/release/open-webui-backend /app/

# Copy frontend build from frontend-build stage
COPY --from=frontend-build /app/build /app/static

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8080

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8080
ENV DATABASE_URL=sqlite:/app/data/webui.db
ENV STATIC_DIR=/app/static

# Run the binary
CMD ["/app/open-webui-backend"]
