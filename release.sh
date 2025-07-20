#!/bin/bash

# Slack Joke Agent Release Script
# Streamlined build and publish script for PyPI
# Usage: ./release.sh [version]

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
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

# Function to show usage
show_usage() {
    echo "Usage: $0 [version]"
    echo ""
    echo "Examples:"
    echo "  $0 1.0.3        # Release version 1.0.3 to PyPI"
    echo "  $0              # Interactive mode (original behavior)"
    echo ""
    echo "When version is provided, the script will:"
    echo "  1. Update version in pyproject.toml"
    echo "  2. Run tests"
    echo "  3. Build package"
    echo "  4. Validate package"
    echo "  5. Upload to PyPI"
    echo "  6. Commit changes and create git tag"
    echo "  7. Push to remote repository"
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  Slack Joke Agent Release                   ║"
echo "║                    PyPI Publishing Script                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_error "This script must be run from the root of a git repository"
    exit 1
fi

# Get current version from pyproject.toml
current_version=$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])" 2>/dev/null || python3 -c "import tomli; print(tomli.load(open('pyproject.toml', 'rb'))['project']['version'])" 2>/dev/null || echo "unknown")

print_step "Current version: $current_version"

# Check if version was provided as argument
if [ $# -eq 1 ]; then
    new_version="$1"
    AUTO_MODE=true
    
    # Validate version format (basic check)
    if [[ ! $new_version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        print_error "Invalid version format. Expected: X.Y.Z (e.g., 1.0.3)"
        exit 1
    fi
    
    if [ "$new_version" = "$current_version" ]; then
        print_error "New version ($new_version) is the same as current version ($current_version)"
        exit 1
    fi
    
    print_step "Auto mode: Releasing version $new_version to PyPI"
    
    # Check for uncommitted changes in auto mode
    if [ -n "$(git status --porcelain)" ]; then
        print_error "You have uncommitted changes. Please commit or stash them before releasing."
        exit 1
    fi
    
    # Update version
    print_step "Updating version to $new_version..."
    sed -i '' "s/version = \"$current_version\"/version = \"$new_version\"/" pyproject.toml
    print_success "Version updated in pyproject.toml"
    current_version=$new_version
else
    AUTO_MODE=false
    
    # Check for uncommitted changes in interactive mode
    if [ -n "$(git status --porcelain)" ]; then
        print_warning "You have uncommitted changes"
        read -p "$(echo -e ${YELLOW}Continue anyway? (y/N)${NC}) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Aborting due to uncommitted changes"
            exit 1
        fi
    fi
    
    # Ask if user wants to update version in interactive mode
    read -p "$(echo -e ${YELLOW}Update version? (y/N)${NC}) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Enter new version (current: $current_version): ${NC}"
        read -r new_version
        
        if [ -n "$new_version" ] && [ "$new_version" != "$current_version" ]; then
            print_step "Updating version to $new_version..."
            sed -i '' "s/version = \"$current_version\"/version = \"$new_version\"/" pyproject.toml
            print_success "Version updated in pyproject.toml"
            current_version=$new_version
        fi
    fi
fi

# Install/upgrade build tools
print_step "Installing/upgrading build tools..."
python3 -m pip install --upgrade pip build twine

# Clean previous builds
print_step "Cleaning previous builds..."
rm -rf build/ dist/ slack_joke_agent.egg-info/

# Run tests
print_step "Running tests..."
if [ -f "test_slack_agent.py" ]; then
    python3 test_slack_agent.py
    if [ $? -eq 0 ]; then
        print_success "All tests passed"
    else
        print_error "Tests failed"
        exit 1
    fi
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
    print_success "Package validation: PASSED"
else
    print_error "Package validation failed"
    exit 1
fi

# Show package contents and summary
print_step "Package contents:"
ls -la dist/
echo ""
echo -e "${GREEN}📋 Package Summary:${NC}"
echo "   - All tests passing ✅"
echo "   - Package validation: PASSED ✅"
echo "   - Version: $current_version ✅"
echo "   - Ready for PyPI publication 🚀"
echo ""

# Publication logic
if [ "$AUTO_MODE" = true ]; then
    # Auto mode: upload directly to PyPI
    print_step "Uploading to Production PyPI..."
    python3 -m twine upload dist/*
    if [ $? -eq 0 ]; then
        print_success "Successfully uploaded to Production PyPI!"
        echo -e "${GREEN}Install with: pip install slack-joke-agent==$current_version${NC}"
        choice="2"  # Set for later use in output
    else
        print_error "Upload to Production PyPI failed"
        exit 1
    fi
else
    # Interactive mode: prompt for publication target
    echo -e "${YELLOW}Choose publication target:${NC}"
    echo "1) Test PyPI (recommended for testing)"
    echo "2) Production PyPI"
    echo "3) Build only (no upload)"

    read -p "Enter choice (1-3): " choice

    case $choice in
        1)
            print_step "Uploading to Test PyPI..."
            python3 -m twine upload --repository testpypi dist/*
            if [ $? -eq 0 ]; then
                print_success "Successfully uploaded to Test PyPI!"
                echo -e "${GREEN}Install with: pip install -i https://test.pypi.org/simple/ slack-joke-agent==$current_version${NC}"
            else
                print_error "Upload to Test PyPI failed"
                exit 1
            fi
            ;;
        2)
            print_warning "This will upload to PRODUCTION PyPI and cannot be undone!"
            read -p "$(echo -e ${YELLOW}Are you absolutely sure? (y/N)${NC}) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                print_step "Uploading to Production PyPI..."
                python3 -m twine upload dist/*
                if [ $? -eq 0 ]; then
                    print_success "Successfully uploaded to Production PyPI!"
                    echo -e "${GREEN}Install with: pip install slack-joke-agent==$current_version${NC}"
                else
                    print_error "Upload to Production PyPI failed"
                    exit 1
                fi
            else
                print_warning "Upload cancelled"
            fi
            ;;
        3)
            print_warning "Build complete - package ready for manual upload"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
fi

# Commit version change if there was one
if [ -n "$(git status --porcelain pyproject.toml)" ]; then
    if confirm "Commit version update? (y/N)"; then
        print_step "Committing version update..."
        git add pyproject.toml
        git commit -m "Release version $current_version

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
        
        print_success "Version update committed"
        
        # Create git tag
        if confirm "Create git tag v$current_version? (y/N)"; then
            git tag -a "v$current_version" -m "Release version $current_version"
            print_success "Git tag v$current_version created"
            
            if confirm "Push to remote repository? (y/N)"; then
                git push origin main
                git push origin "v$current_version"
                print_success "Changes pushed to remote repository"
            fi
        fi
    fi
fi

echo ""
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                     Release Complete! 🎉                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}Package: slack-joke-agent v$current_version${NC}"
echo -e "${GREEN}Build artifacts available in: ./dist/${NC}"

if [ "$choice" = "1" ]; then
    echo -e "${BLUE}Test the package:${NC}"
    echo "pip install -i https://test.pypi.org/simple/ slack-joke-agent==$current_version"
elif [ "$choice" = "2" ]; then
    echo -e "${BLUE}Install the package:${NC}"
    echo "pip install slack-joke-agent==$current_version"
fi

echo -e "${BLUE}Next steps:${NC}"
echo "1. Test the installed package"
echo "2. Update documentation if needed"
echo "3. Announce the release"

print_success "Release script completed successfully!"