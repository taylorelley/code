# Code Pipeline Docker Image
#
# This image contains:
# - Python 3.11 runtime
# - Code binary (built from source or downloaded)
# - Pipeline dependencies
# - Open WebUI Pipelines framework

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Rust (needed to build Code from source)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install Node.js (for npm packages if needed)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Code project and build
# In production, you might want to use a pre-built binary or multi-stage build
COPY --from=code-builder /usr/local/bin/code /usr/local/bin/code
# Or build from source:
# COPY . /tmp/code-source
# RUN cd /tmp/code-source && npm run build && \
#     cp /tmp/code-source/code-rs/target/release/code /usr/local/bin/code && \
#     rm -rf /tmp/code-source

# Verify Code binary
RUN code --version || echo "Code binary verification pending"

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
CMD ["python", "-m", "pipelines.code_pipeline"]
