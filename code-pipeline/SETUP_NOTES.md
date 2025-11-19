# Setup Notes

## ✅ Automatic Build from Source

The Dockerfile now **automatically builds the Code binary from source** during the Docker build process!

### What Happens During Build

1. **Clones** the Code repository from GitHub (https://github.com/anthropics/claude-code)
2. **Installs** all dependencies (Node.js, Rust, npm packages)
3. **Builds** the Code binary from source
4. **Packages** it into the Docker image

### Current Status

- ✅ Docker containers: Running
- ✅ Open WebUI: Accessible at http://localhost:3000
- ✅ Pipeline server: Running with health checks
- ✅ Code binary: Built automatically from source

### How to Build and Run

Simply rebuild the Docker image - it will automatically build Code from source:

```bash
cd /root/code/code-pipeline

# Pull the latest changes
git pull origin claude/auto-configure-webui-pipeline-011CUqWLgGCEV5PEeT37ghZb

# Stop current containers
docker compose down

# Remove old image to force rebuild
docker rmi code-pipeline-code-pipeline

# Build with automatic source compilation (this will take a few minutes)
docker compose build --no-cache code-pipeline

# Start the services
docker compose up -d
```

The build process will:
- Clone the Code repository
- Install all dependencies
- Build the binary from source
- Package everything into the container

**Note:** The first build will take 5-10 minutes as it compiles from source.

### Verify It's Working

After building:

```bash
# Check Code version in container
docker exec code-pipeline /usr/local/bin/code --version

# Should show version instead of "Mock Code binary"

# Check logs for successful startup
docker logs code-pipeline | grep "Code app-server started"

# Try a chat in Open WebUI
# Go to http://localhost:3000 and send a message
```

## Current Container Status

```bash
# View running containers
docker compose ps

# Should show:
# NAME            IMAGE                                  STATUS
# code-pipeline   code-pipeline-code-pipeline           Up (healthy)
# open-webui      ghcr.io/open-webui/open-webui:main   Up (healthy)
```

## Accessing Open WebUI

1. Go to: http://localhost:3000 (or http://your-server-ip:3000)
2. Sign up for an account
3. Select "code-pipeline" from the model dropdown
4. Start chatting!

**Note:** Chat will fail until you install the real Code binary (see above).

## Logs

```bash
# View all logs
docker compose logs -f

# View only code-pipeline logs
docker compose logs -f code-pipeline

# View only open-webui logs
docker compose logs -f open-webui
```

## Health Checks

```bash
# Check pipeline health
curl http://localhost:9099/health

# Check available models
curl http://localhost:9099/v1/models

# Check from inside open-webui container
docker exec open-webui curl http://code-pipeline:9099/health
```

## Troubleshooting

### "Connection lost" errors

This is expected with the mock binary. Install the real Code binary (see above).

### Containers keep restarting

Check logs:
```bash
docker compose logs code-pipeline
```

### Can't access Open WebUI

1. Check firewall: `sudo ufw status`
2. Check if port 3000 is open: `netstat -tlnp | grep 3000`
3. Access via server IP instead of localhost

### Container build fails

```bash
# Clean everything and rebuild
docker compose down -v
docker system prune -af
docker compose build --no-cache
docker compose up -d
```
