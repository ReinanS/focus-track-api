# 🐛 Debug com Docker - FocusTrack API

## 🚀 Configuração Rápida

### 1. Iniciar Debug
```bash
./debug.sh
```

### 2. Conectar VS Code
1. Abra o VS Code na pasta do projeto
2. Pressione `Ctrl+Shift+D` (ou `Cmd+Shift+D` no Mac)
3. Selecione **"Debug FastAPI (Docker)"**
4. Clique em **"Start Debugging"** (F5)

## 🔧 Configurações

### Docker Compose (compose-dev.yaml)
- **Porta API**: 8000
- **Porta Debug**: 5678
- **Hot Reload**: ✅ Ativado
- **Debugpy**: ✅ Configurado

### VS Code (.vscode/launch.json)
- **Path Mapping**: Local → Docker
- **Just My Code**: ❌ Desabilitado
- **Stop on Entry**: ❌ Desabilitado

## 🎯 Como Usar

### Breakpoints
1. Clique na linha onde quer parar (bolinha vermelha)
2. Execute uma requisição para a API
3. O debugger vai parar no breakpoint

### Debug Console
- **F5**: Continuar
- **F10**: Step Over
- **F11**: Step Into
- **Shift+F11**: Step Out
- **Ctrl+Shift+F5**: Restart

### Variáveis e Watch
- **Variables**: Ver variáveis locais
- **Watch**: Adicionar expressões para monitorar
- **Call Stack**: Ver pilha de chamadas

## 🐳 Comandos Docker

### Iniciar
```bash
docker-compose -f compose-dev.yaml up -d
```

### Ver Logs
```bash
docker-compose -f compose-dev.yaml logs -f focus_track_app
```

### Parar
```bash
docker-compose -f compose-dev.yaml down
```

### Reconstruir
```bash
docker-compose -f compose-dev.yaml build --no-cache
```

## 🔍 Troubleshooting

### Problema: "Cannot connect to debugpy"
**Solução:**
1. Verifique se a porta 5678 está livre
2. Reinicie o container: `docker-compose -f compose-dev.yaml restart focus_track_app`
3. Aguarde 10 segundos e tente conectar novamente

### Problema: "Path mapping not working"
**Solução:**
1. Verifique se o arquivo está no volume correto
2. Confirme que `localRoot` e `remoteRoot` estão corretos
3. Reinicie o VS Code

### Problema: "Breakpoint not hit"
**Solução:**
1. Verifique se o código está sendo executado
2. Confirme que o breakpoint está na linha correta
3. Verifique se há erros de sintaxe

## 📁 Estrutura de Arquivos

```
focus-track-api/
├── .vscode/
│   ├── launch.json      # Configurações de debug
│   └── settings.json    # Configurações do VS Code
├── compose-dev.yaml     # Docker Compose para debug
├── Dockerfile.dev       # Dockerfile com debugpy
├── entrypoint-dev.sh    # Script de inicialização
├── debug.sh            # Script de setup
└── DEBUG.md            # Este arquivo
```

## 🎯 Exemplo de Debug

### 1. Adicionar Breakpoint
```python
# focus_track_api/routers/study_session.py
@router.websocket("/monitor")
async def monitor_session(websocket: WebSocket):
    await websocket.accept()  # ← Breakpoint aqui
    print("WebSocket connection established")
```

### 2. Iniciar Debug
1. Execute `./debug.sh`
2. Conecte o VS Code
3. Faça uma requisição WebSocket
4. O debugger vai parar no breakpoint

### 3. Inspecionar Variáveis
- `websocket`: Objeto WebSocket
- `token`: Token de autenticação
- `user`: Usuário autenticado

## 🚀 Próximos Passos

1. **Teste o debug** com uma requisição simples
2. **Adicione breakpoints** nos pontos críticos
3. **Use o debug console** para testar expressões
4. **Monitore variáveis** durante a execução

---

**🎉 Agora você pode debugar o FocusTrack API com Docker no VS Code!** 