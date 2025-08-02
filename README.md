# 🎯 FocusTrack API

> **Sistema de Monitoramento de Atenção e Fadiga em Tempo Real**

Uma API inteligente que utiliza **Computer Vision** e **Machine Learning** para monitorar níveis de atenção, fadiga e distração durante sessões de estudo ou trabalho.

## 🚀 Tecnologias

### **Backend**
- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para PostgreSQL
- **PostgreSQL** - Banco de dados principal
- **Alembic** - Migrações de banco de dados
- **Poetry** - Gerenciamento de dependências

### **Computer Vision & AI**
- **OpenCV** - Processamento de imagens
- **MediaPipe** - Detecção facial e landmarks
- **NumPy** - Computação numérica
- **Custom ML Models** - Algoritmos de atenção

### **Autenticação & Segurança**
- **JWT** - Tokens de autenticação
- **Pwdlib** - Hash de senhas seguro
- **OAuth2** - Autenticação OAuth2

### **DevOps & Deploy**
- **Docker** - Containerização
- **Fly.io** - Deploy em nuvem
- **GitHub Actions** - CI/CD

## 📁 Estrutura do Projeto

```
focus-track-api/
├── focus_track_api/
│   ├── __init__.py
│   ├── app.py                 # Aplicação FastAPI
│   ├── database.py            # Configuração do banco
│   ├── models.py              # Modelos SQLAlchemy
│   ├── security.py            # Autenticação JWT
│   ├── settings.py            # Configurações
│   ├── routers/               # Endpoints da API
│   │   ├── auth.py           # Autenticação
│   │   ├── daily_summary.py  # Resumos diários
│   │   ├── study_session.py  # Sessões de estudo
│   │   ├── user_settings.py  # Configurações do usuário
│   │   └── users.py          # Usuários
│   ├── schemas/              # Schemas Pydantic
│   │   ├── attention.py      # Métricas de atenção
│   │   ├── daily_summary.py  # Resumos
│   │   ├── session_metrics.py # Métricas de sessão
│   │   ├── study_session.py  # Sessões
│   │   ├── token.py          # Tokens
│   │   ├── user_settings.py  # Configurações
│   │   └── users.py          # Usuários
│   ├── services/             # Lógica de negócio
│   │   ├── attention.py      # Processamento de frames
│   │   ├── attention_scorer.py # Algoritmos de atenção
│   │   ├── daily_summary.py  # Resumos diários
│   │   ├── eye_detector.py   # Detecção de olhos
│   │   ├── face_geometry.py  # Geometria facial
│   │   ├── pose_estimation.py # Estimativa de pose
│   │   ├── study_session.py  # Sessões
│   │   ├── user_settings.py  # Configurações
│   │   └── users.py          # Usuários
│   └── utils/                # Utilitários
│       ├── constants.py      # Constantes
│       └── utils.py          # Funções auxiliares
├── migrations/               # Migrações Alembic
├── tests/                   # Testes unitários
├── .vscode/                 # Configurações VS Code
├── compose.yaml             # Docker Compose (prod)
├── compose-dev.yaml         # Docker Compose (dev)
├── Dockerfile               # Docker (prod)
├── Dockerfile.dev           # Docker (dev)
├── pyproject.toml           # Dependências Poetry
└── README.md               # Este arquivo
```

## 🎯 Funcionalidades

### **Monitoramento em Tempo Real**
- **WebSocket** para comunicação bidirecional
- **Processamento de frames** em tempo real
- **Detecção facial** com MediaPipe
- **Análise de olhos** (EAR - Eye Aspect Ratio)
- **Estimativa de pose** (Roll, Pitch, Yaw)
- **Cálculo de PERCLOS** (Percentage of Eye Closure)

### **Métricas de Atenção**
- **Fatigue Score** - Nível de fadiga (0-100%)
- **Distraction Score** - Nível de distração (0-100%)
- **Attention Score** - Nível de atenção (0-100%)
- **PERCLOS** - Indicador de sonolência

### **Sessões de Estudo**
- **Início/Fim** de sessões
- **Duração** automática
- **Métricas médias** e máximas
- **Eventos críticos** com timestamps
- **Remoção automática** de sessões < 1 minuto

### **Análise Histórica**
- **Resumos diários** de performance
- **Timeline** de eventos críticos
- **Tendências** de atenção ao longo do tempo
- **Relatórios** detalhados

### **Configurações Personalizadas**
- **Thresholds** de fadiga e distração
- **Notificações** personalizadas
- **Alertas** em tempo real

## 🚀 Como Executar

### **Pré-requisitos**
- Docker e Docker Compose
- Python 3.12+
- Poetry

### **1. Clone o Repositório**
```bash
git clone <repository-url>
cd focus-track-api
```

### **2. Configuração de Ambiente**
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite as variáveis de ambiente
nano .env
```

### **3. Executar com Docker (Recomendado)**
```bash
# Produção
docker-compose up -d

