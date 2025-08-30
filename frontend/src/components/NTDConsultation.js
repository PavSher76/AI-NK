import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Loader2, 
  HelpCircle, 
  BookOpen, 
  MessageSquare,
  FileText,
  AlertCircle,
  CheckCircle
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
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    checkSystemStatus();
    // Добавляем приветственное сообщение
    setMessages([
      {
        id: 'welcome',
        type: 'system',
        content: 'Добро пожаловать в консультацию НТД от ИИ! Я помогу вам найти ответы на вопросы по нормативным документам и стандартам. Задайте ваш вопрос, и я найду релевантную информацию в базе нормативных документов.',
        timestamp: new Date().toISOString()
      }
    ]);
  }, []);

  const checkSystemStatus = async () => {
    try {
      // Проверяем статус RAG сервиса
      const ragResponse = await fetch('/api/health', {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      // Проверяем статус Ollama
      const ollamaResponse = await fetch('/api/chat/tags', {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      // Проверяем количество документов
      const documentsResponse = await fetch('/api/documents/stats', {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      setSystemStatus({
        ragService: ragResponse.ok,
        ollama: ollamaResponse.ok,
        documents: documentsResponse.ok ? await documentsResponse.json() : null
      });
    } catch (error) {
      console.error('Ошибка проверки статуса системы:', error);
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
              <div className="whitespace-pre-wrap">{message.content}</div>
              
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
            <span className="text-xs text-gray-500">({getStatusText(systemStatus.ragService)})</span>
          </div>
          <div className="flex items-center space-x-2">
            {getStatusIcon(systemStatus.ollama)}
            <span className="text-sm text-gray-700">Ollama</span>
            <span className="text-xs text-gray-500">({getStatusText(systemStatus.ollama)})</span>
          </div>
          <div className="flex items-center space-x-2">
            {getStatusIcon(systemStatus.documents)}
            <span className="text-sm text-gray-700">
              Документы: {systemStatus.documents?.total_documents || 0}
            </span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Заголовок */}
      <div className="bg-white border-b border-gray-200 p-6">
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
      </div>

      {/* Статус системы */}
      {renderSystemStatus()}

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
