#!/bin/bash

# Setup script for Taxi Waybill Bot
# This script helps with initial setup and verification

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "  Taxi Waybill Bot - Setup Script"
echo "================================================"
echo ""

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "ℹ $1"
}

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3.10+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found"
    exit 1
fi

# Check if virtual environment exists
echo ""
echo "Checking virtual environment..."
if [ -d "venv" ]; then
    print_success "Virtual environment exists"
else
    print_warning "Virtual environment not found"
    read -p "Create virtual environment? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_error "Virtual environment required. Exiting."
        exit 1
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
if pip install -r requirements.txt > /dev/null 2>&1; then
    print_success "Dependencies installed"
else
    print_error "Failed to install dependencies"
    exit 1
fi

# Check system dependencies for WeasyPrint
echo ""
echo "Checking system dependencies..."
MISSING_DEPS=()

check_package() {
    if ! dpkg -l | grep -q "^ii  $1 "; then
        MISSING_DEPS+=("$1")
    fi
}

check_package "libpango-1.0-0"
check_package "libcairo2"
check_package "libgdk-pixbuf2.0-0"

if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
    print_success "All system dependencies installed"
else
    print_warning "Missing system dependencies: ${MISSING_DEPS[*]}"
    print_info "Install with: sudo apt install -y ${MISSING_DEPS[*]}"
fi

# Check .env file
echo ""
echo "Checking configuration..."
if [ -f ".env" ]; then
    print_success ".env file exists"
    
    # Check required variables
    source .env
    
    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
        print_warning "TELEGRAM_BOT_TOKEN not set in .env"
    else
        print_success "TELEGRAM_BOT_TOKEN configured"
    fi
    
    if [ -z "$GOOGLE_SHEET_ID" ]; then
        print_warning "GOOGLE_SHEET_ID not set in .env"
    else
        print_success "GOOGLE_SHEET_ID configured"
    fi
else
    print_warning ".env file not found"
    read -p "Create .env from template? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
        print_success ".env file created from template"
        print_info "Please edit .env file and add your credentials"
    fi
fi

# Check service account file
echo ""
echo "Checking Google service account..."
if [ -f "service_account.json" ]; then
    print_success "service_account.json found"
    
    # Validate JSON
    if python3 -c "import json; json.load(open('service_account.json'))" 2>/dev/null; then
        print_success "service_account.json is valid JSON"
    else
        print_error "service_account.json is not valid JSON"
    fi
else
    print_warning "service_account.json not found"
    print_info "Please download your service account key from Google Cloud Console"
fi

# Check directories
echo ""
echo "Checking directories..."
mkdir -p generated_waybills
print_success "generated_waybills directory ready"

mkdir -p logs
print_success "logs directory ready"

# Test imports
echo ""
echo "Testing Python imports..."

test_import() {
    if python3 -c "import $1" 2>/dev/null; then
        print_success "$1 module available"
    else
        print_error "$1 module not available"
        return 1
    fi
}

test_import "telegram"
test_import "gspread"
test_import "jinja2"
test_import "weasyprint"
test_import "qrcode"
test_import "pytz"

# Test services (if configured)
echo ""
echo "Testing bot services..."

if [ -f ".env" ] && [ -f "service_account.json" ]; then
    echo "Testing configuration loading..."
    if python3 -c "import config; print('Config OK')" 2>/dev/null; then
        print_success "Configuration loads successfully"
    else
        print_error "Configuration loading failed"
    fi
    
    if [ ! -z "$GOOGLE_SHEET_ID" ]; then
        echo "Testing Google Sheets connection..."
        if timeout 10 python3 -c "
from bot.services.sheets_service import SheetsService
try:
    s = SheetsService()
    settings = s.get_settings()
    print('Sheets OK')
except Exception as e:
    print(f'Error: {e}')
    exit(1)
" 2>/dev/null; then
            print_success "Google Sheets connection successful"
        else
            print_warning "Google Sheets connection failed (check credentials and permissions)"
        fi
    fi
    
    echo "Testing PDF generation..."
    if python3 -c "
from bot.services.pdf_service import PDFService
try:
    p = PDFService()
    print('PDF OK')
except Exception as e:
    print(f'Error: {e}')
    exit(1)
" 2>/dev/null; then
        print_success "PDF service initialized successfully"
    else
        print_warning "PDF service initialization failed"
    fi
else
    print_warning "Skipping service tests (configuration not complete)"
fi

# Summary
echo ""
echo "================================================"
echo "  Setup Summary"
echo "================================================"
echo ""

READY=true

if [ ! -f ".env" ]; then
    print_error "Configuration incomplete: .env file missing"
    READY=false
fi

if [ ! -f "service_account.json" ]; then
    print_error "Configuration incomplete: service_account.json missing"
    READY=false
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    print_error "Configuration incomplete: TELEGRAM_BOT_TOKEN not set"
    READY=false
fi

if [ -z "$GOOGLE_SHEET_ID" ]; then
    print_error "Configuration incomplete: GOOGLE_SHEET_ID not set"
    READY=false
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    print_warning "System dependencies missing"
    READY=false
fi

echo ""
if [ "$READY" = true ]; then
    print_success "Bot is ready to run!"
    echo ""
    print_info "Start the bot with:"
    echo "  source venv/bin/activate"
    echo "  python main.py"
else
    print_warning "Bot is not ready. Please complete the setup steps above."
    echo ""
    print_info "Next steps:"
    echo "  1. Edit .env file with your credentials"
    echo "  2. Add service_account.json file"
    echo "  3. Install system dependencies if needed"
    echo "  4. Run this script again to verify"
fi

echo ""
echo "================================================"
echo "For detailed instructions, see README.md"
echo "================================================"
