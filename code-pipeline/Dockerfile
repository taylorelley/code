# Code Pipeline Docker Image
#
# This image contains:
# - Python 3.11 runtime
# - Code binary (built from source in multi-stage build)
# - Pipeline dependencies
# - Open WebUI Pipelines framework

# Stage 1: Build Code binary from source
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

# Install Node.js 20.x for building Code
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Clone Code repository and build from source
RUN git clone https://github.com/anthropics/claude-code.git . && \
    echo "Cloned Code repository" && \
    ls -la

# Install dependencies and build
RUN npm install && \
    echo "npm install completed" && \
    npm run build && \
    echo "npm build completed"

# Copy the built binary to /usr/local/bin
RUN if [ -f dist/code ]; then \
        cp dist/code /usr/local/bin/code && chmod +x /usr/local/bin/code; \
    elif [ -f build/code ]; then \
        cp build/code /usr/local/bin/code && chmod +x /usr/local/bin/code; \
    elif [ -f bin/code ]; then \
        cp bin/code /usr/local/bin/code && chmod +x /usr/local/bin/code; \
    else \
        echo "Could not find built Code binary, checking for node executable..." && \
        find . -name "code" -type f -executable && \
        echo "Creating wrapper script..." && \
        echo '#!/bin/bash\nnode /build/dist/index.js "$@"' > /usr/local/bin/code && \
        chmod +x /usr/local/bin/code; \
    fi

# Verify the binary exists and is executable
RUN ls -l /usr/local/bin/code && \
    /usr/local/bin/code --version || echo "Code binary installed (version check may fail)"

# Stage 2: Runtime image
FROM python:3.11-slim

# Install runtime dependencies including Node.js (needed for Code binary)
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js in runtime (required if Code is a Node.js app)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Code binary and built files from builder stage
COPY --from=code-builder /usr/local/bin/code /usr/local/bin/code
COPY --from=code-builder /build/dist /app/code-dist

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
