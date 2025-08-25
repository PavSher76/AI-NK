import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Clock, 
  Activity, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle,
  FileText,
  BarChart3,
  Zap,
  Database,
  Target,
  Timer
} from 'lucide-react';

const DashboardMetrics = ({ authToken }) => {
  const [ollamaStatus, setOllamaStatus] = useState(null);
  const [ollamaPerformance, setOllamaPerformance] = useState(null);
  const [normcontrolAnalytics, setNormcontrolAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError(null);

      const headers = {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      };

      // Получаем статус Ollama
      const ollamaStatusResponse = await fetch('/api/ollama/status', { headers });
      if (ollamaStatusResponse.ok) {
        const statusData = await ollamaStatusResponse.json();
        setOllamaStatus(statusData);
      }

      // Получаем производительность Ollama
      const ollamaPerfResponse = await fetch('/api/ollama/performance', { headers });
      if (ollamaPerfResponse.ok) {
        const perfData = await ollamaPerfResponse.json();
        setOllamaPerformance(perfData);
      }

      // Получаем аналитику нормоконтроля
      const normcontrolResponse = await fetch('/api/normcontrol/analytics', { headers });
      if (normcontrolResponse.ok) {
        const analyticsData = await normcontrolResponse.json();
        setNormcontrolAnalytics(analyticsData);
      }

    } catch (err) {
      console.error('Ошибка загрузки метрик:', err);
      setError('Ошибка загрузки метрик дашбоарда');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authToken) {
      fetchMetrics();
      // Обновляем метрики каждые 30 секунд
      const interval = setInterval(fetchMetrics, 30000);
      return () => clearInterval(interval);
    }
  }, [authToken]);

  const getStatusColor = (status) => {
    if (status === 'healthy' || status === true) return 'text-green-600 bg-green-50';
    if (status === 'unhealthy' || status === false) return 'text-red-600 bg-red-50';
    return 'text-yellow-600 bg-yellow-50';
  };

  const getStatusIcon = (status) => {
    if (status === 'healthy' || status === true) return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (status === 'unhealthy' || status === false) return <AlertTriangle className="w-4 h-4 text-red-500" />;
    return <Clock className="w-4 h-4 text-yellow-500" />;
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
        <div className="flex items-center">
          <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
          <span className="text-red-700">{error}</span>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Метрики Ollama */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Статус Ollama */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Статус Ollama</h3>
            <Cpu className="w-6 h-6 text-blue-600" />
          </div>
          {ollamaStatus ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Состояние:</span>
                <div className="flex items-center">
                  {getStatusIcon(ollamaStatus.service_health)}
                  <span className={`ml-2 text-sm font-medium ${getStatusColor(ollamaStatus.service_health)}`}>
                    {ollamaStatus.service_health === 'healthy' ? 'Работает' : 'Ошибка'}
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Модели:</span>
                <span className="text-sm font-medium text-gray-900">{ollamaStatus.models_count}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Память:</span>
                <span className="text-sm font-medium text-gray-900">{ollamaStatus.memory_usage}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">CPU:</span>
                <span className="text-sm font-medium text-gray-900">{ollamaStatus.cpu_usage}</span>
              </div>
            </div>
          ) : (
            <div className="text-center py-4">
              <Clock className="w-8 h-8 mx-auto text-gray-300 mb-2" />
              <p className="text-sm text-gray-500">Данные недоступны</p>
            </div>
          )}
        </div>

        {/* Производительность Ollama */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Производительность LLM</h3>
            <TrendingUp className="w-6 h-6 text-green-600" />
          </div>
          {ollamaPerformance ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Запросы/час:</span>
                <span className="text-sm font-medium text-gray-900">{ollamaPerformance.requests_last_hour}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Время ответа:</span>
                <span className="text-sm font-medium text-gray-900">{ollamaPerformance.average_response_time}s</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Успешность:</span>
                <span className="text-sm font-medium text-green-600">{ollamaPerformance.success_rate}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Токены/сек:</span>
                <span className="text-sm font-medium text-gray-900">{ollamaPerformance.tokens_per_second}</span>
              </div>
            </div>
          ) : (
            <div className="text-center py-4">
              <Activity className="w-8 h-8 mx-auto text-gray-300 mb-2" />
              <p className="text-sm text-gray-500">Данные недоступны</p>
            </div>
          )}
        </div>

        {/* Аналитика нормоконтроля */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Нормоконтроль</h3>
            <FileText className="w-6 h-6 text-purple-600" />
          </div>
          {normcontrolAnalytics ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Документы:</span>
                <span className="text-sm font-medium text-gray-900">{normcontrolAnalytics.total_documents}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Соответствие:</span>
                <span className="text-sm font-medium text-green-600">{normcontrolAnalytics.compliance_rate}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Находки:</span>
                <span className="text-sm font-medium text-gray-900">{normcontrolAnalytics.average_findings}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Время обработки:</span>
                <span className="text-sm font-medium text-gray-900">{normcontrolAnalytics.performance?.average_processing_time} мин</span>
              </div>
            </div>
          ) : (
            <div className="text-center py-4">
              <BarChart3 className="w-8 h-8 mx-auto text-gray-300 mb-2" />
              <p className="text-sm text-gray-500">Данные недоступны</p>
            </div>
          )}
        </div>
      </div>

      {/* Детальная статистика */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Детализация находок нормоконтроля */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Детализация находок</h3>
            <Target className="w-6 h-6 text-red-600" />
          </div>
          {normcontrolAnalytics?.results ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <div className="flex items-center">
                  <AlertTriangle className="w-4 h-4 text-red-500 mr-2" />
                  <span className="text-sm font-medium text-red-700">Критические</span>
                </div>
                <span className="text-lg font-bold text-red-700">{normcontrolAnalytics.results.critical_findings}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                <div className="flex items-center">
                  <AlertTriangle className="w-4 h-4 text-yellow-500 mr-2" />
                  <span className="text-sm font-medium text-yellow-700">Предупреждения</span>
                </div>
                <span className="text-lg font-bold text-yellow-700">{normcontrolAnalytics.results.warning_findings}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center">
                  <CheckCircle className="w-4 h-4 text-blue-500 mr-2" />
                  <span className="text-sm font-medium text-blue-700">Информационные</span>
                </div>
                <span className="text-lg font-bold text-blue-700">{normcontrolAnalytics.results.info_findings}</span>
              </div>
            </div>
          ) : (
            <div className="text-center py-4">
              <Target className="w-8 h-8 mx-auto text-gray-300 mb-2" />
              <p className="text-sm text-gray-500">Данные недоступны</p>
            </div>
          )}
        </div>

        {/* Статус обработки документов */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Статус обработки</h3>
            <Timer className="w-6 h-6 text-blue-600" />
          </div>
          {normcontrolAnalytics?.overview ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <Clock className="w-4 h-4 text-gray-500 mr-2" />
                  <span className="text-sm font-medium text-gray-700">Ожидают</span>
                </div>
                <span className="text-lg font-bold text-gray-700">{normcontrolAnalytics.overview.pending_reviews}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div className="flex items-center">
                  <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                  <span className="text-sm font-medium text-green-700">Завершены</span>
                </div>
                <span className="text-lg font-bold text-green-700">{normcontrolAnalytics.overview.completed_reviews}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center">
                  <Activity className="w-4 h-4 text-blue-500 mr-2" />
                  <span className="text-sm font-medium text-blue-700">В обработке</span>
                </div>
                <span className="text-lg font-bold text-blue-700">{normcontrolAnalytics.overview.in_progress_reviews}</span>
              </div>
            </div>
          ) : (
            <div className="text-center py-4">
              <Timer className="w-8 h-8 mx-auto text-gray-300 mb-2" />
              <p className="text-sm text-gray-500">Данные недоступны</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default DashboardMetrics;
