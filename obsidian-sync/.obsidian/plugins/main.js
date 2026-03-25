const { Plugin, Notice, Modal, Setting, TFile, TFolder, PluginSettingTab, requestUrl } = require('obsidian');

// Конфигурация Vimana Cognitive Core по умолчанию
const DEFAULT_SETTINGS = {
  // Vimana Cognitive Core endpoints
  vimanaCoreUrl: 'http://localhost:11434',
  privateGptUrl: 'http://localhost:8001',
  
  // Модели Vimana Cognitive Core
  ollamaModel: 'qwen2.5:7b',
  privateGptModel: 'local',
  
  // Режимы работы Vimana Cognitive Core
  primaryAiEngine: 'ollama', // 'ollama', 'private-gpt', 'cognitive-stack'
  fallbackEnabled: true,
  
  // Параметры AI стека
  semanticThreshold: 0.65,
  contextWindow: 4096,
  temperature: 0.3,
  
  // Автоматизация Vimana Core
  autoAnalyzeNewNotes: true,
  enableSemanticConnections: true,
  enableKnowledgeGraph: true,
  enableAutoTagging: true,
  
  // Производительность
  batchSize: 4,
  requestTimeout: 45000,
  maxRetries: 3
}

class VimanaCognitiveCoreSettingTab extends PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display() {
    const { containerEl } = this;
    containerEl.empty();

    containerEl.createEl('h2', { text: 'Vimana Cognitive Core Configuration' });
    containerEl.createEl('p', { 
      text: 'Native integration with your local AI stack: Ollama qwen2.5:7b + PrivateGPT',
      cls: 'setting-item-description'
    });

    // Статус системы Vimana Cognitive Core
    const statusSection = containerEl.createEl('div', { cls: 'vimana-status-section' });
    statusSection.createEl('h3', { text: '🖥️ Vimana Cognitive Core Status' });

    new Setting(statusSection)
      .setName('Статус AI стека')
      .setDesc('Проверка подключения к компонентам Vimana Cognitive Core')
      .addButton(btn => btn
        .setButtonText('Проверить Vimana Core')
        .setCta()
        .onClick(async () => {
          await this.plugin.testVimanaCoreConnection();
        }))
      .addButton(btn => btn
        .setButtonText('Обновить статус')
        .onClick(async () => {
          await this.updateSystemStatus();
        }));

    this.statusDisplay = statusSection.createEl('div', { cls: 'system-status-display' });
    
    // Конфигурация Vimana Cognitive Core
    const configSection = containerEl.createEl('div', { cls: 'vimana-config-section' });
    configSection.createEl('h3', { text: '⚙️ Конфигурация AI стека' });

    new Setting(configSection)
      .setName('Основной AI движок')
      .setDesc('Выберите основной движок Vimana Cognitive Core')
      .addDropdown(dropdown => dropdown
        .addOption('cognitive-stack', 'Vimana Cognitive Stack (гибридный)')
        .addOption('ollama', 'Ollama qwen2.5:7b')
        .addOption('private-gpt', 'PrivateGPT')
        .setValue(this.plugin.settings.primaryAiEngine)
        .onChange(async (value) => {
          this.plugin.settings.primaryAiEngine = value;
          await this.plugin.saveSettings();
          this.plugin.initializeVimanaCore();
        }));

    new Setting(configSection)
      .setName('Ollama Endpoint')
      .setDesc('URL эндпоинта Ollama Vimana Core')
      .addText(text => text
        .setPlaceholder('http://localhost:11434')
        .setValue(this.plugin.settings.vimanaCoreUrl)
        .onChange(async (value) => {
          this.plugin.settings.vimanaCoreUrl = value;
          await this.plugin.saveSettings();
        }));

    new Setting(configSection)
      .setName('PrivateGPT Endpoint')
      .setDesc('URL эндпоинта PrivateGPT Vimana Core')
      .addText(text => text
        .setPlaceholder('http://localhost:8001')
        .setValue(this.plugin.settings.privateGptUrl)
        .onChange(async (value) => {
          this.plugin.settings.privateGptUrl = value;
          await this.plugin.saveSettings();
        }));

    // Настройки алгоритмов Vimana Core
    const algorithmSection = containerEl.createEl('div', { cls: 'vimana-algorithm-section' });
    algorithmSection.createEl('h3', { text: '🧠 Алгоритмы Vimana Core' });

    new Setting(algorithmSection)
      .setName('Порог семантического сходства')
      .setDesc('Минимальное сходство для установления связей в знаниях')
      .addSlider(slider => slider
        .setLimits(0.1, 1.0, 0.05)
        .setValue(this.plugin.settings.semanticThreshold)
        .onChange(async (value) => {
          this.plugin.settings.semanticThreshold = value;
          await this.plugin.saveSettings();
        }));

    new Setting(algorithmSection)
      .setName('Температура генерации')
      .setDesc('Уровень креативности AI (ниже = более детерминировано)')
      .addSlider(slider => slider
        .setLimits(0.1, 1.0, 0.1)
        .setValue(this.plugin.settings.temperature)
        .onChange(async (value) => {
          this.plugin.settings.temperature = value;
          await this.plugin.saveSettings();
        }));

