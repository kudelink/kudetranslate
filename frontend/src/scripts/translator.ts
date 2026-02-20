// Type definitions
interface Language {
  code: string;
  name: string;
}

interface Config {
  ollama: {
    host: string;
    default_model: string;
    auto_download: boolean;
  };
  llm: {
    temperature: number;
    max_tokens: number;
    top_p: number;
  };
  translation: {
    default_source_lang: string;
    default_target_lang: string;
  };
  languages: Language[];
}

interface Model {
  name: string;
  size?: number;
  modified_at?: string;
}

// State
let config: Config | null = null;
let models: Model[] = [];
let currentModel: string = '';
let sourceLang: string = 'auto';
let targetLang: string = 'es';
let sourceText: string = '';
let targetText: string = '';
let isLoading: boolean = false;
let errorMessage: string = '';

// API URL - use relative path for reverse proxy
const API_URL = import.meta.env.PUBLIC_API_URL || '';

// DOM Elements
const sourceTextArea = document.getElementById('source-text') as HTMLTextAreaElement;
const targetTextArea = document.getElementById('target-text') as HTMLTextAreaElement;
const sourceLangSelect = document.getElementById('source-lang') as HTMLSelectElement;
const targetLangSelect = document.getElementById('target-lang') as HTMLSelectElement;
const modelSelect = document.getElementById('model-select') as HTMLSelectElement;
const modelSelectMobile = document.getElementById('model-select-mobile') as HTMLSelectElement;
const translateBtn = document.getElementById('translate-btn') as HTMLButtonElement;
const clearBtn = document.getElementById('clear-btn') as HTMLButtonElement;
const swapBtn = document.getElementById('swap-btn') as HTMLButtonElement;
const copyBtn = document.getElementById('copy-btn') as HTMLButtonElement;
const refreshBtn = document.getElementById('refresh-btn') as HTMLButtonElement;
const refreshBtnMobile = document.getElementById('refresh-btn-mobile') as HTMLButtonElement;
const sourceCharCount = document.getElementById('source-char-count');
const targetCharCount = document.getElementById('target-char-count');
const loadingOverlay = document.getElementById('loading-overlay');
const errorDiv = document.getElementById('error-message');
const modelBadge = document.getElementById('model-badge');
const translationStats = document.getElementById('translation-stats');
const statTokens = document.getElementById('stat-tokens');
const statSpeed = document.getElementById('stat-speed');
const statTime = document.getElementById('stat-time');
const settingsBtn = document.getElementById('settings-btn');
const mobileSettingsModal = document.getElementById('mobile-settings-modal');
const closeSettingsBtn = document.getElementById('close-settings-btn');
const themeToggle = document.getElementById('theme-toggle');

// Initialize
async function init() {
  await loadConfig();
  await loadModels();
  setupEventListeners();
}

// Load configuration
async function loadConfig() {
  try {
    const response = await fetch(`${API_URL}/api/config`);
    config = await response.json();

    if (config) {
      currentModel = config.ollama.default_model;
      populateLanguageSelectors();
      updateModelDisplay();
    }
  } catch (error) {
    console.error('Error loading config:', error);
    showError('Could not load configuration. Make sure the backend is running.');
  }
}

