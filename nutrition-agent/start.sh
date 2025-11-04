#!/usr/bin/env bash
set -euo pipefail

# Root del monorepo
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
APP_DIR="$ROOT_DIR/nutrition-agent"

# Assicura che l'ambiente virtuale esista
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "❌ Ambiente virtuale non trovato in $VENV_DIR"
  echo "➡️  Crealo e reinstalla le dipendenze prima di procedere."
  exit 1
fi

# Installa dipendenze critiche se mancano
echo "ℹ️  Verifico dipendenze critiche da requirements.txt..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip setuptools wheel 2>/dev/null || true
"$VENV_DIR/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

# Imposta PYTHONPATH per i pacchetti locali (namespace 'datapizza')
export PYTHONPATH="$ROOT_DIR/datapizza-ai-core:$ROOT_DIR/datapizza-ai-clients/datapizza-ai-clients-google:$ROOT_DIR/datapizza-ai-clients/datapizza-ai-clients-openai-like:${PYTHONPATH:-}"

# Test import di base per fallire presto con errore chiaro
"$VENV_DIR/bin/python" - <<'PY' || { echo "❌ Import test fallito"; exit 1; }
import sys
print("🧪 PYTHONPATH head:", sys.path[:5])
try:
    import datapizza.core
    import datapizza.clients.google
    import datapizza.clients.openai_like
    print("✅ Namespace 'datapizza' OK")
except Exception as e:
    import traceback; traceback.print_exc()
    raise
PY

# Variabili utili per OpenRouter (facoltative, safe defaults)
export OPENROUTER_HTTP_REFERER="${OPENROUTER_HTTP_REFERER:-http://localhost:8501}"
export OPENROUTER_X_TITLE="${OPENROUTER_X_TITLE:-Nutrition Agent}"

# Avvio Streamlit
cd "$APP_DIR"
echo "🚀 Avvio Streamlit (http://localhost:8501)"
exec "$VENV_DIR/bin/streamlit" run nutrition_dashboard.py
