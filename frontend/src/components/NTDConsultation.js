import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Loader2, 
  HelpCircle, 
  BookOpen, 
  MessageSquare,
  FileText,
  AlertCircle,
  CheckCircle,
  Search,
  Zap,
  Brain,
  BarChart3,
  X
} from 'lucide-react';

const NTDConsultation = ({ isAuthenticated, authToken }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState({
    ragService: null,
    ollama: null,
    documents: null
  });
  const [hybridSearchStats, setHybridSearchStats] = useState(null);
  const [showSearchStats, setShowSearchStats] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    checkSystemStatus();
    loadHybridSearchStats();
    // Добавляем приветственное сообщение
    setMessages([
      {
        id: 'welcome',
        type: 'system',
        content: 'Добро пожаловать в консультацию НТД от ИИ! Я помогу вам найти ответы на вопросы по нормативным документам и стандартам. Задайте ваш вопрос, и я найду релевантную информацию в базе нормативных документов.',
        timestamp: new Date().toISOString()
      }
    ]);

    // Автоматическая проверка статуса каждые 30 секунд
    const statusInterval = setInterval(() => {
      checkSystemStatus();
    }, 30000);

    // Очистка интервала при размонтировании компонента
    return () => clearInterval(statusInterval);
  }, []);

  const loadHybridSearchStats = async () => {
    try {
      const response = await fetch('/rag/hybrid_search_stats');
      if (response.ok) {
        const data = await response.json();
        setHybridSearchStats(data);
      }
    } catch (error) {
      console.error('Ошибка загрузки статистики гибридного поиска:', error);
    }
  };

  const checkSystemStatus = async () => {
    try {
      // Проверяем статус RAG сервиса
      const ragResponse = await fetch('/rag/health');
      
      // Проверяем статус Ollama через RAG сервис
      const ollamaResponse = await fetch('/rag/models');

      // Проверяем количество документов
      const documentsResponse = await fetch('/rag/documents/stats');

      setSystemStatus({
        ragService: ragResponse.ok,
        ollama: ollamaResponse.ok,
        documents: documentsResponse.ok ? await documentsResponse.json() : null
      });
    } catch (error) {
      console.error('Ошибка проверки статуса системы:', error);
      // Устанавливаем статус ошибки для всех сервисов
      setSystemStatus({
        ragService: false,
        ollama: false,
        documents: null
      });
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/ntd-consultation/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          message: inputMessage,
          user_id: 'default_user', // Добавляем user_id
          history: messages.filter(m => m.type !== 'system').map(m => ({
            role: m.type === 'user' ? 'user' : 'assistant',
            content: m.content
          }))
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.response,
        sources: data.sources || [],
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Ошибка отправки сообщения:', error);
      
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        type: 'error',
        content: 'Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте еще раз.',
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getIntentTypeLabel = (intentType) => {
    const labels = {
      'definition': 'Определения',
      'applicability': 'Область применения',
      'requirements': 'Требования',
      'procedure': 'Процедуры',
      'exceptions': 'Исключения',
      'general': 'Общие вопросы'
    };
    return labels[intentType] || intentType;
  };

  const formatMessageContent = (content) => {
    if (!content) return '';
    
    // Простое форматирование Markdown-подобного текста
    return content
      .split('\n')
      .map((line, index) => {
        // Заголовки
        if (line.startsWith('## ')) {
          return (
            <h2 key={index} className="text-lg font-semibold text-gray-800 mt-4 mb-2">
              {line.replace('## ', '')}
            </h2>
          );
        }
        
        // Подзаголовки
        if (line.startsWith('### ')) {
          return (
            <h3 key={index} className="text-md font-medium text-gray-700 mt-3 mb-1">
              {line.replace('### ', '')}
            </h3>
          );
        }
        
        // Жирный текст
        if (line.startsWith('**') && line.endsWith('**')) {
          return (
            <p key={index} className="font-semibold text-gray-800 mb-2">
              {line.replace(/\*\*/g, '')}
            </p>
          );
        }
        
        // Курсив
        if (line.startsWith('*') && line.endsWith('*') && !line.startsWith('**')) {
          return (
            <p key={index} className="italic text-gray-600 mb-2">
              {line.replace(/\*/g, '')}
            </p>
          );
        }
        
        // Разделитель
        if (line.startsWith('---')) {
          return <hr key={index} className="my-4 border-gray-300" />;
        }
        
        // Обычный текст
        if (line.trim()) {
          return (
            <p key={index} className="mb-2 text-gray-700 leading-relaxed">
              {line}
            </p>
          );
        }
        
        // Пустые строки
        return <br key={index} />;
      });
  };

  const renderMessage = (message) => {
    const isUser = message.type === 'user';
    const isSystem = message.type === 'system';
    const isError = message.type === 'error';

    return (
      <div
        key={message.id}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div
          className={`max-w-3xl px-4 py-3 rounded-lg ${
            isUser
              ? 'bg-blue-600 text-white'
              : isSystem
              ? 'bg-gray-100 text-gray-800'
              : isError
              ? 'bg-red-100 text-red-800'
              : 'bg-white text-gray-800 border border-gray-200'
          }`}
        >
          <div className="flex items-start space-x-2">
            {!isUser && (
              <div className="flex-shrink-0 mt-1">
                {isSystem ? (
                  <HelpCircle className="w-4 h-4 text-gray-500" />
                ) : isError ? (
                  <AlertCircle className="w-4 h-4 text-red-500" />
                ) : (
                  <MessageSquare className="w-4 h-4 text-blue-500" />
                )}
              </div>
            )}
            <div className="flex-1">
              <div className="whitespace-pre-wrap prose prose-sm max-w-none">
                {formatMessageContent(message.content)}
              </div>
              
              {/* Отображение информации о намерении для пользовательских сообщений */}
              {isUser && message.intent_type && (
                <div className="mt-2 pt-2 border-t border-blue-400/30">
                  <div className="flex items-center space-x-2 text-xs text-blue-100">
                    <span className="font-medium">Намерение:</span>
                    <span className="px-2 py-1 bg-blue-400/20 rounded-full">
                      {getIntentTypeLabel(message.intent_type)}
                    </span>
                    <span className="text-blue-200">
                      ({Math.round(message.intent_confidence * 100)}%)
                    </span>
                  </div>
                  {message.intent_keywords && message.intent_keywords.length > 0 && (
                    <div className="mt-1 text-xs text-blue-200">
                      <span className="font-medium">Ключевые слова:</span> {message.intent_keywords.join(', ')}
                    </div>
                  )}
                </div>
              )}
              
              {message.sources && message.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="text-sm font-medium text-gray-600 mb-2">
                    Источники:
                  </div>
                  <div className="space-y-1">
                    {message.sources.map((source, index) => (
                      <div key={index} className="flex items-center space-x-2 text-sm text-gray-500">
                        <FileText className="w-3 h-3" />
                        <span>{source.title || source.filename}</span>
                        {source.page && (
                          <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                            стр. {source.page}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="text-xs text-gray-400 mt-2">
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderSystemStatus = () => {
    const getStatusIcon = (status) => {
      if (status === true) return <CheckCircle className="w-4 h-4 text-green-500" />;
      if (status === false) return <AlertCircle className="w-4 h-4 text-red-500" />;
      return <Loader2 className="w-4 h-4 text-yellow-500 animate-spin" />;
    };

    const getStatusText = (status) => {
      if (status === true) return 'Работает';
      if (status === false) return 'Ошибка';
      return 'Проверка...';
    };

    const getStatusColor = (status) => {
      if (status === true) return 'text-green-600';
      if (status === false) return 'text-red-600';
      return 'text-yellow-600';
    };

    return (
      <div className="bg-white p-4 rounded-lg border border-gray-200 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
          <BookOpen className="w-5 h-5 mr-2 text-blue-600" />
          Статус системы
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-2">
            {getStatusIcon(systemStatus.ragService)}
            <span className="text-sm text-gray-700">RAG сервис</span>
            <span className={`text-xs font-medium ${getStatusColor(systemStatus.ragService)}`}>
              ({getStatusText(systemStatus.ragService)})
            </span>
          </div>
          <div className="flex items-center space-x-2">
            {getStatusIcon(systemStatus.ollama)}
            <span className="text-sm text-gray-700">Ollama</span>
            <span className={`text-xs font-medium ${getStatusColor(systemStatus.ollama)}`}>
              ({getStatusText(systemStatus.ollama)})
            </span>
          </div>
          <div className="flex items-center space-x-2">
            {getStatusIcon(systemStatus.documents)}
            <span className="text-sm text-gray-700">
              Документы: {systemStatus.documents?.documents || 0}
            </span>
            <span className="text-xs text-gray-500">
              ({systemStatus.documents?.chunks || 0} чанков)
            </span>
          </div>
        </div>
      </div>
    );
  };

  const renderHybridSearchStats = () => {
    if (!hybridSearchStats || !showSearchStats) return null;

    const stats = hybridSearchStats.stats;
    const bgeReranker = hybridSearchStats.bge_reranker;
    const mmr = hybridSearchStats.mmr;
    const intentClassifier = hybridSearchStats.intent_classifier;
    
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6 shadow-soft">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Статистика гибридного поиска</h3>
              <p className="text-sm text-gray-500">BM25 + Dense поиск с Alpha смешиванием и RRF</p>
            </div>
          </div>
          <button
            onClick={() => setShowSearchStats(false)}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-all duration-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
          {/* BM25 статистика */}
          <div className="bg-gradient-to-r from-warning-50 to-warning-100 rounded-xl p-4 border border-warning-200">
            <div className="flex items-center space-x-3 mb-2">
              <Search className="w-5 h-5 text-warning-600" />
              <h4 className="font-semibold text-warning-900">BM25 Поиск</h4>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-warning-700">
                <span className="font-medium">Обучен:</span> {stats.bm25_trained ? 'Да' : 'Нет'}
              </p>
              <p className="text-sm text-warning-700">
                <span className="font-medium">Размер корпуса:</span> {stats.corpus_size.toLocaleString()}
              </p>
              <p className="text-sm text-warning-700">
                <span className="font-medium">Средняя длина:</span> {stats.avg_doc_length?.toFixed(1) || 'N/A'}
              </p>
            </div>
          </div>

          {/* Dense поиск */}
          <div className="bg-gradient-to-r from-primary-50 to-primary-100 rounded-xl p-4 border border-primary-200">
            <div className="flex items-center space-x-3 mb-2">
              <Brain className="w-5 h-5 text-primary-600" />
              <h4 className="font-semibold text-primary-900">Dense Поиск</h4>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-primary-700">
                <span className="font-medium">Модель:</span> BGE-M3
              </p>
              <p className="text-sm text-primary-700">
                <span className="font-medium">Размер вектора:</span> 1024
              </p>
              <p className="text-sm text-primary-700">
                <span className="font-medium">Коллекция:</span> normative_documents
              </p>
            </div>
          </div>

          {/* BGE Реранкер */}
          <div className="bg-gradient-to-r from-success-50 to-success-100 rounded-xl p-4 border border-success-200">
            <div className="flex items-center space-x-3 mb-2">
              <Zap className="w-5 h-5 text-success-600" />
              <h4 className="font-semibold text-success-900">BGE Реранкер</h4>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-success-700">
                <span className="font-medium">Модель:</span> {bgeReranker?.model_name || 'bge-ranking-base'}
              </p>
              <p className="text-sm text-success-700">
                <span className="font-medium">Статус:</span> {bgeReranker?.health_status ? 'Доступен' : 'Недоступен'}
              </p>
              <p className="text-sm text-success-700">
                <span className="font-medium">Батч:</span> {bgeReranker?.max_batch_size || 10}
              </p>
            </div>
          </div>

          {/* MMR Диверсификация */}
          <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-xl p-4 border border-purple-200">
            <div className="flex items-center space-x-3 mb-2">
              <Brain className="w-5 h-5 text-purple-600" />
              <h4 className="font-semibold text-purple-900">MMR Диверсификация</h4>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-purple-700">
                <span className="font-medium">Lambda:</span> {mmr?.lambda_param || 0.7}
              </p>
              <p className="text-sm text-purple-700">
                <span className="font-medium">Порог:</span> {mmr?.similarity_threshold || 0.8}
              </p>
              <p className="text-sm text-purple-700">
                <span className="font-medium">Статус:</span> Включен
              </p>
            </div>
          </div>

          {/* Классификатор намерений */}
          <div className="bg-gradient-to-r from-indigo-50 to-indigo-100 rounded-xl p-4 border border-indigo-200">
            <div className="flex items-center space-x-3 mb-2">
              <Zap className="w-5 h-5 text-indigo-600" />
              <h4 className="font-semibold text-indigo-900">Классификация намерений</h4>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-indigo-700">
                <span className="font-medium">Типы:</span> {intentClassifier?.intent_types?.length || 6}
              </p>
              <p className="text-sm text-indigo-700">
                <span className="font-medium">Ключевые слова:</span> {intentClassifier?.keywords_count?.definition || 0}
              </p>
              <p className="text-sm text-indigo-700">
                <span className="font-medium">Статус:</span> Включен
              </p>
            </div>
          </div>

          {/* Параметры смешивания */}
          <div className="bg-gradient-to-r from-accent-50 to-accent-100 rounded-xl p-4 border border-accent-200">
            <div className="flex items-center space-x-3 mb-2">
              <BarChart3 className="w-5 h-5 text-accent-600" />
              <h4 className="font-semibold text-accent-900">Параметры</h4>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-accent-700">
                <span className="font-medium">Alpha:</span> {stats.alpha}
              </p>
              <p className="text-sm text-accent-700">
                <span className="font-medium">RRF:</span> {stats.use_rrf ? 'Включен' : 'Отключен'}
              </p>
              <p className="text-sm text-accent-700">
                <span className="font-medium">Топ-50→8:</span> Включен
              </p>
            </div>
          </div>
        </div>

        <div className="mt-4 p-4 bg-gray-50 rounded-xl">
          <h4 className="font-semibold text-gray-900 mb-2">Как работает гибридный поиск:</h4>
          <div className="text-sm text-gray-600 space-y-1">
            <p>• <strong>Классификация намерений</strong> - определение типа запроса (определения, требования, процедуры)</p>
            <p>• <strong>Переписывание запроса</strong> - генерация специфичных подзапросов для нужных разделов</p>
            <p>• <strong>BM25</strong> - точное совпадение ключевых слов и терминов</p>
            <p>• <strong>Dense</strong> - семантическое понимание смысла запроса</p>
            <p>• <strong>Alpha смешивание</strong> - комбинирование результатов с весами</p>
            <p>• <strong>RRF</strong> - объединение рангов для лучшего качества</p>
            <p>• <strong>BGE Реранкер</strong> - финальная сортировка топ-50 в топ-8</p>
            <p>• <strong>MMR Диверсификация</strong> - обеспечение разнообразия результатов</p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Заголовок */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-blue-600 rounded-lg">
              <HelpCircle className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Консультация НТД от ИИ</h1>
              <p className="text-sm text-gray-500">
                Получите консультацию по нормативным документам и стандартам
              </p>
            </div>
          </div>
          
          {/* Кнопка статистики гибридного поиска */}
          <button
            onClick={() => setShowSearchStats(!showSearchStats)}
            className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-xl hover:from-primary-600 hover:to-primary-700 transition-all duration-300 shadow-soft hover:shadow-glow"
          >
            <BarChart3 className="w-4 h-4" />
            <span className="text-sm font-medium">
              {showSearchStats ? 'Скрыть статистику' : 'Статистика поиска'}
            </span>
          </button>
        </div>
      </div>

      {/* Статус системы */}
      {renderSystemStatus()}

      {/* Статистика гибридного поиска */}
      {renderHybridSearchStats()}

      {/* Чат */}
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-4">
        {/* Сообщения */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map(renderMessage)}
          {isLoading && (
            <div className="flex justify-start mb-4">
              <div className="bg-white text-gray-800 border border-gray-200 max-w-3xl px-4 py-3 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                  <span className="text-sm text-gray-600">ИИ обрабатывает ваш запрос...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Поле ввода */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex space-x-4">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Задайте вопрос по нормативным документам..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows="3"
                disabled={isLoading || !isAuthenticated}
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading || !isAuthenticated}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              <span>Отправить</span>
            </button>
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Нажмите Enter для отправки, Shift+Enter для новой строки
          </div>
        </div>
      </div>
    </div>
  );
};

export default NTDConsultation;