// Load available models with retry
async function loadModels(retries: number = 10, delay: number = 3000) {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(`${API_URL}/api/models`);
      const data = await response.json();
      models = data.models || [];

      // If models are available, populate the selector
      if (models.length > 0) {
        populateModelSelector();
        hideError();
        return;
      }

      // No models available yet, retry after delay
      console.log(`No models available yet, retrying... (${i + 1}/${retries})`);
      if (i < retries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    } catch (error) {
      console.error('Error loading models:', error);
      // Retry on connection error
      if (i < retries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  // After all retries, still show error but allow translation to trigger download
  populateModelSelector();
}

// Populate language selectors
function populateLanguageSelectors() {
  if (!config) return;

  const languages = config.languages;

  sourceLangSelect.innerHTML = '';
  targetLangSelect.innerHTML = '';

  languages.forEach(lang => {
    const option = new Option(lang.name, lang.code);
    sourceLangSelect.add(option.cloneNode(true) as HTMLOptionElement);
    targetLangSelect.add(new Option(lang.name, lang.code));
  });

  // Set defaults
  sourceLangSelect.value = config.translation.default_source_lang;
  targetLangSelect.value = config.translation.default_target_lang;
  sourceLang = sourceLangSelect.value;
  targetLang = targetLangSelect.value;
}

// Populate model selector
function populateModelSelector() {
  modelSelect.innerHTML = '';
  if (modelSelectMobile) modelSelectMobile.innerHTML = '';

  if (models.length === 0) {
    const option = new Option('No models available', '');
    modelSelect.add(option);
    if (modelSelectMobile) modelSelectMobile.add(option.cloneNode(true) as HTMLOptionElement);
    return;
  }

  models.forEach(model => {
    // Show full model name with size (e.g., "translategemma:4b")
    const displayName = model.name;
    const option = new Option(displayName, model.name);
    modelSelect.add(option);
    if (modelSelectMobile) modelSelectMobile.add(option.cloneNode(true) as HTMLOptionElement);
  });

  // Set current model
  if (currentModel) {
    const matchingModel = models.find(m => m.name.startsWith(currentModel));
    if (matchingModel) {
      modelSelect.value = matchingModel.name;
      if (modelSelectMobile) modelSelectMobile.value = matchingModel.name;
    }
  }

  currentModel = modelSelect.value;
  updateModelDisplay();
}

// Update model badge display
function updateModelDisplay() {
  if (modelBadge) {
    // Show full model name with size (e.g., "translategemma:4b")
    modelBadge.textContent = currentModel;
  }
  // Sync mobile selector
  if (modelSelectMobile && currentModel) {
    modelSelectMobile.value = currentModel;
  }
}

// Setup event listeners
function setupEventListeners() {
  // Source language change
  sourceLangSelect?.addEventListener('change', () => {
    sourceLang = sourceLangSelect.value;
    // If source matches target (and not auto), swap them
    if (sourceLang !== 'auto' && sourceLang === targetLang) {
      targetLang = targetLangSelect.value = sourceLangSelect.dataset.prev || 'en';
    }
    sourceLangSelect.dataset.prev = sourceLang;
  });

  // Target language change
  targetLangSelect?.addEventListener('change', () => {
    targetLang = targetLangSelect.value;
    // If target matches source (and source is not auto), swap them
    if (sourceLang !== 'auto' && targetLang === sourceLang) {
      sourceLang = sourceLangSelect.value = targetLangSelect.dataset.prev || 'en';
    }
    targetLangSelect.dataset.prev = targetLang;
  });

  // Model change
  modelSelect?.addEventListener('change', async () => {
    const selectedModel = modelSelect.value;
    if (selectedModel && selectedModel !== currentModel) {
      currentModel = selectedModel;
      updateModelDisplay();

      // Check if model needs to be downloaded
      await checkAndDownloadModel(selectedModel);
    }
  });

  // Refresh models
  refreshBtn?.addEventListener('click', async () => {
    refreshBtn.disabled = true;
    await loadModels();
    refreshBtn.disabled = false;
  });

  // Source text change
  sourceTextArea?.addEventListener('input', () => {
    sourceText = sourceTextArea.value;
    updateCharCount();
  });

  // Translate button
  translateBtn?.addEventListener('click', translate);

  // Keyboard shortcut (Ctrl+Enter to translate)
  sourceTextArea?.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
      e.preventDefault();
      translate();
    }
  });

  // Swap button
  swapBtn?.addEventListener('click', swapLanguages);

  // Copy button
  copyBtn?.addEventListener('click', copyTranslation);

  // Clear button
  clearBtn?.addEventListener('click', () => {
    sourceTextArea.value = '';
    targetTextArea.value = '';
    sourceText = '';
    targetText = '';
    if (translationStats) translationStats.style.display = 'none';
    updateCharCount();
  });

  // Mobile settings modal
  settingsBtn?.addEventListener('click', () => {
    if (mobileSettingsModal) {
      mobileSettingsModal.style.display = 'flex';
    }
  });

  closeSettingsBtn?.addEventListener('click', () => {
    if (mobileSettingsModal) {
      mobileSettingsModal.style.display = 'none';
    }
  });

  mobileSettingsModal?.addEventListener('click', (e) => {
    if (e.target === mobileSettingsModal) {
      mobileSettingsModal.style.display = 'none';
    }
  });

  // Mobile model select
  modelSelectMobile?.addEventListener('change', async () => {
    const selectedModel = modelSelectMobile.value;
    if (selectedModel && selectedModel !== currentModel) {
      currentModel = selectedModel;
      updateModelDisplay();
      if (modelSelect) modelSelect.value = selectedModel;
      await checkAndDownloadModel(selectedModel);
    }
  });

  // Mobile refresh button
  refreshBtnMobile?.addEventListener('click', async () => {
    refreshBtnMobile.disabled = true;
    await loadModels();
    refreshBtnMobile.disabled = false;
  });

  // Theme toggle
  themeToggle?.addEventListener('click', () => {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  });
}

