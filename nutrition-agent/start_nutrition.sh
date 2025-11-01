#!/bin/bash
# 🥗 Nutrition Agent - Launch Script

echo "🥗 Starting Nutrition Agent Dashboard..."
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f "../.env" ]; then
    echo "❌ Error: .env file not found in parent directory"
    echo "   Create ../.env with: GOOGLE_API_KEY=your_key"
    exit 1
fi

# Load .env
export $(grep -v '^#' ../.env | xargs)

# Check API key
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ Error: GOOGLE_API_KEY not found in .env"
    exit 1
fi

echo "✅ API Key configured"
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not installed"
    echo "   Install with: pip install streamlit"
    exit 1
fi

echo "🚀 Launching dashboard on http://127.0.0.1:8550"
echo ""
echo "📍 Navigation:"
echo "   - 🏠 Home: Overview and quick actions"
echo "   - 👤 Profilo: Configure your profile"
echo "   - 📅 Piano Giornaliero: Daily meal plan"
echo "   - 📆 Piano Settimanale: Weekly meal plan"
echo "   - 🔍 Cerca Ricette: Search recipes"
echo "   - 📊 Analisi: Nutrition analytics"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

# Launch streamlit
streamlit run nutrition_dashboard.py --server.port 8550
