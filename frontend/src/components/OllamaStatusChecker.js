import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, AlertCircle, Loader2, RefreshCw } from 'lucide-react';

const OllamaStatusChecker = () => {
  const [ollamaStatus, setOllamaStatus] = useState(null);
  const [vllmStatus, setVllmStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastCheck, setLastCheck] = useState(null);

  const VLLM_OLLAMA_URL = 'http://localhost:8005';

  const checkStatus = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Проверяем статус vLLM + Ollama сервиса
      const response = await fetch(`${VLLM_OLLAMA_URL}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const statusData = await response.json();
        setOllamaStatus(statusData.services?.ollama || null);
        setVllmStatus(statusData.services?.vllm || null);
        setLastCheck(new Date().toLocaleTimeString());
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (err) {
      setError(err.message);
      setOllamaStatus(null);
      setVllmStatus(null);
    } finally {
      setLoading(false);
    }
  };

  const getModels = async () => {
    try {
      const response = await fetch(`${VLLM_OLLAMA_URL}/models`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const modelsData = await response.json();
        return modelsData;
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (err) {
      console.error('Error fetching models:', err);
      return null;
    }
  };

  useEffect(() => {
    checkStatus();
    
    // Автоматическая проверка каждые 30 секунд
    const interval = setInterval(checkStatus, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'degraded':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'unhealthy':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600';
      case 'degraded':
        return 'text-yellow-600';
      case 'unhealthy':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'healthy':
        return 'Работает';
      case 'degraded':
        return 'Частично работает';
      case 'unhealthy':
        return 'Не работает';
      default:
        return 'Неизвестно';
    }
  };

  if (loading && !ollamaStatus) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center space-x-2">
          <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
          <span className="text-gray-600">Проверка статуса Ollama...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Статус Ollama через vLLM
        </h3>
        <button
          onClick={checkStatus}
          disabled={loading}
          className="flex items-center space-x-2 px-3 py-2 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Обновить</span>
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center space-x-2">
            <XCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">Ошибка: {error}</span>
          </div>
        </div>
      )}

      {lastCheck && (
        <div className="text-sm text-gray-500 mb-4">
          Последняя проверка: {lastCheck}
        </div>
      )}

      <div className="space-y-4">
        {/* Статус Ollama */}
        <div className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium text-gray-900">Ollama</h4>
            {ollamaStatus && getStatusIcon(ollamaStatus.status)}
          </div>
          
          {ollamaStatus ? (
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <span className={`font-medium ${getStatusColor(ollamaStatus.status)}`}>
                  {getStatusText(ollamaStatus.status)}
                </span>
              </div>
              
              <div className="text-sm text-gray-600">
                <div>URL: {ollamaStatus.ollama_url}</div>
                <div>Моделей: {ollamaStatus.total_models}</div>
                <div>BGE-M3: {ollamaStatus.bge_m3_available ? '✅ Доступна' : '❌ Недоступна'}</div>
                <div>GPT-OSS: {ollamaStatus.gpt_oss_available ? '✅ Доступна' : '❌ Недоступна'}</div>
                {ollamaStatus.response_time_ms && (
                  <div>Время ответа: {ollamaStatus.response_time_ms.toFixed(1)} мс</div>
                )}
              </div>

              {ollamaStatus.available_models && ollamaStatus.available_models.length > 0 && (
                <div className="mt-2">
                  <div className="text-sm font-medium text-gray-700 mb-1">Доступные модели:</div>
                  <div className="flex flex-wrap gap-1">
                    {ollamaStatus.available_models.map((model, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                      >
                        {model}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-gray-500">Статус недоступен</div>
          )}
        </div>

        {/* Статус vLLM */}
        <div className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium text-gray-900">vLLM</h4>
            {vllmStatus && getStatusIcon(vllmStatus.status)}
          </div>
          
          {vllmStatus ? (
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <span className={`font-medium ${getStatusColor(vllmStatus.status)}`}>
                  {getStatusText(vllmStatus.status)}
                </span>
              </div>
              
              <div className="text-sm text-gray-600">
                <div>URL: {vllmStatus.url}</div>
                {vllmStatus.models && (
                  <div>Моделей: {vllmStatus.models.length}</div>
                )}
              </div>
            </div>
          ) : (
            <div className="text-gray-500">Статус недоступен</div>
          )}
        </div>

        {/* Тест чата */}
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">Тест чата</h4>
          <ChatTester vllmOllamaUrl={VLLM_OLLAMA_URL} />
        </div>
      </div>
    </div>
  );
};

// Компонент для тестирования чата
const ChatTester = ({ vllmOllamaUrl }) => {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const sendMessage = async () => {
    if (!message.trim()) return;

    setLoading(true);
    setError('');
    setResponse('');

    try {
      const response = await fetch(`${vllmOllamaUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: message,
          model: 'gpt-oss:20b',
          max_tokens: 100
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setResponse(data.response);
        } else {
          setError(data.response || 'Ошибка генерации ответа');
        }
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex space-x-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Введите сообщение для теста..."
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !message.trim()}
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Отправить'}
        </button>
      </div>

      {error && (
        <div className="p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {error}
        </div>
      )}

      {response && (
        <div className="p-3 bg-gray-50 border border-gray-200 rounded">
          <div className="text-sm font-medium text-gray-700 mb-1">Ответ:</div>
          <div className="text-sm text-gray-600">{response}</div>
        </div>
      )}
    </div>
  );
};

export default OllamaStatusChecker;
