import React from 'react';
import OllamaStatusChecker from '../components/OllamaStatusChecker';

const OllamaMonitor = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Мониторинг Ollama
          </h1>
          <p className="text-gray-600">
            Проверка статуса локально установленного Ollama через vLLM сервис
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Основной статус */}
          <div className="lg:col-span-2">
            <OllamaStatusChecker />
          </div>

          {/* Дополнительная информация */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Информация о сервисе
            </h3>
            <div className="space-y-3 text-sm text-gray-600">
              <div>
                <span className="font-medium">VLLM + Ollama Service:</span>
                <br />
                <span className="text-blue-600">http://localhost:8005</span>
              </div>
              <div>
                <span className="font-medium">Ollama API:</span>
                <br />
                <span className="text-blue-600">http://localhost:11434</span>
              </div>
              <div>
                <span className="font-medium">Автоматическая проверка:</span>
                <br />
                Каждые 30 секунд
              </div>
            </div>
          </div>

          {/* Инструкции */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Инструкции
            </h3>
            <div className="space-y-3 text-sm text-gray-600">
              <div>
                <span className="font-medium">1. Запуск Ollama:</span>
                <br />
                <code className="bg-gray-100 px-2 py-1 rounded">ollama serve</code>
              </div>
              <div>
                <span className="font-medium">2. Запуск vLLM сервиса:</span>
                <br />
                <code className="bg-gray-100 px-2 py-1 rounded">./scripts/start_vllm_ollama.sh</code>
              </div>
              <div>
                <span className="font-medium">3. Проверка моделей:</span>
                <br />
                <code className="bg-gray-100 px-2 py-1 rounded">ollama list</code>
              </div>
            </div>
          </div>
        </div>

        {/* Статус системы */}
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Статус системы
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <SystemStatusCard
              title="Ollama"
              url="http://localhost:11434/api/tags"
              description="Локальный сервис Ollama"
            />
            <SystemStatusCard
              title="VLLM + Ollama"
              url="http://localhost:8001/health"
              description="Интеграционный сервис"
            />
            <SystemStatusCard
              title="RAG Service"
              url="http://localhost:8003/health"
              description="RAG сервис с Ollama"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// Компонент для отображения статуса системы
const SystemStatusCard = ({ title, url, description }) => {
  const [status, setStatus] = React.useState('unknown');
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await fetch(url, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });
        setStatus(response.ok ? 'healthy' : 'unhealthy');
      } catch {
        setStatus('unhealthy');
      } finally {
        setLoading(false);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, [url]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'unhealthy':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'healthy':
        return 'Работает';
      case 'unhealthy':
        return 'Не работает';
      default:
        return 'Проверка...';
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-medium text-gray-900">{title}</h4>
        {loading ? (
          <div className="w-3 h-3 bg-gray-400 rounded-full animate-pulse" />
        ) : (
          <div className={`w-3 h-3 rounded-full ${
            status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
          }`} />
        )}
      </div>
      
      <p className="text-sm text-gray-600 mb-3">{description}</p>
      
      <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
        {getStatusText(status)}
      </div>
    </div>
  );
};

export default OllamaMonitor;
