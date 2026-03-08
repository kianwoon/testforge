#!/bin/bash
set -e

echo "🔧 NanoClow Setup"
echo "================="

# Run interactive Python setup
python3 scripts/setup_cli.py

# Build Docker containers
echo "🐳 Building Docker containers..."
cd docker
docker-compose build

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start NanoClow:"
echo "  cd docker && docker-compose up"
