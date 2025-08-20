import React from 'react';
import { 
  Activity, 
  Database, 
  Cpu, 
  Shield, 
  Users, 
  FileText,
  CheckCircle,
  AlertCircle,
  Clock,
  MessageSquare,
  BookOpen
} from 'lucide-react';

const DashboardPage = ({ systemStatus, models }) => {
  console.log('🔍 [DEBUG] DashboardPage.js: Component rendered with props:', {
    systemStatus,
    modelsCount: models?.length || 0
  });

  // Отладочные логи для отслеживания изменений состояния
  React.useEffect(() => {
    console.log('🔍 [DEBUG] DashboardPage.js: systemStatus changed:', systemStatus);
  }, [systemStatus]);

  React.useEffect(() => {
    console.log('🔍 [DEBUG] DashboardPage.js: models changed:', models);
  }, [models]);

  const getStatusIcon = (status) => {
    console.log('🔍 [DEBUG] DashboardPage.js: getStatusIcon called with status:', status);
    if (status === true) {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    } else if (status === false) {
      return <AlertCircle className="w-5 h-5 text-red-500" />;
    } else {
      return <Clock className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusText = (status) => {
    console.log('🔍 [DEBUG] DashboardPage.js: getStatusText called with status:', status);
    if (status === true) return 'Работает';
    if (status === false) return 'Ошибка';
    return 'Проверка...';
  };

  const getStatusColor = (status) => {
    console.log('🔍 [DEBUG] DashboardPage.js: getStatusColor called with status:', status);
    if (status === true) return 'text-green-600 bg-green-50';
    if (status === false) return 'text-red-600 bg-red-50';
    return 'text-yellow-600 bg-yellow-50';
  };

  console.log('🔍 [DEBUG] DashboardPage.js: Rendering dashboard with:', {
    systemStatus,
    modelsCount: models?.length || 0
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Дашборд системы</h1>
        <p className="mt-2 text-gray-600">Обзор состояния системы и доступных компонентов</p>
      </div>

      {/* Статус сервисов */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Database className="w-8 h-8 text-blue-600" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Gateway</h3>
              <div className="flex items-center mt-1">
                {getStatusIcon(systemStatus?.gateway)}
                <span className={`ml-2 text-sm font-medium ${getStatusColor(systemStatus?.gateway)}`}>
                  {getStatusText(systemStatus?.gateway)}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Cpu className="w-8 h-8 text-green-600" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Ollama</h3>
              <div className="flex items-center mt-1">
                {getStatusIcon(systemStatus?.ollama)}
                <span className={`ml-2 text-sm font-medium ${getStatusColor(systemStatus?.ollama)}`}>
                  {getStatusText(systemStatus?.ollama)}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Shield className="w-8 h-8 text-purple-600" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Keycloak</h3>
              <div className="flex items-center mt-1">
                {getStatusIcon(systemStatus?.keycloak)}
                <span className={`ml-2 text-sm font-medium ${getStatusColor(systemStatus?.keycloak)}`}>
                  {getStatusText(systemStatus?.keycloak)}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Activity className="w-8 h-8 text-orange-600" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Система</h3>
              <div className="flex items-center mt-1">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="ml-2 text-sm font-medium text-green-600 bg-green-50">
                  Активна
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Доступные модели */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Доступные модели</h3>
          </div>
          <div className="p-6">
            {models && models.length > 0 ? (
              <div className="space-y-3">
                {models.map((model) => (
                  <div key={model.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center">
                      <Cpu className="w-4 h-4 text-gray-600 mr-2" />
                      <span className="text-sm font-medium text-gray-900">{model.id}</span>
                    </div>
                    <span className="text-xs text-gray-500">{model.owned_by || 'Unknown'}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Cpu className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                <p className="text-gray-500">Модели не загружены</p>
              </div>
            )}
          </div>
        </div>

        {/* Быстрые действия */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Быстрые действия</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <button className="w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                <MessageSquare className="w-4 h-4 mr-2" />
                Открыть чат с ИИ
              </button>
              <button className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                <FileText className="w-4 h-4 mr-2" />
                Загрузить документ для проверки
              </button>
              <button className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                <BookOpen className="w-4 h-4 mr-2" />
                Управление нормативными документами
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