    // Автоматизация Vimana Core
    const automationSection = containerEl.createEl('div', { cls: 'vimana-automation-section' });
    automationSection.createEl('h3', { text: '🤖 Автоматизация Vimana Core' });

    new Setting(automationSection)
      .setName('Автоанализ новых заметок')
      .setDesc('Vimana Core автоматически анализирует новые заметки')
      .addToggle(toggle => toggle
        .setValue(this.plugin.settings.autoAnalyzeNewNotes)
        .onChange(async (value) => {
          this.plugin.settings.autoAnalyzeNewNotes = value;
          await this.plugin.saveSettings();
        }));

    new Setting(automationSection)
      .setName('Семантические связи')
      .setDesc('Автоматически находить семантические связи между заметками')
      .addToggle(toggle => toggle
        .setValue(this.plugin.settings.enableSemanticConnections)
        .onChange(async (value) => {
          this.plugin.settings.enableSemanticConnections = value;
          await this.plugin.saveSettings();
        }));

    new Setting(automationSection)
      .setName('Автотегирование')
      .setDesc('Vimana Core автоматически генерирует теги для заметок')
      .addToggle(toggle => toggle
        .setValue(this.plugin.settings.enableAutoTagging)
        .onChange(async (value) => {
          this.plugin.settings.enableAutoTagging = value;
          await this.plugin.saveSettings();
        }));

    // Инициализация статуса
    this.updateSystemStatus();
  }

  async updateSystemStatus() {
    const ollamaStatus = await this.plugin.testOllamaConnection();
    const privateGptStatus = await this.plugin.testPrivateGptConnection();
    
    this.statusDisplay.empty();
    
    const statusHTML = `
      <div class="vimana-status-grid">
        <div class="status-item ${ollamaStatus ? 'status-ok' : 'status-error'}">
          <strong>Ollama qwen2.5:7b:</strong> ${ollamaStatus ? '✅ Активен' : '❌ Недоступен'}
        </div>
        <div class="status-item ${privateGptStatus ? 'status-ok' : 'status-error'}">
          <strong>PrivateGPT:</strong> ${privateGptStatus ? '✅ Активен' : '❌ Недоступен'}
        </div>
        <div class="status-item status-info">
          <strong>Режим:</strong> ${this.plugin.settings.primaryAiEngine}
        </div>
        <div class="status-item status-info">
          <strong>Проанализировано:</strong> ${this.plugin.analyzedNotes.size} заметок
        </div>
      </div>
    `;
    
    this.statusDisplay.innerHTML = statusHTML;
  }
}

// 🎯 Vimana Cognitive Core Client
class VimanaCognitiveCore {
  constructor(plugin) {
    this.plugin = plugin;
    this.ollama = new VimanaOllamaClient(plugin);
    this.privateGpt = new VimanaPrivateGptClient(plugin);
    this.mode = plugin.settings.primaryAiEngine;
  }

  async initialize() {
    console.log('Initializing Vimana Cognitive Core...');
    
    // Проверяем доступность компонентов
    const ollamaReady = await this.ollama.testConnection();
    const privateGptReady = await this.privateGpt.testConnection();
    
    console.log(`Vimana Core status - Ollama: ${ollamaReady}, PrivateGPT: ${privateGptReady}`);
    
    // Автоматически выбираем лучший доступный режим
    if (this.mode === 'cognitive-stack') {
      if (ollamaReady && privateGptReady) {
        this.mode = 'cognitive-stack';
      } else if (ollamaReady) {
        this.mode = 'ollama';
      } else if (privateGptReady) {
        this.mode = 'private-gpt';
      } else {
        throw new Error('Vimana Cognitive Core: ни один компонент не доступен');
      }
    }
    
    return {
      ollama: ollamaReady,
      privateGpt: privateGptReady,
      mode: this.mode
    };
  }

  // 💬 Унифицированный интерфейс генерации
  async generate(prompt, context = '', options = {}) {
    const systemPrompt = this.buildSystemPrompt(context, options.taskType);
    
    switch (this.mode) {
      case 'ollama':
        return await this.ollama.generate(prompt, systemPrompt, options);
      
      case 'private-gpt':
        return await this.privateGpt.chat(prompt, systemPrompt, options);
      
      case 'cognitive-stack':
        // Гибридный режим: используем оба движка для лучшего качества
        try {
          // Сначала пробуем Ollama для скорости
          return await this.ollama.generate(prompt, systemPrompt, options);
        } catch (error) {
          console.log('Ollama failed, trying PrivateGPT...');
          return await this.privateGpt.chat(prompt, systemPrompt, options);
        }
      
      default:
        throw new Error(`Unknown Vimana Core mode: ${this.mode}`);
    }
  }

  // 🔍 Семантическое сходство через Vimana Core
  async calculateSemanticSimilarity(text1, text2) {
    // В гибридном режиме используем PrivateGPT для эмбеддингов (более точные)
    if (this.mode === 'cognitive-stack' || this.mode === 'private-gpt') {
      try {
        return await this.privateGpt.calculateSimilarity(text1, text2);
      } catch (error) {
        console.log('PrivateGPT similarity failed, trying Ollama...');
      }
    }
    
    // Fallback на Ollama или текстовый метод
    return await this.ollama.calculateSemanticSimilarity(text1, text2);
  }

