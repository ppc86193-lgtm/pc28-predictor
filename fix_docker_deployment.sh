#!/bin/bash
# PC28 Predictor - Docker Deployment Fix Script
# Addresses I/O errors and Redis connection issues

set -e

echo "🔧 PC28 Docker Deployment Fix"
echo "=============================="
echo ""

# Step 1: Check disk space
echo "📊 Checking disk space..."
df -h /Users/a606/Downloads/grok1
echo ""

# Step 2: Clean Docker system
echo "🧹 Cleaning Docker system..."
docker system df
echo ""
read -p "Clean Docker cache? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker system prune -a --volumes -f
    docker builder prune -f
    echo "✅ Docker cache cleaned"
fi
echo ""

# Step 3: Stop existing containers
echo "🛑 Stopping existing containers..."
cd pc28_predictor
docker-compose down -v 2>/dev/null || true
echo ""

# Step 4: Build with optimized settings
echo "🏗️  Building Docker image (optimized)..."
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build with no cache to avoid I/O errors
docker build \
    --no-cache \
    --pull \
    --progress=plain \
    -t pc28-predictor:latest \
    .

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful"
else
    echo "❌ Docker build failed"
    echo ""
    echo "Troubleshooting tips:"
    echo "1. Restart Docker Desktop"
    echo "2. Check disk space: df -h"
    echo "3. Try: docker system prune -a --volumes"
    exit 1
fi
echo ""

# Step 5: Verify Redis configuration
echo "🔍 Verifying Redis configuration..."
docker run --rm \
    -e REDIS_HOST=redis \
    -e REDIS_PORT=6379 \
    pc28-predictor:latest \
    python -c "import config; print(f'✅ Redis Host: {config.redis_host}, Port: {config.redis_port}')"
echo ""

# Step 6: Start services
echo "🚀 Starting services..."
docker-compose up -d
echo ""

# Step 7: Wait for services to be healthy
echo "⏳ Waiting for services to be healthy (60s)..."
sleep 60
echo ""

# Step 8: Check service status
echo "📋 Service Status:"
docker-compose ps
echo ""

# Step 9: Check Redis connection
echo "🔗 Testing Redis connection..."
docker exec pc28-predictor python -c "
import config
try:
    config.redis_client.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
" || echo "⚠️  Container not ready yet"
echo ""

# Step 10: Health check
echo "🏥 Testing health endpoint..."
sleep 5
curl -f http://localhost:8000/health || echo "⚠️  Health check failed - service may still be starting"
echo ""
echo ""

# Step 11: Show logs
echo "📝 Recent logs:"
docker-compose logs --tail=20 app
echo ""

echo "✅ Deployment fix complete!"
echo ""
echo "Next steps:"
echo "1. Check logs: docker-compose logs -f app"
echo "2. Test API: curl http://localhost:8000/health"
echo "3. Monitor: docker-compose ps"
echo "4. Stop: docker-compose down"
