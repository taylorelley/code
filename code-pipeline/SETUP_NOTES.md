# Setup Notes

## ✅ Containers Running Successfully!

Both Open WebUI and code-pipeline containers are now running and healthy!

## ⚠️ Next Step: Install Real Code Binary

The containers are using a **mock Code binary** which exits immediately. You need to install the real Code binary to enable full functionality.

### Current Status

- ✅ Docker containers: Running
- ✅ Open WebUI: Accessible at http://localhost:3000
- ✅ Pipeline server: Running with health checks
- ⚠️  Code binary: Using mock (needs real binary)

### Error You're Seeing

```
RuntimeError: Request failed: Connection lost
```

This happens because the mock Code binary exits immediately instead of running as a server.

### How to Fix

You have three options:

#### Option 1: Download Pre-built Code Binary (Fastest)

If available, download a pre-built Code binary:

```bash
# Download Code binary (replace with actual download link)
wget https://github.com/just-every/code/releases/latest/download/code-linux-x64 -O code

# Make it executable
chmod +x code

# Copy into the running container
docker cp code code-pipeline:/usr/local/bin/code

# Restart the container
docker restart code-pipeline

# Check logs
docker logs code-pipeline -f
```

#### Option 2: Build Code from Source

```bash
# Clone the Code repository
cd /root/code
git clone https://github.com/just-every/code.git code-source
cd code-source

# Build Code (requires Node.js and Rust)
npm install
npm run build

# Copy built binary to code-pipeline directory
cp dist/code ../code-pipeline/code-binary

# Update Dockerfile to use it
cd ../code-pipeline

# Rebuild with real binary
docker compose down
docker compose build --no-cache code-pipeline
docker compose up -d
```

#### Option 3: Mount Code Binary from Host

```bash
# If you have Code installed on your host
which code

# Add volume mount to docker-compose.yml:
# volumes:
#   - /path/to/code:/usr/local/bin/code:ro

docker compose down
docker compose up -d
```

### Verify It's Working

Once you have the real Code binary:

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
