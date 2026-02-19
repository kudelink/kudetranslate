# KudeTranslate

A self-hosted neural machine translation web application powered by Ollama and Large Language Models (LLM). The application provides real-time streaming translation with a clean, responsive interface similar to DeepL.

## Architecture

KudeTranslate consists of three Docker services orchestrated via Docker Compose:

### Services

- **Ollama** - Local LLM inference engine that runs the translation model
- **Backend** (Flask + Gunicorn) - REST API handling translation requests, model management, and streaming responses
- **Frontend** (Astro + Node.js + Express) - Responsive web interface with integrated API proxy

### Technology Stack

| Component | Technology |
|-----------|------------|
| Container Orchestration | Docker Compose |
| Backend Framework | Flask (Python) |
| WSGI Server | Gunicorn |
| Frontend Framework | Astro (Static) |
| Frontend Server | Node.js + Express |
| API Proxy | Express HTTP Proxy |
| Styling | Tailwind CSS |
| LLM Engine | Ollama |
| Translation Model | TranslateGemma (configurable) |

### Network Architecture

```
User Browser -> Frontend (Node.js:80) -> Backend (Internal)
                                    -> Ollama (Internal)
```

Only the frontend port is exposed externally. Backend and Ollama communicate internally.

## Features

- Real-time streaming translation with token-by-token display
- Support for multiple languages (including Galician, Catalan, Basque)
- Automatic model download if not present
- Responsive design for desktop and mobile
- Model selection and switching
- Translation statistics (tokens, speed, duration)
- Language swap functionality
- Clipboard copy support

## Prerequisites

- Docker Engine 20.10+
- Docker Compose v2+
- At least 8GB RAM (recommended for larger models)

## Configuration

All configuration is managed via `config.yaml`:

```yaml
ollama:
  host: "http://ollama:11434"
  default_model: "translategemma:4b"
  auto_download: true

llm:
  temperature: 0.3
  max_tokens: 2048
  top_p: 0.9

translation:
  default_source_lang: "auto"
  default_target_lang: "es"

languages:
  - code: "es"
    name: "Spanish"
  # ... additional languages
```

### Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ollama.host` | Ollama API endpoint | `http://ollama:11434` |
| `ollama.default_model` | Default translation model | `translategemma:4b` |
| `ollama.auto_download` | Auto-download missing models | `true` |
| `llm.temperature` | Generation temperature (0-1) | `0.3` |
| `llm.max_tokens` | Maximum tokens to generate | `2048` |
| `llm.top_p` | Nucleus sampling parameter | `0.9` |

## Installation

### Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd translate-docker
   ```

2. Start all services:
   ```bash
   docker compose up -d
   ```

3. Access the application:
   - Frontend: http://localhost:4321 (only exposed port)

Note: Backend and Ollama are only accessible internally within the Docker network.

### First Run

On first run, the backend will automatically:
1. Check if the default model exists
2. Download TranslateGemma if not present
3. Start all three services
4. Be ready for translation

The model download may take several minutes depending on your internet connection.

Check backend logs to monitor model download:
```bash
docker compose logs backend
```

## Usage

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config` | GET | Get current configuration |
| `/api/models` | GET | List available Ollama models |
| `/api/models/check/<model>` | GET | Check if model exists |
| `/api/models/download` | POST | Download a model |
| `/api/translate` | POST | Translate text (non-streaming) |
| `/api/translate/stream` | POST | Translate text (streaming SSE) |

### API Examples

API requests should go through the frontend proxy:

#### Get Configuration
```bash
curl http://localhost:4321/api/config
```

#### List Models
```bash
curl http://localhost:4321/api/models
```

#### Stream Translation
```bash
curl -X POST http://localhost:4321/api/translate/stream \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world",
    "source_lang": "en",
    "target_lang": "es",
    "model": "translategemma:4b"
  }'
```

### Environment Variables

The following environment variables can be used to override container settings:

#### Backend
- `OLLAMA_HOST` - Ollama service URL (default: `http://ollama:11434`)
- `CONFIG_PATH` - Path to configuration file (default: `/app/config.yaml`)

#### Ollama
- `OLLAMA_HOST` - Bind address (default: `0.0.0.0`)
- `OLLAMA_NUM_THREADS` - CPU threads to use (default: `8`)
- `OLLAMA_FLASH_ATTENTION` - Enable flash attention (default: `1`)

#### Frontend
- `BACKEND_URL` - Backend API URL (default: `http://backend:5000`)

## Development

### Building Images

```bash
# Build all services
docker compose build

# Build specific service
docker compose build backend
docker compose build frontend
```

### Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f ollama
```

### Stopping Services

```bash
docker compose down
```

To remove volumes (including downloaded models):
```bash
docker compose down -v
```

## Troubleshooting

### Model Not Found

If you see a model not found error, ensure the backend has finished downloading the model. Check logs:
```bash
docker compose logs backend
```

### Connection Refused

Ensure all services are running:
```bash
docker compose ps
```

### Memory Issues

If you encounter OOM errors, try:
1. Using a smaller model (e.g., `translategemma:4b` instead of `8b`)
2. Reducing `OLLAMA_NUM_THREADS` in docker-compose.yml
3. Increasing Docker memory allocation

### Timeout Errors

Translation requests may take time for large texts. The Gunicorn timeout is set to 300 seconds. Adjust in the backend Dockerfile if needed.

## Performance Optimization

### Ollama Settings

The docker-compose.yml includes performance optimizations:
- `OLLAMA_NUM_THREADS=8` - Uses 8 CPU threads
- `OLLAMA_FLASH_ATTENTION=1` - Enables optimized attention mechanism

### Gunicorn Workers

The backend uses 2 Gunicorn workers with a 300-second timeout. Adjust in the backend Dockerfile:
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "300", "app.main:app"]
```

## License

Apache 2.0
