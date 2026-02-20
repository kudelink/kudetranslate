# KudeTranslate

A self-hosted neural machine translation web application powered by Ollama and Large Language Models (LLM). The application provides real-time streaming translation with a clean, responsive interface similar to DeepL.

## Architecture

KudeTranslate consists of three Docker services orchestrated via Docker Compose:

### Services

- **Ollama** - Local LLM inference engine that runs the translation models
- **Backend** (Flask + Gunicorn/Gevent) - REST API handling translation requests, model management, queue system, and streaming responses via SSE
- **Frontend** (Astro + Node.js + Express) - Responsive web interface with integrated API proxy

### Technology Stack

| Component | Technology |
|-----------|------------|
| Container Orchestration | Docker Compose |
| Backend Framework | Flask (Python) |
| WSGI Server | Gunicorn + Gevent |
| Frontend Framework | Astro (Static) |
| Frontend Server | Node.js + Express |
| API Proxy | http-proxy-middleware |
| Styling | CSS Custom Properties |
| LLM Engine | Ollama |
| Translation Models | TranslateGemma, Ministral (configurable) |

### Network Architecture

```
User Browser -> Frontend (Node.js:80) -> Backend (Flask:5000) -> Ollama (11434)
```

Only the frontend port (4321) is exposed externally. Backend and Ollama communicate internally within the Docker network.

## Features

- Real-time streaming translation with token-by-token display (SSE)
- Multi-model support with model-specific prompt types
- Translation queue system with position feedback for concurrent users
- Dark/Light mode with warm color palette and localStorage persistence
- Automatic download of all configured models on startup
- Support for multiple languages (including Galician, Catalan, Basque)
- Language swap prevention (source and target cannot be the same)
- Responsive design for desktop and mobile
- Model selection and switching
- Translation statistics (tokens, speed, duration)
- Language swap functionality
- Clipboard copy support

## Prerequisites

- Docker Engine 20.10+
- Docker Compose v2+
- At least 8GB RAM (recommended for running multiple models)

## Configuration

All configuration is managed via `config.yaml` (mounted as read-only volume in the backend container):

```yaml
ollama:
  host: "http://ollama:11434"
  default_model: "translategemma:4b"
  auto_download: true

llm:
  temperature: 0.1
  max_tokens: 8192
  top_p: 0.9
  num_thread: 18

models:
  - name: "translategemma:4b"
    prompt_type: "translategemma"
  - name: "ministral-3:3b"
    prompt_type: "generic"

translation:
  default_source_lang: "en"
  default_target_lang: "es"

languages:
  - code: "auto"
    name: "Detect Language"
  - code: "es"
    name: "Spanish"
  # ... additional languages
```

### Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ollama.host` | Ollama API endpoint | `http://ollama:11434` |
| `ollama.default_model` | Default translation model | `translategemma:4b` |
| `ollama.auto_download` | Auto-download missing models on startup | `true` |
| `llm.temperature` | Generation temperature (0-1) | `0.1` |
| `llm.max_tokens` | Maximum tokens to generate | `8192` |
| `llm.top_p` | Nucleus sampling parameter | `0.9` |
| `llm.num_thread` | CPU threads for Ollama inference (0 = auto) | `0` |
| `models[].name` | Model name as registered in Ollama | - |
| `models[].prompt_type` | Prompt template to use (`translategemma` or `generic`) | `generic` |

### Multi-Model Support

Each model can have a different prompt type:

- **`translategemma`** - Specialized prompt format for TranslateGemma models with language codes
- **`generic`** - Simple translation prompt compatible with general-purpose LLMs (Ministral, Llama, etc.)

All models listed in the `models` section are automatically downloaded on startup if `auto_download` is enabled.

## Installation

### Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd kudetranslate
   ```

2. Edit `config.yaml` to configure models, languages, and LLM parameters.

3. Start all services:
   ```bash
   docker compose up -d --build
   ```

4. Access the application:
   - Frontend: http://localhost:4321 (only exposed port)

### First Run

On first run, the backend will automatically:
1. Download all configured models (e.g., TranslateGemma and Ministral)
2. Start the translation service
3. Be ready for translation

The model download may take several minutes depending on your internet connection and model size.

Check backend logs to monitor model download progress:
```bash
docker compose logs -f backend
```

## Translation Queue

KudeTranslate includes a built-in translation queue system for handling concurrent users:

- Only one translation is processed at a time (serialized via semaphore)
- Additional requests are queued and users see their queue position in real-time
- Queue position updates are sent via SSE every 2 seconds
- The frontend displays a banner: "Queue position: X of Y. Waiting for your turn..."
- When it's their turn, the banner disappears and streaming translation begins

This ensures Ollama dedicates all CPU resources to one translation at a time for optimal speed.

## Usage

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config` | GET | Get current configuration |
| `/api/models` | GET | List available and configured models |
| `/api/models/check/<model>` | GET | Check if a model is downloaded |
| `/api/models/download` | POST | Download a model |
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

#### Ollama

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_HOST` | Bind address | `0.0.0.0` |
| `OLLAMA_FLASH_ATTENTION` | Enable flash attention | `1` |
| `OLLAMA_KV_CACHE_TYPE` | KV cache quantization (`q8_0`, `q4_0`) | `q8_0` |
| `OLLAMA_NUM_PARALLEL` | Max parallel requests | `1` |
| `OLLAMA_MAX_LOADED_MODELS` | Models to keep in RAM | `2` |
| `OLLAMA_KEEP_ALIVE` | Time to keep models loaded (`-1` = forever) | `-1` |

#### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_HOST` | Ollama service URL | `http://ollama:11434` |
| `CONFIG_PATH` | Path to configuration file | `/app/config.yaml` |

#### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_URL` | Backend API URL | `http://backend:5000` |

## Development

### Building Images

```bash
# Build all services
docker compose build

# Build specific service
docker compose build backend
docker compose build frontend
```

### Rebuilding After Config Changes

The `config.yaml` is mounted as a volume, but Flask reads it at startup. To apply config changes:

```bash
docker compose up -d --force-recreate backend
```

For code changes, rebuild the image:

```bash
docker compose up -d --build backend
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

## Performance Optimization

### Ollama Settings

The `docker-compose.yml` includes several performance optimizations:

| Setting | Effect |
|---------|--------|
| `OLLAMA_FLASH_ATTENTION=1` | Reduces memory usage and accelerates inference |
| `OLLAMA_KV_CACHE_TYPE=q8_0` | Quantizes KV cache for lower memory footprint |
| `OLLAMA_NUM_PARALLEL=1` | Dedicates all resources to one request at a time |
| `OLLAMA_MAX_LOADED_MODELS=2` | Keeps both models in RAM to avoid reload delays |
| `OLLAMA_KEEP_ALIVE=-1` | Never unloads models from RAM |

### CPU Thread Control

CPU threads are configured via `config.yaml` (`llm.num_thread`) and sent per-request to Ollama. Set this to the number of CPU cores you want to dedicate (e.g., `18` on a 20-core server). A value of `0` lets Ollama decide automatically.

### Gunicorn Configuration

The backend uses 1 Gunicorn worker with Gevent for cooperative concurrency:

```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--worker-connections", "100", "--timeout", "300", "--worker-class", "gevent", "app.main:app"]
```

A single worker is required for the translation queue semaphore to work correctly across all requests. Gevent handles concurrent connections via lightweight greenlets.

## Troubleshooting

### Model Not Found

If you see a model not found error, ensure the backend has finished downloading. Check logs:
```bash
docker compose logs -f backend
```

### Connection Refused

Ensure all services are running:
```bash
docker compose ps
```

### Memory Issues

If you encounter OOM errors, try:
1. Using smaller models (e.g., `translategemma:4b` instead of `8b`)
2. Reducing `OLLAMA_MAX_LOADED_MODELS` to `1`
3. Increasing Docker memory allocation

### Timeout Errors

Translation requests may take time for large texts. Timeouts are configured at multiple levels:
- Gunicorn: 300 seconds
- Frontend proxy: 600 seconds (to accommodate queue waiting time)
- Ollama requests: (10s connect, 300s read)

### Config Changes Not Reflected

Flask reads `config.yaml` once at startup. After editing the file, restart the backend:
```bash
docker compose up -d --force-recreate backend
```

## License

Apache 2.0
