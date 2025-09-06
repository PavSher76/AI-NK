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
import DashboardMetrics from '../components/DashboardMetrics';

const DashboardPage = ({ systemStatus, models, isAuthenticated, userInfo, authMethod, onPageChange }) => {
  console.log('🔍 [DEBUG] DashboardPage.js: Component rendered with props:', {
    systemStatus,
    modelsCount: models?.length || 0,
    isAuthenticated,
    authMethod,
    userInfo: !!userInfo
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
    modelsCount: models?.length || 0,
    isAuthenticated,
    authMethod
  });

  return (
    <div className="max-w-7xl mx-auto animate-fade-in">
      {/* Заголовок страницы */}
      <div className="mb-8">
        <div className="flex items-center space-x-4 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl flex items-center justify-center shadow-soft">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Дашборд</h1>
            <p className="text-gray-600 mt-1">Обзор состояния системы и доступных компонентов</p>
          </div>
        </div>
      </div>

      {/* Статус сервисов */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card-elevated group">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-soft group-hover:shadow-glow transition-all duration-300">
              <Database className="w-6 h-6 text-white" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">Gateway</h3>
              <div className="flex items-center mt-2">
                {getStatusIcon(systemStatus?.gateway)}
                <span className={`ml-2 text-sm font-medium px-3 py-1 rounded-lg ${
                  systemStatus?.gateway ? 'status-success' : 'status-error'
                }`}>
                  {getStatusText(systemStatus?.gateway)}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="card-elevated group">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-gradient-to-br from-success-500 to-success-600 rounded-xl flex items-center justify-center shadow-soft group-hover:shadow-glow transition-all duration-300">
              <Cpu className="w-6 h-6 text-white" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">Ollama</h3>
              <div className="flex items-center mt-2">
                {getStatusIcon(systemStatus?.ollama)}
                <span className={`ml-2 text-sm font-medium px-3 py-1 rounded-lg ${
                  systemStatus?.ollama ? 'status-success' : 'status-error'
                }`}>
                  {getStatusText(systemStatus?.ollama)}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="card-elevated group">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-gradient-to-br from-accent-500 to-accent-600 rounded-xl flex items-center justify-center shadow-soft group-hover:shadow-glow transition-all duration-300">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">Keycloak</h3>
              <div className="flex items-center mt-2">
                {getStatusIcon(systemStatus?.keycloak)}
                <span className={`ml-2 text-sm font-medium px-3 py-1 rounded-lg ${
                  systemStatus?.keycloak ? 'status-success' : 'status-error'
                }`}>
                  {getStatusText(systemStatus?.keycloak)}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="card-elevated group">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-gradient-to-br from-warning-500 to-warning-600 rounded-xl flex items-center justify-center shadow-soft group-hover:shadow-glow transition-all duration-300">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">Система</h3>
              <div className="flex items-center mt-2">
                <CheckCircle className="w-5 h-5 text-success-500" />
                <span className="ml-2 text-sm font-medium px-3 py-1 rounded-lg status-success">
                  Активна
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Метрики Ollama и нормоконтроля */}
      <DashboardMetrics authToken={localStorage.getItem('authToken')} />

      {/* Статистика */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Доступные модели */}
        <div className="card-elevated">
          <div className="px-6 py-5 border-b border-gray-100">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center">
                <Cpu className="w-4 h-4 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Доступные модели</h3>
            </div>
          </div>
          <div className="p-6">
            {models && models.length > 0 ? (
              <div className="space-y-3">
                {models.map((model, index) => (
                  <div key={model.id} className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border border-gray-200 hover:shadow-soft transition-all duration-300 animate-slide-up" style={{animationDelay: `${index * 100}ms`}}>
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center">
                        <Cpu className="w-4 h-4 text-white" />
                      </div>
                      <span className="text-sm font-semibold text-gray-900">{model.id}</span>
                    </div>
                    <span className="text-xs font-medium text-gray-500 bg-white px-2 py-1 rounded-lg border border-gray-200">
                      {model.owned_by || 'Unknown'}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-gradient-to-br from-gray-200 to-gray-300 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Cpu className="w-8 h-8 text-gray-400" />
                </div>
                <p className="text-gray-500 font-medium">Модели не загружены</p>
                <p className="text-sm text-gray-400 mt-1">Проверьте подключение к сервису</p>
              </div>
            )}
          </div>
        </div>

        {/* Быстрые действия */}
        <div className="card-elevated">
          <div className="px-6 py-5 border-b border-gray-100">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-accent-500 to-accent-600 rounded-lg flex items-center justify-center">
                <Activity className="w-4 h-4 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Быстрые действия</h3>
            </div>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <button 
                onClick={() => onPageChange && onPageChange('chat')}
                className="w-full btn-primary flex items-center justify-center space-x-2"
              >
                <MessageSquare className="w-4 h-4" />
                <span>Открыть чат с ИИ</span>
              </button>
              <button 
                onClick={() => onPageChange && onPageChange('normcontrol')}
                className="w-full btn-secondary flex items-center justify-center space-x-2"
              >
                <FileText className="w-4 h-4" />
                <span>Загрузить документ для проверки</span>
              </button>
              <button 
                onClick={() => onPageChange && onPageChange('documents')}
                className="w-full btn-secondary flex items-center justify-center space-x-2"
              >
                <BookOpen className="w-4 h-4" />
                <span>Управление нормативными документами</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
