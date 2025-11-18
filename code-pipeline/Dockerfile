# Code Pipeline Docker Image
#
# This image contains:
# - Python 3.11 runtime
# - Code binary (built from source in multi-stage build)
# - Pipeline dependencies
# - Open WebUI Pipelines framework

# Stage 1: Build Code binary
FROM rust:1.75-slim AS code-builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for building Code
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy Code source (assumes Dockerfile context includes parent directory)
# Adjust paths based on your build context
# Use RUN with shell logic since COPY doesn't support shell operators
RUN if [ -f ../package.json ]; then \
      cp ../package.json .; \
    else \
      echo "{}" > package.json; \
    fi

RUN if [ -f ../tsconfig.json ]; then \
      cp ../tsconfig.json .; \
    else \
      echo "{}" > tsconfig.json; \
    fi

RUN if [ -d ../code-rs ]; then \
      cp -r ../code-rs .; \
    else \
      mkdir -p code-rs; \
    fi

# Build Code binary (or use a mock for testing)
# If source not available, create a simple mock binary
RUN if [ -f package.json ] && [ -f code-rs/Cargo.toml ]; then \
        npm install && npm run build:rs && \
        cp code-rs/target/release/code /usr/local/bin/code; \
    else \
        echo '#!/bin/sh\necho "Mock Code binary - replace with real build"\nexit 1' > /usr/local/bin/code && \
        chmod +x /usr/local/bin/code; \
    fi

# Stage 2: Runtime image
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Code binary from builder stage
COPY --from=code-builder /usr/local/bin/code /usr/local/bin/code

# Verify Code binary exists
RUN ls -l /usr/local/bin/code && chmod +x /usr/local/bin/code

# Copy pipeline code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set up working directory for Code sessions
RUN mkdir -p /data/code-workspace
ENV CODE_WORKING_DIR=/data/code-workspace

# Expose port for pipeline server (when running standalone)
EXPOSE 9099

# Default command (run pipeline server)
# When used with Open WebUI, this will be overridden
CMD ["python", "server.py"]