// Update character count
function updateCharCount() {
  if (sourceCharCount) {
    sourceCharCount.textContent = `${sourceText.length} characters`;
  }
  if (targetCharCount) {
    targetCharCount.textContent = `${targetText.length} characters`;
  }
}

// Check and download model if needed
async function checkAndDownloadModel(modelName: string) {
  showLoading();

  try {
    const response = await fetch(`${API_URL}/api/models/check/${modelName}`);
    const data = await response.json();

    if (!data.exists && config?.ollama.auto_download) {
      showLoading();
      await downloadModel(modelName);
    }
  } catch (error) {
    console.error('Error checking model:', error);
  } finally {
    hideLoading();
  }
}

// Download model
async function downloadModel(modelName: string) {
  try {
    const response = await fetch(`${API_URL}/api/models/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_name: modelName })
    });

    const data = await response.json();
    if (data.success) {
      await loadModels();
    }
  } catch (error) {
    console.error('Error downloading model:', error);
    showError('Failed to download model.');
  }
}

// Translate text with streaming
async function translate() {
  if (!sourceText.trim()) {
    showError('Please enter text to translate.');
    return;
  }

  hideError();
  showLoading();

  // Clear previous translation and stats
  targetTextArea.value = '';
  targetText = '';
  if (translationStats) translationStats.style.display = 'none';
  updateCharCount();

  try {
    const response = await fetch(`${API_URL}/api/translate/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: sourceText,
        source_lang: sourceLang,
        target_lang: targetLang,
        model: currentModel
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('Response body is null');
    }

    let done = false;
    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;

      if (value) {
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.error) {
                showError(data.error);
                hideLoading();
                return;
              }

              // Queue status updates
              if (data.queue === true) {
                showQueueStatus(data.position, data.total);
                continue;
              }
              if (data.started === true) {
                hideQueueStatus();
                continue;
              }

              if (data.token) {
                targetText += data.token;
                targetTextArea.value = targetText;
                targetTextArea.scrollTop = targetTextArea.scrollHeight;
                updateCharCount();
              }

              // Show stats when done
              if (data.done && data.eval_count) {
                if (statTokens) statTokens.textContent = `${data.eval_count} tokens`;
                if (statSpeed) statSpeed.textContent = `${data.tokens_per_second} tok/s`;
                if (statTime) statTime.textContent = `${data.eval_duration_ms}ms`;
                if (translationStats) translationStats.style.display = 'flex';
              }

              if (data.done) {
                break;
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    }
  } catch (error) {
    console.error('Translation error:', error);
    showError('Translation failed. Please try again.');
  } finally {
    hideLoading();
  }
}

// Swap languages and text
function swapLanguages() {
  const tempLang = sourceLang;
  const tempText = sourceText;

  sourceLang = targetLang;
  targetLang = tempLang;
  sourceText = targetText;
  targetText = tempText;

  sourceLangSelect.value = sourceLang;
  targetLangSelect.value = targetLang;
  sourceTextArea.value = sourceText;
  targetTextArea.value = targetText;

  updateCharCount();
}

// Copy translation to clipboard
async function copyTranslation() {
  if (!targetText) return;

  try {
    await navigator.clipboard.writeText(targetText);
    const originalText = copyBtn?.textContent;
    if (copyBtn) {
      copyBtn.textContent = 'Copied!';
      setTimeout(() => {
        copyBtn.textContent = originalText || 'Copy';
      }, 2000);
    }
  } catch (error) {
    console.error('Failed to copy:', error);
  }
}

// Show/hide loading
function showLoading() {
  isLoading = true;
  updateButtonStates();
}

function hideLoading() {
  isLoading = false;
  hideQueueStatus();
  updateButtonStates();
}

// Update button states
function updateButtonStates() {
  if (translateBtn) {
    translateBtn.disabled = isLoading || !sourceText.trim();
  }
  if (swapBtn) {
    swapBtn.disabled = isLoading;
    swapBtn.classList.toggle('translating', isLoading);
  }
}

// Show/hide queue status
const queueBanner = document.getElementById('queue-banner');
const queueText = document.getElementById('queue-text');

function showQueueStatus(position: number, total: number) {
  if (queueBanner && queueText) {
    queueText.textContent = `Queue position: ${position} of ${total}. Waiting for your turn...`;
    queueBanner.style.display = 'flex';
  }
}

function hideQueueStatus() {
  if (queueBanner) {
    queueBanner.style.display = 'none';
  }
}

// Show/hide error
function showError(message: string) {
  if (errorDiv) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
  }
}

function hideError() {
  if (errorDiv) {
    errorDiv.style.display = 'none';
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', init);
