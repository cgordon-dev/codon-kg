#!/bin/bash
# Setup script for mcp-mem0 server

set -e

echo "🧠 Setting up mcp-mem0 server..."

# Change to mcp-mem0 directory
cd mcp-mem0

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    pip install uv
fi

# Install dependencies
echo "Installing dependencies..."
uv pip install -e .

# Copy environment file
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "Copying .env.example to .env..."
        cp .env.example .env
        echo "Please edit .env file with your configurations"
    else
        echo "Creating .env file..."
        cat > .env << 'EOF'
TRANSPORT=stdio
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-openai-api-key
LLM_CHOICE=gpt-4o-mini
EMBEDDING_MODEL_CHOICE=text-embedding-3-small
DATABASE_URL=postgresql://user:pass@localhost:5432/mem0db
EOF
        echo "Created .env file - please edit with your configurations"
    fi
else
    echo ".env file already exists"
fi

echo "✅ mcp-mem0 setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys and database URL"
echo "2. Set up PostgreSQL database"
echo "3. Run the server with: python src/main.py"