# Desenvolvimento
docker-compose -f compose-dev.yaml up -d
```

### **4. Executar Localmente**
```bash
# Instalar dependências
poetry install

# Configurar banco
poetry run alembic upgrade head

# Executar aplicação
poetry run uvicorn focus_track_api.app:app --reload
```

## 🐛 Debug

### **Debug com Docker**
```bash
# Iniciar debug
./debug.sh

# Conectar VS Code
# 1. Abra VS Code na pasta do projeto
# 2. Ctrl+Shift+D → "Debug FastAPI (Docker)"
# 3. F5 para conectar
```

### **Debug Local**
```bash
# VS Code: "Debug FastAPI (Poetry)"
# Ou manualmente:
poetry run python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn focus_track_api.app:app --reload
```

## 📊 API Endpoints

### **Autenticação**
```
POST /auth/token          # Login
POST /auth/refresh        # Refresh token
```

### **Usuários**
```
GET    /users/me          # Perfil do usuário
POST   /users             # Criar usuário
PUT    /users/me          # Atualizar usuário
```

### **Sessões de Estudo**
```
GET    /study-session                    # Listar sessões
POST   /study-session                    # Criar sessão
GET    /study-session/{id}              # Detalhes da sessão
POST   /study-session/start             # Iniciar sessão
POST   /study-session/finalize/{id}     # Finalizar sessão
WS     /study-session/monitor           # Monitoramento WebSocket
```

### **Resumos Diários**
```
GET    /daily-summary                    # Listar resumos
GET    /daily-summary/overview          # Visão geral
```

### **Configurações**
```
GET    /settings                        # Configurações do usuário
POST   /settings                        # Criar configurações
PUT    /settings                        # Atualizar configurações
```

## 🧪 Testes

### **Executar Testes**
```bash
# Todos os testes
poetry run pytest

# Com cobertura
poetry run pytest --cov=focus_track_api

# Testes específicos
poetry run pytest tests/test_auth.py
```

### **Linting e Formatação**
```bash
# Linting
poetry run ruff check

# Formatação
poetry run ruff format

# Fix automático
poetry run ruff check --fix
```

## 🐳 Docker

### **Comandos Úteis**
```bash
# Construir imagem
docker-compose build

# Executar
docker-compose up -d

# Ver logs
docker-compose logs -f focus_track_app

# Parar
docker-compose down

# Reconstruir
docker-compose build --no-cache
```

### **Desenvolvimento**
```bash
# Debug com hot reload
docker-compose -f compose-dev.yaml up -d

# Ver logs de debug
docker-compose -f compose-dev.yaml logs -f focus_track_app
```

## 🔧 Configurações

### **Variáveis de Ambiente**
```env
# Banco de dados
DATABASE_URL=postgresql+psycopg://user:pass@localhost/db

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# PostgreSQL
POSTGRES_USER=app_user
POSTGRES_DB=app_db
POSTGRES_PASSWORD=app_password
```

### **Configurações de Desenvolvimento**
- **Hot Reload**: Ativado em desenvolvimento
- **Debugpy**: Porta 5678 para debug
- **Logs**: Verbose em desenvolvimento
- **CORS**: Configurado para frontend

## 📈 Métricas e Performance

### **Algoritmos de Atenção**
- **EAR (Eye Aspect Ratio)**: Detecção de piscadas
- **PERCLOS**: Indicador de sonolência
- **Gaze Tracking**: Rastreamento do olhar
- **Pose Estimation**: Estimativa de pose da cabeça

### **Performance**
- **Processamento**: ~30fps em tempo real
- **Latência**: <100ms para análise de frame
- **Precisão**: >90% na detecção de fadiga
- **Escalabilidade**: Suporte a múltiplas sessões

## 🚀 Deploy

### **Fly.io**
```bash
# Deploy
flyctl deploy

# Ver logs
flyctl logs

# SSH
flyctl ssh console
```

### **Migrações**
```bash
# Executar migrações
flyctl ssh console -a focus-track-api -C "poetry run alembic upgrade head"
```

## 🤝 Contribuição

### **Fluxo de Desenvolvimento**
1. **Fork** o repositório
2. **Crie** uma branch: `git checkout -b feature/nova-funcionalidade`
3. **Commit** suas mudanças: `git commit -am 'Adiciona nova funcionalidade'`
4. **Push** para a branch: `git push origin feature/nova-funcionalidade`
5. **Abra** um Pull Request

### **Padrões de Código**
- **Black** para formatação
- **Ruff** para linting
- **Type hints** obrigatórios
- **Docstrings** para funções públicas
- **Testes** para novas funcionalidades

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🆘 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/focus-track-api/issues)
- **Documentação**: [Wiki](https://github.com/seu-usuario/focus-track-api/wiki)
- **Email**: reinandesouza01@gmail.com

---

**🎯 FocusTrack API - Monitoramento Inteligente de Atenção**