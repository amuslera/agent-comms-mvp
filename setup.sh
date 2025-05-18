#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Setting up Bluelabel Agent OS development environment...${NC}"

# Check if Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.8 or later is required. Please install it first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print('{}.{}'.format(sys.version_info.major, sys.version_info.minor))")
if [[ "$PYTHON_VERSION" < "3.8" ]]; then
    echo "❌ Python 3.8 or later is required. Found Python $PYTHON_VERSION"
    exit 1
fi

# Create and activate virtual environment
echo -e "${GREEN}🔧 Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Upgrade pip
echo -e "${GREEN}⬆️  Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${GREEN}📦 Installing dependencies...${NC}"
pip install -e .
pip install -r requirements-dev.txt

# Set up pre-commit hooks
echo -e "${GREEN}🔧 Setting up pre-commit hooks...${NC}
pre-commit install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${GREEN}📝 Creating .env file...${NC}"
    cp .env.example .env
    echo "Created .env file from .env.example"
else
    echo -e "${GREEN}ℹ️  .env file already exists, skipping...${NC}"
fi

echo -e "\n${GREEN}✨ Setup complete!${NC}"
echo -e "To activate the virtual environment, run:\n  source venv/bin/activate  # On Windows: .\\venv\\Scripts\\activate"
echo -e "\nTo run the system:\n  python -m tools.run_plan --help"