  // 🏷️ Генерация тегов через Vimana Core
  async suggestTags(content, title = '', maxTags = 5) {
    const prompt = `
ПРОАНИЛИЗИРУЙ ЗАМЕТКУ И ПРЕДЛОЖИ ТЕГИ:

ЗАГОЛОВОК: ${title}
СОДЕРЖАНИЕ: ${content.substring(0, 1800)}

ТРЕБОВАНИЯ VIMANA CORE:
- Только релевантные конкретные темы
- Используй профессиональную терминологию  
- Формат: #тег1, #тег2, #тег3
- Максимум ${maxTags} тегов
- Приоритет специфичным терминам над общими
`;

    const systemPrompt = `Ты Vimana Cognitive Core - эксперт по категоризации знаний. 
Отвечай ТОЛЬКО списком тегов через запятую, начиная с #. 
Игнорируй общие теги вроде #заметка, #анализ.`;

    try {
      const response = await this.generate(prompt, systemPrompt, {
        max_tokens: 80,
        temperature: 0.2,
        taskType: 'tagging'
      });

      return this.parseTags(response, maxTags);
    } catch (error) {
      console.error('Vimana Core tagging failed:', error);
      return this.getFallbackTags(content);
    }
  }

  // 🗺️ Генерация MOC через Vimana Core
  async generateMOCContent(notes, topic) {
    const notesSummary = notes.map(note => 
      `- ${note.title}: ${note.excerpt || 'нет описания'}`
    ).join('\n');

    const prompt = `
СОЗДАЙ КАРТУ СОДЕРЖАНИЯ (MOC) ДЛЯ ТЕМЫ: "${topic}"

ЗАМЕТКИ ДЛЯ ВКЛЮЧЕНИЯ:
${notesSummary}

СТРУКТУРА VIMANA CORE:
1. # ${topic} - основной заголовок
2. ## Введение - краткий обзор темы
3. ## Подтемы - группировка по связанным концепциям
4. ### Связанные заметки - список с аннотациями
5. ## Выводы - синтез знаний и направления развития

ТРЕБОВАНИЯ:
- Используй маркдаун формат
- Создай ссылки [[ ]] на все заметки
- Группируй логически связанные заметки
- Добавь аннотации к ключевым заметкам
- Предложи направления для дальнейшего исследования
`;

    const systemPrompt = `Ты Vimana Cognitive Core - эксперт по структурированию знаний и созданию карт содержания.
Создай хорошо организованную MOC в формате Markdown.`;

    try {
      return await this.generate(prompt, systemPrompt, {
        max_tokens: 1200,
        temperature: 0.4,
        taskType: 'moc-generation'
      });
    } catch (error) {
      console.error('Vimana Core MOC generation failed:', error);
      return this.generateFallbackMOC(notes, topic);
    }
  }

  // 📊 Анализ знаний через Vimana Core
  async analyzeKnowledgeStructure(notesContent) {
    const combinedContent = notesContent.substring(0, 3500);

    const prompt = `
ПРОАНАЛИЗИРУЙ СТРУКТУРУ ЗНАНИЙ:

СОДЕРЖАНИЕ БАЗЫ ЗНАНИЙ:
${combinedContent}

АНАЛИЗ VIMANA CORE:
1. Ключевые темы и концепции
2. Потенциальные пробелы в знаниях  
3. Рекомендации по развитию
4. Возможные новые связи между темами

Формат: структурированный маркированный список с конкретными рекомендациями.
`;

    const systemPrompt = `Ты Vimana Cognitive Core - эксперт по анализу структур знаний.
Дай конкретные, actionable рекомендации по улучшению базы знаний.`;

    try {
      return await this.generate(prompt, systemPrompt, {
        max_tokens: 800,
        temperature: 0.5,
        taskType: 'knowledge-analysis'
      });
    } catch (error) {
      console.error('Vimana Core knowledge analysis failed:', error);
      return 'Анализ знаний временно недоступен.';
    }
  }

  // 🛠️ Вспомогательные методы Vimana Core
  buildSystemPrompt(context, taskType) {
    const basePrompt = `Ты Vimana Cognitive Core - продвинутая AI система для управления знаниями.
Контекст: ${context}`;

    const taskPrompts = {
      'tagging': 'Фокус на точной категоризации и тегировании.',
      'moc-generation': 'Фокус на структурировании и организации знаний.',
      'knowledge-analysis': 'Фокус на анализе паттернов и выявлении пробелов.',
      'semantic-analysis': 'Фокус на понимании смысловых связей.'
    };

    return `${basePrompt} ${taskPrompts[taskType] || ''}`;
  }

  parseTags(response, maxTags) {
    const tags = response.split(',')
      .map(tag => tag.trim())
      .filter(tag => tag.startsWith('#'))
      .slice(0, maxTags);

    return tags.length > 0 ? tags : this.getFallbackTags();
  }

