#!/usr/bin/env bash
# smoke.sh — Chimera Cerebro smoke test
# Usage: bash .claude/skills/run-chimera-cerebro/smoke.sh
# Requires: API server already running on port 5555

set -euo pipefail

BASE="http://localhost:5555"

echo "=== Chimera API Smoke Test ==="

# 1. Health check
echo -n "[1] GET /  ... "
resp=$(curl -sf "$BASE/")
echo "$resp" | grep -q '"status":"online"' && echo "OK" || { echo "FAIL: $resp"; exit 1; }

# 2. /chat endpoint
echo -n "[2] POST /chat  ... "
resp=$(curl -sf -X POST "$BASE/chat" \
  -H "Content-Type: application/json" \
  -d '{"tarea":"hola"}')
echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'respuesta' in d and len(d['respuesta']) > 0, f'bad response: {d}'; print('OK')"

# 3. /siri endpoint (returns plain text, not JSON object)
echo -n "[3] POST /siri  ... "
resp=$(curl -sf -X POST "$BASE/siri" \
  -H "Content-Type: application/json" \
  -d '{"tarea":"hola"}')
[ -n "$resp" ] && echo "OK" || { echo "FAIL: empty response"; exit 1; }

echo ""
echo "=== All smoke tests passed ==="
