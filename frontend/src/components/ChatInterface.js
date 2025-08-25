import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Trash2, Loader2, Paperclip, FileText, X } from 'lucide-react';
import ModelSelector from './ModelSelector';

const ChatInterface = ({ 
  messages, 
  onSendMessage, 
  onSendMessageWithFile, 
  isLoading, 
  error, 
  onClearChat, 
  selectedModel,
  models,
  onModelSelect,
  onRefreshModels,
  isAuthenticated
}) => {
  console.log('🔍 [DEBUG] ChatInterface.js: Component rendered with model:', selectedModel);

  const [inputValue, setInputValue] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileUploading, setFileUploading] = useState(false);
  const [fileUploadProgress, setFileUploadProgress] = useState(0);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Отладочные логи для отслеживания изменений состояния
  useEffect(() => {
    console.log('🔍 [DEBUG] ChatInterface.js: messages state changed:', messages.length, 'messages');
  }, [messages]);

  useEffect(() => {
    console.log('🔍 [DEBUG] ChatInterface.js: selectedModel changed to:', selectedModel);
  }, [selectedModel]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (isLoading || fileUploading) return;
    
    if (selectedFile) {
      // Отправляем сообщение с файлом
      await handleFileUpload();
    } else if (inputValue.trim()) {
      // Отправляем обычное сообщение
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    try {
      setFileUploading(true);
      setFileUploadProgress(0);
      
      // Создаем FormData для отправки файла
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('message', inputValue || 'Обработай этот файл');
      
      // Отправляем файл и сообщение
      await onSendMessageWithFile(formData, selectedFile.name);
      
      // Очищаем состояние
      setSelectedFile(null);
      setInputValue('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
    } catch (error) {
      console.error('Ошибка загрузки файла:', error);
    } finally {
      setFileUploading(false);
      setFileUploadProgress(0);
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatUsage = (usage) => {
    if (!usage) return null;
    return (
      <div className="text-xs text-gray-500 mt-2">
        Токены: {usage.prompt_tokens} + {usage.completion_tokens} = {usage.total_tokens}
      </div>
    );
  };

  // Обработка выбора файла
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Проверяем тип файла
      const allowedTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/msword',
        'application/vnd.ms-excel'
      ];
      
      if (allowedTypes.includes(file.type)) {
        // Проверяем размер файла (максимум 10MB)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
          alert('Файл слишком большой. Максимальный размер: 10MB');
          return;
        }
        
        setSelectedFile(file);
      } else {
        alert('Поддерживаются только файлы PDF, Word и Excel');
      }
    }
  };

  // Удаление выбранного файла
  const removeSelectedFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Получение иконки для типа файла
  const getFileIcon = (fileType) => {
    if (fileType.includes('pdf')) return '📄';
    if (fileType.includes('word') || fileType.includes('document')) return '📝';
    if (fileType.includes('excel') || fileType.includes('spreadsheet')) return '📊';
    return '📎';
  };

  // Форматирование размера файла
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  console.log('🔍 [DEBUG] ChatInterface.js: Rendering with state:', {
    messagesCount: messages.length,
    isLoading,
    error,
    inputMessage: inputValue.length,
    selectedModel
  });

  return (
    <div className="card h-[600px] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Чат с AI</h2>
            <div className="flex items-center space-x-2 mt-1">
              <span className="text-sm text-gray-500">Модель:</span>
              <ModelSelector
                models={models}
                selectedModel={selectedModel}
                onModelChange={onModelSelect}
                onRefresh={onRefreshModels}
                isAuthenticated={isAuthenticated}
              />
            </div>
          </div>
        </div>
        <button
          onClick={onClearChat}
          className="p-2 text-gray-400 hover:text-red-500 transition-colors"
          title="Очистить чат"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <Bot className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>Начните разговор с AI</p>
            <p className="text-sm">Задайте любой вопрос или попросите о помощи</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <div className="flex items-start space-x-2">
                  {message.role === 'assistant' && (
                    <Bot className="w-4 h-4 mt-0.5 text-gray-500 flex-shrink-0" />
                  )}
                  <div className="flex-1">
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    {formatUsage(message.usage)}
                    <p className="text-xs opacity-70 mt-1">
                      {formatTime(message.timestamp)}
                    </p>
                  </div>
                  {message.role === 'user' && (
                    <User className="w-4 h-4 mt-0.5 text-white opacity-70 flex-shrink-0" />
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
                <span className="text-gray-500">AI думает...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Error Message */}
      {error && (
        <div className="mx-4 mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200">
        {/* Выбранный файл */}
        {selectedFile && (
          <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-lg">{getFileIcon(selectedFile.type)}</span>
                <div>
                  <p className="text-sm font-medium text-blue-900">{selectedFile.name}</p>
                  <p className="text-xs text-blue-600">{formatFileSize(selectedFile.size)}</p>
                  <p className="text-xs text-blue-500 mt-1">
                    ⚠️ Большие файлы могут быть обрезаны до 10000 символов
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={removeSelectedFile}
                className="p-1 text-blue-400 hover:text-blue-600 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Прогресс загрузки файла */}
        {fileUploading && (
          <div className="mb-3">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
              <span>Загрузка файла...</span>
              <span>{fileUploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${fileUploadProgress}%` }}
              ></div>
            </div>
          </div>
        )}

        <div className="flex space-x-2">
          {/* Кнопка прикрепления файла */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading || fileUploading}
            className="p-2 text-gray-400 hover:text-blue-600 transition-colors disabled:opacity-50"
            title="Прикрепить файл"
          >
            <Paperclip className="w-5 h-5" />
          </button>
          
          {/* Скрытый input для файлов */}
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            accept=".pdf,.docx,.doc,.xlsx,.xls"
            className="hidden"
            disabled={isLoading || fileUploading}
          />

          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={selectedFile ? "Опишите, что нужно сделать с файлом..." : "Введите сообщение..."}
            className="input-field flex-1"
            disabled={isLoading || fileUploading}
          />
          <button
            type="submit"
            disabled={(!inputValue.trim() && !selectedFile) || isLoading || fileUploading}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface;
