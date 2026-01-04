#!/bin/bash
# ============================================================================
# PyDeck Installation Script
# ============================================================================
# Quick installer for the PyDeck performance refactor
#
# Usage:
#   chmod +x install_pydeck.sh
#   ./install_pydeck.sh
# ============================================================================

echo "🚀 Installing PyDeck Performance Upgrade..."
echo ""

# Check if we're in the Webtool directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found"
    echo "Please run this script from the Webtool directory"
    exit 1
fi

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $python_version"

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
python3 -m pip install --upgrade pip

# Install requirements
echo ""
echo "📥 Installing dependencies..."
python3 -m pip install -r requirements.txt

# Verify PyDeck installation
echo ""
echo "✅ Verifying PyDeck installation..."
pydeck_version=$(python3 -c "import pydeck; print(pydeck.__version__)" 2>&1)

if [ $? -eq 0 ]; then
    echo "   ✅ PyDeck version: $pydeck_version"
else
    echo "   ❌ PyDeck installation failed"
    exit 1
fi

# Verify Streamlit version
echo ""
echo "✅ Verifying Streamlit installation..."
streamlit_version=$(streamlit --version 2>&1 | grep "Streamlit," | awk '{print $2}')

if [ ! -z "$streamlit_version" ]; then
    echo "   ✅ Streamlit version: $streamlit_version"
else
    echo "   ⚠️  Could not determine Streamlit version"
fi

# Success message
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  ✅ PyDeck Installation Complete!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "🚀 Next steps:"
echo "   1. Start dashboard: streamlit run app.py"
echo "   2. Load your data (State → City → Load Data)"
echo "   3. Test performance with Apply filters"
echo "   4. Click markers to see detail panel"
echo ""
echo "📖 Documentation:"
echo "   • Quick Start: QUICK_START_PYDECK.md"
echo "   • Full Guide:  PYDECK_MIGRATION_GUIDE.md"
echo "   • Summary:     REFACTOR_SUMMARY.md"
echo ""
echo "⚡ Expected Performance:"
echo "   • 196 listings:   < 0.5 seconds"
echo "   • 5,000 listings: < 1 second"
echo "   • 15,000 listings: < 2 seconds"
echo ""
echo "════════════════════════════════════════════════════════════"

