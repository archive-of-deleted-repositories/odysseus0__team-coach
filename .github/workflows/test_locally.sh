#!/bin/bash

# Local testing script for GitHub Actions workflow
# This simulates the workflow execution locally

echo "=== Testing GitHub Actions Workflow Locally ==="
echo ""

# Check Python version
echo "1. Checking Python version..."
python_version=$(python3 --version 2>&1)
if [[ $python_version == *"3.12"* ]] || [[ $python_version == *"3.13"* ]]; then
    echo "✓ Python version OK: $python_version"
else
    echo "✗ Python 3.12+ required. Found: $python_version"
    exit 1
fi

# Check if uv is installed
echo ""
echo "2. Checking uv installation..."
if command -v uv &> /dev/null; then
    echo "✓ uv is installed"
else
    echo "✗ uv not found. Install with: pip install uv"
    exit 1
fi

# Check sample data
echo ""
echo "3. Checking sample data..."
if [ -d "demo_agentic_newsletter/sample_data" ]; then
    file_count=$(ls demo_agentic_newsletter/sample_data/*.txt 2>/dev/null | wc -l)
    echo "✓ Sample data found: $file_count files"
else
    echo "✗ Sample data directory not found"
    exit 1
fi

# Test CI script
echo ""
echo "4. Testing CI newsletter generation..."
if [ -f "demo_agentic_newsletter/generate_newsletter_ci.py" ]; then
    # Set a dummy API key for testing (not used in demo mode)
    export CLAUDE_API_KEY="test-key-not-used-in-demo"
    
    # Run the script
    python3 demo_agentic_newsletter/generate_newsletter_ci.py
    
    # Check output
    if [ -f "demo_agentic_newsletter/newsletter_output.md" ]; then
        echo "✓ Newsletter generated successfully"
        echo ""
        echo "Output preview:"
        head -n 20 demo_agentic_newsletter/newsletter_output.md
    else
        echo "✗ Newsletter generation failed"
        exit 1
    fi
else
    echo "✗ CI script not found"
    exit 1
fi

echo ""
echo "=== All tests passed! ==="
echo ""
echo "Next steps:"
echo "1. Configure secrets in GitHub repository settings"
echo "2. Push changes to trigger workflow"
echo "3. Or manually trigger from Actions tab"