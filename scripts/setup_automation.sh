#!/bin/bash
# Setup script for awesome-llm-apps automation infrastructure

set -e  # Exit on error

echo "🤖 Setting up Automation Infrastructure for awesome-llm-apps"
echo "=========================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.12"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    print_status "Python $python_version meets requirement (>= $required_version)"
else
    print_error "Python $python_version does not meet requirement (>= $required_version)"
    exit 1
fi

# Install Python dependencies
echo -e "\nInstalling Python dependencies..."
pip install --upgrade pip

# Core dependencies for automation
pip install \
    safety \
    bandit \
    pip-audit \
    requests \
    packaging \
    matplotlib \
    pre-commit \
    ruff \
    mypy \
    pylint

print_status "Python dependencies installed"

# Install Node.js dependencies for documentation linting
echo -e "\nChecking Node.js..."
if command -v node &> /dev/null; then
    node_version=$(node --version)
    print_status "Node.js $node_version found"
    
    echo "Installing Node.js dependencies..."
    npm install -g markdownlint-cli cspell
    print_status "Node.js dependencies installed"
else
    print_warning "Node.js not found - skipping markdown linting tools"
    print_warning "Install Node.js for full documentation checking capabilities"
fi

# Setup pre-commit hooks
echo -e "\nSetting up pre-commit hooks..."
if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install
    print_status "Pre-commit hooks installed"
    
    # Run hooks on all files to check current state
    echo "Running pre-commit hooks on all files (this may take a while)..."
    pre-commit run --all-files || true
else
    print_error ".pre-commit-config.yaml not found"
fi

# Initialize health monitoring database
echo -e "\nInitializing health monitoring..."
python3 scripts/repository_health_monitor.py --record
print_status "Health monitoring initialized"

# Create necessary directories
echo -e "\nCreating directory structure..."
mkdir -p scripts/health_reports
mkdir -p scripts/logs
print_status "Directory structure created"

# Set script permissions
echo -e "\nSetting script permissions..."
chmod +x scripts/*.py
chmod +x scripts/*.sh
print_status "Script permissions set"

# Generate initial reports
echo -e "\nGenerating initial analysis reports..."

# Run version analysis
echo "Running version analysis..."
python3 scripts/version_hunter.py || print_warning "Version analysis completed with warnings"

# Run documentation analysis
echo "Running documentation analysis..."
python3 scripts/doc_consistency_analyzer.py || print_warning "Documentation analysis completed with warnings"

# Generate health report
echo "Generating health report..."
python3 scripts/repository_health_monitor.py --report --output scripts/health_reports

print_status "Initial analysis complete"

# Display summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Automation Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n📋 Next Steps:"
echo "1. Review the generated reports in scripts/health_reports/"
echo "2. Commit and push the automation infrastructure"
echo "3. GitHub Actions will activate automatically"
echo "4. Run 'pre-commit run --all-files' to test hooks"
echo "5. Schedule regular health monitoring (see .github/AUTOMATION_README.md)"

echo -e "\n🛠️ Useful Commands:"
echo "- Run full maintenance: python scripts/automated_maintenance.py"
echo "- Check health: python scripts/repository_health_monitor.py --report"
echo "- Test pre-commit: pre-commit run --all-files"
echo "- Update hooks: pre-commit autoupdate"

echo -e "\n📚 Documentation:"
echo "See .github/AUTOMATION_README.md for detailed documentation"

# Check for any critical issues
if [ -f "scripts/health_reports/health_report.json" ]; then
    health_score=$(python3 -c "import json; print(json.load(open('scripts/health_reports/health_report.json'))['current_health']['overall_score'])")
    
    echo -e "\n📊 Current Repository Health Score: ${health_score}/100"
    
    if (( $(echo "$health_score < 70" | bc -l) )); then
        print_warning "Repository health needs attention. Review the reports for details."
    fi
fi

echo -e "\n✨ Setup complete! Happy coding! 🚀"