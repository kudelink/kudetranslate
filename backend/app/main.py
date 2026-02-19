import os
import yaml
import logging
import json
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from app.translator import Translator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Load configuration
CONFIG_PATH = os.environ.get('CONFIG_PATH', '/app/config.yaml')

def load_config():
    """Load configuration from YAML file."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

config = load_config()

# Initialize translator
ollama_config = config.get('ollama', {})
llm_config = config.get('llm', {})

translator = Translator(
    ollama_host=ollama_config.get('host', 'http://ollama:11434'),
    default_model=ollama_config.get('default_model', 'llama3.2'),
    temperature=llm_config.get('temperature', 0.3),
    max_tokens=llm_config.get('max_tokens', 2048),
    top_p=llm_config.get('top_p', 0.9),
    num_thread=llm_config.get('num_thread', 0)
)

auto_download = ollama_config.get('auto_download', True)

# Load configured models with their prompt types
configured_models = config.get('models', [])
model_prompt_types = {m['name']: m.get('prompt_type', 'generic') for m in configured_models}


def ensure_models_downloaded():
    """Ensure all configured models are downloaded on startup."""
    if not auto_download:
        return

    model_names = [m['name'] for m in configured_models]
    if not model_names:
        model_names = [ollama_config.get('default_model', 'translategemma:4b')]

    for model_name in model_names:
        try:
            if not translator.check_model_exists(model_name):
                logger.info(f"Model {model_name} not found. Downloading...")
                success = translator.download_model(model_name)
                if success:
                    logger.info(f"Model {model_name} downloaded successfully")
                else:
                    logger.warning(f"Failed to download model {model_name}")
            else:
                logger.info(f"Model {model_name} is already available")
        except Exception as e:
            logger.warning(f"Error checking/downloading model {model_name}: {e}")


# Download all configured models on startup
ensure_models_downloaded()


@app.route('/api/config', methods=['GET'])
def get_config():
    """Return current configuration."""
    return jsonify({
        'ollama': ollama_config,
        'llm': llm_config,
        'translation': config.get('translation', {}),
        'languages': config.get('languages', []),
        'models': configured_models
    })


@app.route('/api/models', methods=['GET'])
def get_models():
    """Get list of available and configured models."""
    available = translator.get_available_models()
    available_names = {m.get('name', '') for m in available}

    # Add configured models that aren't downloaded yet
    for cm in configured_models:
        name = cm['name']
        if not any(a.startswith(name) for a in available_names):
            available.append({'name': name, 'downloaded': False})
        else:
            # Mark downloaded models
            for m in available:
                if m.get('name', '').startswith(name):
                    m['downloaded'] = True

    return jsonify({'models': available})


@app.route('/api/models/check/<model_name>', methods=['GET'])
def check_model(model_name):
    """Check if a model exists."""
    exists = translator.check_model_exists(model_name)
    return jsonify({'exists': exists, 'model': model_name})


@app.route('/api/models/download', methods=['POST'])
def download_model():
    """Download a model."""
    data = request.get_json()
    model_name = data.get('model_name')

    if not model_name:
        return jsonify({'error': 'model_name is required'}), 400

    success = translator.download_model(model_name)
    return jsonify({'success': success, 'model': model_name})


@app.route('/api/translate/stream', methods=['POST'])
def translate_stream():
    """Translate text with streaming response."""
    data = request.get_json()

    text = data.get('text', '')
    source_lang = data.get('source_lang', 'auto')
    target_lang = data.get('target_lang', 'es')
    model = data.get('model')

    if not text:
        return jsonify({'translated_text': ''})

    def generate():
        try:
            # Use default model if none specified
            model_to_use = model or translator.default_model

            # Check if model exists, download if needed
            if auto_download and not translator.check_model_exists(model_to_use):
                logger.info(f"Auto-downloading model: {model_to_use}")
                download_success = translator.download_model(model_to_use)
                if not download_success:
                    yield f"data: {json.dumps({'error': f'Failed to download model {model_to_use}'})}\n\n"
                    return

            # Track stats
            stats = None

            # Resolve prompt type for this model
            prompt_type = model_prompt_types.get(model_to_use, 'generic')

            for chunk in translator.translate_stream(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                model=model_to_use,
                prompt_type=prompt_type
            ):
                if 'response' in chunk:
                    # Check if this is the last chunk with stats
                    if chunk.get('done', False):
                        # Calculate stats
                        eval_count = chunk.get('eval_count', 0)
                        eval_duration = chunk.get('eval_duration', 0)  # nanoseconds

                        tokens_per_second = 0
                        if eval_duration > 0:
                            tokens_per_second = (eval_count / eval_duration) * 1e9  # convert to seconds

                        stats = {
                            'token': chunk['response'],
                            'done': True,
                            'eval_count': eval_count,
                            'tokens_per_second': round(tokens_per_second, 2),
                            'eval_duration_ms': round(eval_duration / 1e6, 2)
                        }
                        yield f"data: {json.dumps(stats)}\n\n"
                    else:
                        yield f"data: {json.dumps({'token': chunk['response'], 'done': False})}\n\n"

        except Exception as e:
            logger.error(f"Translation error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
