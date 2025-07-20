#!/bin/bash

# Slack Joke Agent Release Script
# Builds and publishes the package to PyPI

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}🚀 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to prompt for confirmation
confirm() {
    read -p "$(echo -e ${YELLOW}$1${NC}) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  Slack Joke Agent Release                   ║"
echo "║                    PyPI Publishing Script                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check for required tools
print_step "Checking required tools..."

if ! command_exists python3; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

if ! command_exists git; then
    print_error "Git is required but not installed"
    exit 1
fi

print_success "All required tools are available"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_error "This script must be run from the root of a git repository"
    exit 1
fi

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    print_warning "You have uncommitted changes"
    if ! confirm "Continue anyway? (y/N)"; then
        print_error "Aborting due to uncommitted changes"
        exit 1
    fi
fi

# Get current version from pyproject.toml
current_version=$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])" 2>/dev/null || python3 -c "import tomli; print(tomli.load(open('pyproject.toml', 'rb'))['project']['version'])" 2>/dev/null || echo "unknown")

print_step "Current version: $current_version"

# Prompt for new version
echo -e "${YELLOW}Enter new version (current: $current_version): ${NC}"
read -r new_version

if [ -z "$new_version" ]; then
    print_error "Version cannot be empty"
    exit 1
fi

# Update version in pyproject.toml
print_step "Updating version to $new_version..."
if command_exists sed; then
    # macOS compatible sed
    sed -i '' "s/version = \"$current_version\"/version = \"$new_version\"/" pyproject.toml
else
    print_error "sed command not found"
    exit 1
fi

print_success "Version updated in pyproject.toml"

# Install/upgrade build tools
print_step "Installing/upgrading build tools..."
python3 -m pip install --upgrade pip build twine

# Clean previous builds
print_step "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

# Run tests if available
if [ -f "test_slack_agent.py" ] || [ -d "tests" ]; then
    print_step "Running tests..."
    python3 -m pytest || {
        print_error "Tests failed"
        exit 1
    }
    print_success "All tests passed"
else
    print_warning "No tests found - skipping test phase"
fi

# Build the package
print_step "Building package..."
python3 -m build

if [ $? -eq 0 ]; then
    print_success "Package built successfully"
else
    print_error "Package build failed"
    exit 1
fi

# Check the built package
print_step "Checking package..."
python3 -m twine check dist/*

if [ $? -eq 0 ]; then
    print_success "Package check passed"
else
    print_error "Package check failed"
    exit 1
fi

# Show package contents
print_step "Package contents:"
ls -la dist/

# Prompt for publication target
echo -e "${YELLOW}Choose publication target:${NC}"
echo "1) Test PyPI (recommended for first release)"
echo "2) Production PyPI"
echo "3) Skip upload (build only)"

read -p "Enter choice (1-3): " choice

case $choice in
    1)
        print_step "Uploading to Test PyPI..."
        python3 -m twine upload --repository testpypi dist/*
        if [ $? -eq 0 ]; then
            print_success "Successfully uploaded to Test PyPI!"
            echo -e "${GREEN}Install with: pip install -i https://test.pypi.org/simple/ slack-joke-agent==$new_version${NC}"
        else
            print_error "Upload to Test PyPI failed"
            exit 1
        fi
        ;;
    2)
        print_warning "This will upload to PRODUCTION PyPI and cannot be undone!"
        if confirm "Are you absolutely sure? (y/N)"; then
            print_step "Uploading to Production PyPI..."
            python3 -m twine upload dist/*
            if [ $? -eq 0 ]; then
                print_success "Successfully uploaded to Production PyPI!"
                echo -e "${GREEN}Install with: pip install slack-joke-agent==$new_version${NC}"
            else
                print_error "Upload to Production PyPI failed"
                exit 1
            fi
        else
            print_warning "Upload cancelled"
        fi
        ;;
    3)
        print_warning "Skipping upload - package built only"
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

# Commit version change
if [ -n "$(git status --porcelain pyproject.toml)" ]; then
    print_step "Committing version update..."
    git add pyproject.toml
    git commit -m "Release version $new_version

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    
    print_success "Version update committed"
    
    # Create git tag
    if confirm "Create git tag v$new_version? (y/N)"; then
        git tag -a "v$new_version" -m "Release version $new_version"
        print_success "Git tag v$new_version created"
        
        if confirm "Push to remote repository? (y/N)"; then
            git push origin main
            git push origin "v$new_version"
            print_success "Changes pushed to remote repository"
        fi
    fi
fi

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                     Release Complete! 🎉                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}Package: slack-joke-agent v$new_version${NC}"
echo -e "${GREEN}Build artifacts available in: ./dist/${NC}"

if [ "$choice" = "1" ]; then
    echo -e "${BLUE}Test the package:${NC}"
    echo "pip install -i https://test.pypi.org/simple/ slack-joke-agent==$new_version"
elif [ "$choice" = "2" ]; then
    echo -e "${BLUE}Install the package:${NC}"
    echo "pip install slack-joke-agent==$new_version"
fi

echo -e "${BLUE}Next steps:${NC}"
echo "1. Test the installed package"
echo "2. Update documentation if needed"
echo "3. Announce the release"

print_success "Release script completed successfully!"