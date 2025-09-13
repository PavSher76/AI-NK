import React from 'react';
import { 
  Activity, 
  Database, 
  Cpu, 
  Shield, 
  CheckCircle,
  AlertCircle,
  Clock
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

    </div>
  );
};

export default DashboardPage;
