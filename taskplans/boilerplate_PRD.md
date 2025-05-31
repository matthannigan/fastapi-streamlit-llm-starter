# FastAPI-Streamlit-LLM Starter Template

A production-ready starter template for building AI-powered applications using FastAPI, Streamlit, and PydanticAI.

## 🌟 Features

- **🚀 Modern Stack**: FastAPI + Streamlit + PydanticAI
- **🤖 AI Integration**: Easy integration with multiple AI models
- **📊 Rich UI**: Interactive Streamlit interface with real-time updates
- **🐳 Docker Ready**: Complete containerization for easy deployment
- **🔒 Production Ready**: Security headers, rate limiting, health checks
- **📈 Scalable**: Designed for horizontal scaling
- **🧪 Extensible**: Easy to add new features and AI operations

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │───▶│     FastAPI      │───▶│   PydanticAI    │
│   Frontend      │    │     Backend      │    │   + LLM APIs    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                      │
         │              ┌─────────────────┐             │
         └─────────────▶│  Shared Models  │◀────────────┘
                        │   (Pydantic)    │
                        └─────────────────┘
```

### Project Structure

```
fastapi-streamlit-llm-starter/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py         # FastAPI app and routes
│   │   ├── config.py       # Configuration management
│   │   └── services/       # Business logic services
│   └── Dockerfile
├── frontend/                # Streamlit application
│   ├── app/
│   │   ├── app.py          # Main Streamlit app
│   │   ├── config.py       # Frontend configuration
│   │   └── utils/          # Utility functions
│   └── Dockerfile
├── shared/                  # Shared Pydantic models
│   └── models.py
├── nginx/                   # Nginx configuration
├── docker-compose.yml       # Docker orchestration
└── Makefile                # Development shortcuts
```

## New Functionality

