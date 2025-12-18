#!/usr/bin/env bash
set -e

echo "Starting deployment..."

# 1. Create virtual environment at repo root
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# 2. Activate venv
source .venv/bin/activate

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install dependencies (use uv if available)
if command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.cargo/bin:$PATH"
  echo "Using uv for dependency installation..."
  uv pip install -r requirements.txt
else
  echo "Using pip for dependency installation..."
  pip install -r requirements.txt
fi

# 5. Start server in background
echo "Starting server on port 8080..."
nohup uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8080 \
  > server.log 2>&1 &

echo "Deployment completed successfully."