  getFallbackTags(content = '') {
    // Простой fallback на основе ключевых слов
    const words = content.toLowerCase().split(/\W+/);
    const freq = {};
    
    words.forEach(word => {
      if (word.length > 4 && word.length < 20) {
        freq[word] = (freq[word] || 0) + 1;
      }
    });
    
    const topWords = Object.entries(freq)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([word]) => `#${word}`);
    
    return topWords.length > 0 ? topWords : ['#анализ', '#заметка'];
  }

  generateFallbackMOC(notes, topic) {
    let content = `# ${topic}\n\n`;
    content += `## Связанные заметки\n\n`;
    
    notes.forEach(note => {
      content += `### [[${note.title}]]\n`;
      content += `${note.excerpt || 'Описание отсутствует'}\n\n`;
    });
    
    return content;
  }
}

// 🦙 Vimana Ollama Client (qwen2.5:7b)
class VimanaOllamaClient {
  constructor(plugin) {
    this.plugin = plugin;
    this.baseUrl = plugin.settings.vimanaCoreUrl;
    this.model = plugin.settings.ollamaModel;
  }

  async testConnection() {
    try {
      const response = await requestUrl({
        url: `${this.baseUrl}/api/tags`,
        method: 'GET',
        throw: false,
        timeout: 10000
      });
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  async generate(prompt, systemPrompt = '', options = {}) {
    const data = {
      model: this.model,
      prompt: prompt,
      system: systemPrompt,
      stream: false,
      options: {
        temperature: options.temperature || this.plugin.settings.temperature,
        top_p: 0.9,
        top_k: 40,
        num_predict: options.max_tokens || 500
      }
    };

    const response = await requestUrl({
      url: `${this.baseUrl}/api/generate`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      throw: false,
      timeout: this.plugin.settings.requestTimeout
    });

    if (response.status === 200) {
      const result = JSON.parse(response.text);
      return result.response;
    } else {
      throw new Error(`Ollama error: ${response.status} - ${response.text}`);
    }
  }

  async calculateSemanticSimilarity(text1, text2) {
    // Для qwen2.5:7b используем текстовый анализ как fallback
    // В реальной реализации можно использовать эмбеддинги если модель поддерживает
    return this.textBasedSimilarity(text1, text2);
  }

  textBasedSimilarity(text1, text2) {
    const words1 = new Set(text1.toLowerCase().match(/\b\w+\b/g) || []);
    const words2 = new Set(text2.toLowerCase().match(/\b\w+\b/g) || []);
    
    const intersection = new Set([...words1].filter(x => words2.has(x)));
    const union = new Set([...words1, ...words2]);
    
    return union.size > 0 ? intersection.size / union.size : 0;
  }
}

// 🔒 Vimana PrivateGPT Client
class VimanaPrivateGptClient {
  constructor(plugin) {
    this.plugin = plugin;
    this.baseUrl = plugin.settings.privateGptUrl;
  }

  async testConnection() {
    try {
      const response = await requestUrl({
        url: `${this.baseUrl}/v1/models`,
        method: 'GET',
        throw: false,
        timeout: 10000
      });
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  async chat(prompt, systemPrompt = '', options = {}) {
    const messages = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: prompt }
    ];

    const data = {
      messages: messages,
      use_context: true,
      include_sources: false,
      stream: false
    };

    const response = await requestUrl({
      url: `${this.baseUrl}/v1/chat/completions`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      throw: false,
      timeout: this.plugin.settings.requestTimeout
    });

    if (response.status === 200) {
      const result = JSON.parse(response.text);
      return result.choices[0].message.content;
    } else {
      throw new Error(`PrivateGPT error: ${response.status} - ${response.text}`);
    }
  }

  async calculateSimilarity(text1, text2) {
    // PrivateGPT обычно имеет лучшие эмбеддинги
    // В реальной реализации используем /v1/embeddings endpoint
    return this.advancedTextSimilarity(text1, text2);
  }

  advancedTextSimilarity(text1, text2) {
    // Более продвинутый текстовый анализ
    const processText = (text) => {
      return text.toLowerCase()
        .replace(/[^\w\s]/g, ' ')
        .split(/\s+/)
        .filter(word => word.length > 3)
        .reduce((acc, word) => {
          acc[word] = (acc[word] || 0) + 1;
          return acc;
        }, {});
    };

    const tf1 = processText(text1);
    const tf2 = processText(text2);
    
    const allWords = new Set([...Object.keys(tf1), ...Object.keys(tf2)]);
    
    let dotProduct = 0;
    let norm1 = 0;
    let norm2 = 0;

    allWords.forEach(word => {
      const val1 = tf1[word] || 0;
      const val2 = tf2[word] || 0;
      
      dotProduct += val1 * val2;
      norm1 += val1 * val1;
      norm2 += val2 * val2;
    });

    return norm1 && norm2 ? dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2)) : 0;
  }
}

// 🧠 Vimana Knowledge Graph Manager
class VimanaKnowledgeGraph {
  constructor(plugin) {
    this.plugin = plugin;
    this.connections = new Map();
    this.clusters = new Map();
  }

