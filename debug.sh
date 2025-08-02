#!/bin/bash

echo "🚀 Iniciando debug do FocusTrack API..."

# Para containers existentes
echo "🛑 Parando containers existentes..."
docker-compose -f compose-dev.yaml down

# Reconstrói a imagem com debug
echo "🔨 Reconstruindo imagem com debug..."
docker-compose -f compose-dev.yaml build

# Inicia os containers
echo "▶️  Iniciando containers..."
docker-compose -f compose-dev.yaml up -d

echo "⏳ Aguardando aplicação inicializar..."
sleep 10

echo "✅ Debug configurado!"
echo ""
echo "📋 Próximos passos:"
echo "1. Abra o VS Code"
echo "2. Vá para a aba 'Run and Debug' (Ctrl+Shift+D)"
echo "3. Selecione 'Debug FastAPI (Docker)'"
echo "4. Clique em 'Start Debugging' (F5)"
echo ""
echo "🔗 URLs:"
echo "- API: http://localhost:8000"
echo "- Debug: localhost:5678"
echo ""
echo "🐳 Para ver logs: docker-compose -f compose-dev.yaml logs -f focus_track_app" 