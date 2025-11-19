# Code Pipeline Docker Image
#
# This image contains:
# - Python 3.11 runtime
# - Code binary (built from source in multi-stage build)
# - Pipeline dependencies
# - Open WebUI Pipelines framework

# Stage 1: Build Code binary from the parent repository
FROM rust:1.75-slim AS code-builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    ca-certificates \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy the entire Code repository (parent directory)
COPY .. .

# Build Code binary from source
RUN cd code-rs && \
    cargo build --release --bin code && \
    echo "Code binary built successfully" && \
    ls -l target/release/code

# Copy the built binary to a standard location
RUN cp code-rs/target/release/code /usr/local/bin/code && \
    chmod +x /usr/local/bin/code && \
    /usr/local/bin/code --version

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

# Verify Code binary exists and is executable
RUN ls -l /usr/local/bin/code && \
    chmod +x /usr/local/bin/code && \
    /usr/local/bin/code --version

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