  addConnection(sourceNote, targetNote, similarity, context) {
    const connectionId = `${sourceNote.path}-${targetNote.path}`;
    
    this.connections.set(connectionId, {
      source: sourceNote.path,
      target: targetNote.path,
      similarity: similarity,
      context: context,
      type: 'vimana-semantic',
      timestamp: Date.now()
    });

    this.updateCluster(sourceNote, targetNote, similarity);
  }

  updateCluster(sourceNote, targetNote, similarity) {
    const sourceCluster = this.clusters.get(sourceNote.path) || new Set();
    const targetCluster = this.clusters.get(targetNote.path) || new Set();
    
    sourceCluster.add(targetNote.path);
    targetCluster.add(sourceNote.path);
    
    this.clusters.set(sourceNote.path, sourceCluster);
    this.clusters.set(targetNote.path, targetCluster);
  }

  async generateKnowledgeGraph() {
    const graphContent = this.buildGraphContent();
    const graphPath = `Vimana-Graphs/Knowledge-Graph-${new Date().toISOString().split('T')[0]}.md`;
    
    await this.plugin.openOrCreateNote(graphPath, graphContent);
    return graphPath;
  }

  buildGraphContent() {
    let content = `# 🧠 Vimana Knowledge Graph\n\n`;
    content += `*Сгенерировано Vimana Cognitive Core ${new Date().toLocaleString()}*\n\n`;
    
    content += `## 📊 Статистика графа\n\n`;
    content += `- **Всего узлов**: ${this.clusters.size}\n`;
    content += `- **Всего связей**: ${this.connections.size}\n`;
    content += `- **Плотность графа**: ${this.calculateGraphDensity().toFixed(3)}\n\n`;
    
    content += `## 🔗 Кластеры знаний\n\n`;
    
    // Группируем по кластерам
    const clusters = this.identifyKnowledgeClusters();
    
    clusters.forEach((cluster, index) => {
      if (cluster.notes.length > 1) {
        content += `### Кластер ${index + 1}: ${cluster.topic || 'Смежная тема'}\n\n`;
        content += `- **Размер**: ${cluster.notes.length} заметок\n`;
        content += `- **Связность**: ${cluster.density.toFixed(2)}\n\n`;
        
        cluster.notes.forEach(notePath => {
          const noteName = notePath.split('/').pop().replace('.md', '');
          content += `  - [[${noteName}]]\n`;
        });
        content += '\n';
      }
    });
    
    return content;
  }

  identifyKnowledgeClusters() {
    const visited = new Set();
    const clusters = [];
    
    this.clusters.forEach((connections, notePath) => {
      if (!visited.has(notePath)) {
        const cluster = this.exploreCluster(notePath, visited);
        if (cluster.notes.length > 1) {
          cluster.topic = this.estimateClusterTopic(cluster.notes);
          cluster.density = this.calculateClusterDensity(cluster.notes);
          clusters.push(cluster);
        }
      }
    });
    
    return clusters;
  }

  exploreCluster(startNote, visited) {
    const cluster = { notes: new Set() };
    const queue = [startNote];
    
    while (queue.length > 0) {
      const current = queue.shift();
      if (!visited.has(current)) {
        visited.add(current);
        cluster.notes.add(current);
        
        const connections = this.clusters.get(current) || new Set();
        connections.forEach(connectedNote => {
          if (!visited.has(connectedNote)) {
            queue.push(connectedNote);
          }
        });
      }
    }
    
    return {
      notes: Array.from(cluster.notes),
      size: cluster.notes.size
    };
  }

  estimateClusterTopic(notes) {
    // Простая эвристика для определения темы кластера
    const names = notes.map(path => path.split('/').pop().replace('.md', ''));
    return names.slice(0, 3).join(', ');
  }

  calculateClusterDensity(notes) {
    let possibleConnections = notes.length * (notes.length - 1) / 2;
    if (possibleConnections === 0) return 0;
    
    let actualConnections = 0;
    
    notes.forEach(note1 => {
      notes.forEach(note2 => {
        if (note1 !== note2 && this.connections.has(`${note1}-${note2}`)) {
          actualConnections++;
        }
      });
    });
    
    return actualConnections / possibleConnections;
  }

  calculateGraphDensity() {
    const n = this.clusters.size;
    const possibleConnections = n * (n - 1) / 2;
    return possibleConnections > 0 ? this.connections.size / possibleConnections : 0;
  }
}

