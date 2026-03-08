#!/bin/bash
set -e

echo "🔧 NanoClow Setup"
echo "================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your API keys before continuing."
    exit 1
fi

# Create shared volume directories
echo "📁 Creating shared volume directories..."
mkdir -p shared/{ingress,egress,page_objects,html_dumps,logs}

# Build Docker containers
echo "🐳 Building Docker containers..."
cd docker
docker-compose build

echo "✅ Setup complete!"
echo ""
echo "To start NanoClow:"
echo "  cd docker && docker-compose up"
