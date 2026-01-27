#!/bin/bash

# BudgeX Backend Service Setup Script

echo "🚀 Setting up BudgeX Backend Service..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "⚠️  Please update .env with your configuration values!"
    else
        echo "⚠️  .env.example not found. Please create .env manually."
    fi
else
    echo "✅ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your database and email configuration"
echo "2. Create PostgreSQL database: CREATE DATABASE budgex_mobile_db;"
echo "3. Run migrations: alembic upgrade head"
echo "4. Start the server: uvicorn app.main:app --reload"
echo ""
echo "To activate the virtual environment later, run:"
echo "  source venv/bin/activate"