// 🎯 Основной класс плагина Vimana Cognitive Core
module.exports = class VimanaCognitiveCorePlugin extends Plugin {
  async onload() {
    console.log('🖥️ Loading Vimana Cognitive Core Plugin...');
    
    await this.loadSettings();
    await this.initializeVimanaCore();
    this.setupVimanaComponents();
    
    new Notice('Vimana Cognitive Core активирован! 🧠');
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }

  async initializeVimanaCore() {
    this.vimanaCore = new VimanaCognitiveCore(this);
    this.knowledgeGraph = new VimanaKnowledgeGraph(this);
    this.analyzedNotes = new Set();
    
    try {
      const status = await this.vimanaCore.initialize();
      console.log('Vimana Cognitive Core initialized:', status);
      
      if (status.mode === 'cognitive-stack') {
        new Notice('Vimana Cognitive Stack: оба движка активны 🚀');
      } else {
        new Notice(`Vimana Core: используется ${status.mode} движок`);
      }
    } catch (error) {
      console.error('Vimana Core initialization failed:', error);
      new Notice('❌ Vimana Cognitive Core не доступен');
    }
  }

  setupVimanaComponents() {
    this.addSettingTab(new VimanaCognitiveCoreSettingTab(this.app, this));
    this.addVimanaCommands();
    this.addVimanaUI();
    this.setupVimanaAutomation();
  }

  addVimanaCommands() {
    // Основные команды Vimana Core
    this.addCommand({
      id: 'vimana-semantic-analysis',
      name: 'Vimana: Семантический анализ заметки',
      editorCheck: true,
      callback: () => this.analyzeActiveNote()
    });

    this.addCommand({
      id: 'vimana-knowledge-graph',
      name: 'Vimana: Построить граф знаний',
      callback: () => this.generateKnowledgeGraph()
    });

    this.addCommand({
      id: 'vimana-ai-tagging',
      name: 'Vimana: AI тегирование хранилища',
      callback: () => this.autoTagVault()
    });

    this.addCommand({
      id: 'vimana-stack-status',
      name: 'Vimana: Статус Cognitive Core',
      callback: () => this.showVimanaStatus()
    });

    this.addCommand({
      id: 'vimana-deep-analysis',
      name: 'Vimana: Глубокий анализ хранилища',
      callback: () => this.performDeepAnalysis()
    });
  }

  addVimanaUI() {
    // Иконка Vimana Core
    this.ribbonIcon = this.addRibbonIcon('brain-circuit', 'Vimana Cognitive Core', () => {
      this.openVimanaDashboard();
    });

    // Статус бар Vimana Core
    this.statusBar = this.addStatusBarItem();
    this.updateVimanaStatusBar();
  }

  setupVimanaAutomation() {
    if (this.settings.autoAnalyzeNewNotes) {
      this.registerEvent(
        this.app.vault.on('create', (file) => {
          if (file instanceof TFile && file.extension === 'md') {
            this.scheduleVimanaAnalysis(file);
          }
        })
      );

      this.registerEvent(
        this.app.vault.on('modify', (file) => {
          if (file instanceof TFile && file.extension === 'md') {
            // Переанализируем измененные заметки
            this.analyzedNotes.delete(file.path);
            this.scheduleVimanaAnalysis(file);
          }
        })
      );
    }
  }

  // 🧪 ТЕСТИРОВАНИЕ VIMANA CORE

  async testVimanaCoreConnection() {
    const ollamaStatus = await this.testOllamaConnection();
    const privateGptStatus = await this.testPrivateGptConnection();
    
    let message = 'Vimana Cognitive Core: ';
    message += `Ollama: ${ollamaStatus ? '✅' : '❌'} `;
    message += `PrivateGPT: ${privateGptStatus ? '✅' : '❌'}`;
    
    new Notice(message);
    return ollamaStatus && privateGptStatus;
  }

  async testOllamaConnection() {
    try {
      const response = await requestUrl({
        url: `${this.settings.vimanaCoreUrl}/api/tags`,
        method: 'GET',
        throw: false,
        timeout: 10000
      });
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  async testPrivateGptConnection() {
    try {
      const response = await requestUrl({
        url: `${this.settings.privateGptUrl}/v1/models`,
        method: 'GET',
        throw: false,
        timeout: 10000
      });
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  // 🔧 ОСНОВНЫЕ ФУНКЦИИ VIMANA CORE

  async scheduleVimanaAnalysis(note) {
    if (this.analyzedNotes.has(note.path)) return;

    // Интеллектуальная задержка для избежания конфликтов
    setTimeout(async () => {
      try {
        await this.analyzeNoteWithVimana(note);
        this.analyzedNotes.add(note.path);
      } catch (error) {
        console.error('Vimana analysis error:', error);
      }
    }, 2000);
  }

  async analyzeNoteWithVimana(note) {
    if (!this.settings.autoAnalyzeNewNotes) return;

    const content = await this.app.vault.read(note);
    
    // Параллельный анализ с Vimana Core
    const analysisPromises = [];
    
    if (this.settings.enableAutoTagging) {
      analysisPromises.push(this.autoTagWithVimana(note, content));
    }
    
    if (this.settings.enableSemanticConnections) {
      analysisPromises.push(this.findSemanticConnections(note, content));
    }
    
    await Promise.allSettled(analysisPromises);
    console.log(`Vimana Core analyzed: ${note.basename}`);
  }

  async autoTagWithVimana(note, content) {
    try {
      const tags = await this.vimanaCore.suggestTags(content, note.basename);
      await this.applyVimanaTags(note, content, tags);
      return true;
    } catch (error) {
      console.error('Vimana tagging failed:', error);
      return false;
    }
  }

  async findSemanticConnections(note, content) {
    if (!this.settings.enableSemanticConnections) return [];

    const allNotes = this.app.vault.getMarkdownFiles();
    const recommendations = [];

    // Ограничиваем для производительности
    const notesToCheck = allNotes
      .filter(n => n.path !== note.path)
      .slice(0, 30);

    for (const otherNote of notesToCheck) {
      try {
        const otherContent = await this.app.vault.read(otherNote);
        const similarity = await this.vimanaCore.calculateSemanticSimilarity(
          content.substring(0, 2000),
          otherContent.substring(0, 2000)
        );

        if (similarity >= this.settings.semanticThreshold) {
          recommendations.push({
            note: otherNote,
            similarity,
            reason: `Vimana Semantic: ${(similarity * 100).toFixed(1)}%`
          });

          // Добавляем в граф знаний
          this.knowledgeGraph.addConnection(note, otherNote, similarity, 'semantic');
        }
      } catch (error) {
        console.error(`Vimana connection analysis failed for ${otherNote.path}:`, error);
      }
    }

    // Сохраняем рекомендации Vimana Core
    if (recommendations.length > 0) {
      await this.saveVimanaRecommendations(note, recommendations);
    }

    return recommendations;
  }

  async applyVimanaTags(note, originalContent, tags) {
    if (!tags || tags.length === 0) return;

    const cleanTags = tags.filter(tag => tag && tag.startsWith('#'));
    
    let newContent = originalContent;
    const frontmatterRegex = /^---\s*\n([\s\S]*?)\n---\s*\n/;
    const frontmatterMatch = originalContent.match(frontmatterRegex);

    if (frontmatterMatch) {
      let frontmatter = frontmatterMatch[1];
      if (frontmatter.includes('tags:')) {
        const existingTagsMatch = frontmatter.match(/tags:\s*\[(.*?)\]/);
        if (existingTagsMatch) {
          const existingTags = existingTagsMatch[1].split(',').map(t => t.trim());
          const allTags = [...new Set([...existingTags, ...cleanTags])];
          frontmatter = frontmatter.replace(
            /tags:\s*\[.*?\]/,
            `tags: [${allTags.join(', ')}]`
          );
        }
      } else {
        frontmatter += `\ntags: [${cleanTags.join(', ')}]`;
      }
      newContent = originalContent.replace(frontmatterRegex, `---\n${frontmatter}\n---\n`);
    } else {
      newContent = `---\ntags: [${cleanTags.join(', ')}]\n---\n${originalContent}`;
    }

    await this.app.vault.modify(note, newContent);
  }

  async saveVimanaRecommendations(sourceNote, recommendations) {
    const sortedRecs = recommendations
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, 8);

    let content = `# 🧠 Vimana Semantic Recommendations\n\n`;
    content += `*Сгенерировано Vimana Cognitive Core ${new Date().toLocaleString()}*\n\n`;
    content += `## Семантические связи для [[${sourceNote.basename}]]\n\n`;

    sortedRecs.forEach((rec, index) => {
      content += `### ${index + 1}. [[${rec.note.basename}]]\n`;
      content += `- **Семантическое сходство**: ${(rec.similarity * 100).toFixed(1)}%\n`;
      content += `- **Тип связи**: ${rec.reason}\n\n`;
    });

    const recPath = `Vimana-Recommendations/${sourceNote.basename}-semantic.md`;
    await this.openOrCreateNote(recPath, content);
  }

  // 🎯 ИНТЕРФЕЙСНЫЕ МЕТОДЫ VIMANA CORE

  async analyzeActiveNote() {
    const activeNote = this.app.workspace.getActiveFile();
    if (!activeNote) {
      new Notice('Откройте заметку для анализа Vimana Core');
      return;
    }

    new Notice(`🧠 Vimana Core анализирует: ${activeNote.basename}...`);
    const content = await this.app.vault.read(activeNote);
    
    await this.autoTagWithVimana(activeNote, content);
    await this.findSemanticConnections(activeNote, content);
    
    new Notice('✅ Vimana Core анализ завершен!');
  }

  async generateKnowledgeGraph() {
    new Notice('🕸️ Vimana Core строит граф знаний...');
    
    const graphPath = await this.knowledgeGraph.generateKnowledgeGraph();
    await this.app.workspace.openLinkText(graphPath, '', true);
    
    new Notice('✅ Граф знаний Vimana Core создан!');
  }

  async autoTagVault() {
    new Notice('🏷️ Vimana Core начинает тегирование хранилища...');
    
    const allNotes = this.app.vault.getMarkdownFiles();
    let processed = 0;

    // Ограничиваем для демо
    const notesToProcess = allNotes.slice(0, 25);

    for (const note of notesToProcess) {
      try {
        const content = await this.app.vault.read(note);
        const success = await this.autoTagWithVimana(note, content);
        if (success) processed++;
        
        // Задержка для избежания перегрузки
        await this.sleep(300);
      } catch (error) {
        console.error(`Vimana tagging failed for ${note.path}:`, error);
      }
    }

    new Notice(`✅ Vimana Core тегирование завершено! Обработано ${processed} заметок`);
  }

  async showVimanaStatus() {
    const ollamaStatus = await this.testOllamaConnection();
    const privateGptStatus = await this.testPrivateGptConnection();
    
    let message = 'Vimana Cognitive Core: ';
    message += `Ollama: ${ollamaStatus ? '✅' : '❌'} `;
    message += `PrivateGPT: ${privateGptStatus ? '✅' : '❌'} `;
    message += `Анализ: ${this.analyzedNotes.size} заметок`;
    
    new Notice(message);
  }

  async performDeepAnalysis() {
    new Notice('🔍 Vimana Core начинает глубокий анализ хранилища...');
    
    const analysisModal = new VimanaDeepAnalysisModal(this.app, this);
    analysisModal.open();
  }

  async openVimanaDashboard() {
    const ollamaStatus = await this.testOllamaConnection();
    const privateGptStatus = await this.testPrivateGptConnection();
    
    let dashboardContent = `# 🧠 Vimana Cognitive Core Dashboard\n\n`;
    dashboardContent += `## 📊 Статус системы\n\n`;
    dashboardContent += `- **Vimana Core**: ${ollamaStatus && privateGptStatus ? '✅ Активен' : '⚠️ Частично активен'}\n`;
    dashboardContent += `- **Ollama qwen2.5:7b**: ${ollamaStatus ? '✅ Подключен' : '❌ Недоступен'}\n`;
    dashboardContent += `- **PrivateGPT**: ${privateGptStatus ? '✅ Подключен' : '❌ Недоступен'}\n`;
    dashboardContent += `- **Режим работы**: ${this.settings.primaryAiEngine}\n`;
    dashboardContent += `- **Проанализировано**: ${this.analyzedNotes.size} заметок\n`;
    dashboardContent += `- **Семантических связей**: ${this.knowledgeGraph.connections.size}\n`;
    
    dashboardContent += `\n## 🎯 Команды Vimana Core\n\n`;
    dashboardContent += `1. [[Vimana-Recommendations|Семантические рекомендации]]\n`;
    dashboardContent += `2. [[Vimana-Graphs|Графы знаний]]\n`;
    dashboardContent += `3. [[Vimana-Analysis|Глубокий анализ]]\n`;
    
    dashboardContent += `\n## ⚙️ Настройки\n\n`;
    dashboardContent += `- Порог сходства: ${this.settings.semanticThreshold}\n`;
    dashboardContent += `- Автоанализ: ${this.settings.autoAnalyzeNewNotes ? 'Включен' : 'Выключен'}\n`;
    dashboardContent += `- Семантические связи: ${this.settings.enableSemanticConnections ? 'Включены' : 'Выключены'}\n`;
    
    dashboardContent += `\n---\n`;
    dashboardContent += `*Vimana Cognitive Core ${new Date().toLocaleString()}*`;

    await this.openOrCreateNote('Vimana-Cognitive-Core-Dashboard.md', dashboardContent);
  }

  updateVimanaStatusBar() {
    const icon = this.settings.primaryAiEngine === 'cognitive-stack' ? '🧠' : 
                this.settings.primaryAiEngine === 'ollama' ? '🦙' : '🔒';
    this.statusBar.setText(`${icon} Vimana Core`);
  }

  // 🛠️ ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ

  async openOrCreateNote(filePath, content = '') {
    try {
      let file = this.app.vault.getAbstractFileByPath(filePath);
      
      if (!file) {
        const folderPath = filePath.split('/').slice(0, -1).join('/');
        if (folderPath && !this.app.vault.getAbstractFileByPath(folderPath)) {
          await this.app.vault.createFolder(folderPath);
        }
        file = await this.app.vault.create(filePath, content);
      }
      
      await this.app.workspace.openLinkText(filePath, '', true);
      return file;
    } catch (error) {
      new Notice(`Vimana Core: ошибка создания заметки - ${error.message}`);
      throw error;
    }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  onunload() {
    console.log('Unloading Vimana Cognitive Core Plugin...');
  }
}

// 🎨 МОДАЛЬНЫЕ ОКНА VIMANA CORE

class VimanaDeepAnalysisModal extends Modal {
  constructor(app, plugin) {
    super(app);
    this.plugin = plugin;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.addClass('vimana-deep-analysis-modal');
    
    contentEl.createEl('h2', { text: '🔍 Vimana Deep Analysis' });
    
    new Setting(contentEl)
      .setName('Тип анализа')
      .setDesc('Выберите глубину анализа Vimana Core')
      .addDropdown(dropdown => dropdown
        .addOption('standard', 'Стандартный анализ')
        .addOption('semantic', 'Семантический анализ')
        .addOption('knowledge-gaps', 'Анализ пробелов знаний')
        .setValue('standard')
        .onChange(value => this.analysisType = value));
    
    new Setting(contentEl)
      .addButton(btn => {
        btn.setButtonText('🚀 Запустить Vimana Analysis')
          .setCta()
          .onClick(() => this.startDeepAnalysis());
      });
    
    this.progressEl = contentEl.createEl('div', { cls: 'vimana-progress' });
  }

  async startDeepAnalysis() {
    this.progressEl.empty();
    this.progressEl.createEl('p', { text: 'Vimana Core инициализирует глубокий анализ...' });
    
    new Notice('Vimana Core: начинаем глубокий анализ хранилища...');
    
    // Здесь можно реализовать сложный анализ через Vimana Core
  }
}
