import React from 'react';
import { 
  Home, 
  MessageSquare, 
  FileText, 
  BookOpen, 
  User, 
  Settings,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  LogOut
} from 'lucide-react';

const Navigation = ({ 
  currentPage, 
  onPageChange, 
  systemStatus, 
  models, 
  isAuthenticated, 
  userInfo, 
  authMethod, 
  onLogout 
}) => {
  console.log('🔍 [DEBUG] Navigation.js: Rendering with props:', {
    currentPage,
    systemStatus,
    modelsCount: models?.length || 0
  });

  const handlePageClick = (page) => {
    console.log('🔍 [DEBUG] Navigation.js: handlePageClick called with page:', page);
    onPageChange(page);
  };

  const getStatusIcon = (status) => {
    console.log('🔍 [DEBUG] Navigation.js: getStatusIcon called with status:', status);
    if (status === true) {
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    } else if (status === false) {
      return <AlertCircle className="w-4 h-4 text-red-500" />;
    } else {
      return <RefreshCw className="w-4 h-4 text-yellow-500 animate-spin" />;
    }
  };

  const getStatusText = (status) => {
    console.log('🔍 [DEBUG] Navigation.js: getStatusText called with status:', status);
    if (status === true) return 'Работает';
    if (status === false) return 'Ошибка';
    return 'Проверка...';
  };

  console.log('🔍 [DEBUG] Navigation.js: System status details:', {
    gateway: systemStatus?.gateway,
    ollama: systemStatus?.ollama,
    keycloak: systemStatus?.keycloak
  });

  return (
    <nav className="bg-white shadow-lg border-b">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16">
          {/* Логотип и название */}
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center">
              <BookOpen className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">AI-НК</span>
            </div>
          </div>

          {/* Навигационные ссылки */}
          <div className="flex items-center space-x-8">
            <button
              onClick={() => handlePageClick('dashboard')}
              className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                currentPage === 'dashboard'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <Home className="w-4 h-4 mr-2" />
              Дашборд
            </button>

            <button
              onClick={() => handlePageClick('chat')}
              className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                currentPage === 'chat'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <MessageSquare className="w-4 h-4 mr-2" />
              Чат с ИИ
            </button>

            <button
              onClick={() => handlePageClick('normcontrol')}
              className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                currentPage === 'normcontrol'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <FileText className="w-4 h-4 mr-2" />
              Нормоконтроль
            </button>

            <button
              onClick={() => handlePageClick('documents')}
              className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                currentPage === 'documents'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <BookOpen className="w-4 h-4 mr-2" />
              Нормативные Документы
            </button>
          </div>

          {/* Статус системы и пользователь */}
          <div className="flex items-center space-x-4">
            {/* Статус сервисов */}
            <div className="flex items-center space-x-2 text-sm">
              <span className="text-gray-600">Статус:</span>
              <div className="flex items-center space-x-1">
                {getStatusIcon(systemStatus?.gateway)}
                <span className="text-xs">{getStatusText(systemStatus?.gateway)}</span>
              </div>
            </div>

            {/* Информация о пользователе */}
            <div className="flex items-center space-x-2">
              <User className="w-4 h-4 text-gray-600" />
              <span className="text-sm text-gray-700">
                {userInfo?.username || 'Тестовый пользователь'}
                {authMethod && (
                  <span className="ml-1 text-xs text-gray-500">({authMethod})</span>
                )}
              </span>
            </div>

            {/* Кнопка выхода */}
            {isAuthenticated && (
              <button
                onClick={onLogout}
                className="flex items-center px-3 py-2 rounded-md text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 transition-colors"
                title="Выйти из системы"
              >
                <LogOut className="w-4 h-4 mr-1" />
                Выйти
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
