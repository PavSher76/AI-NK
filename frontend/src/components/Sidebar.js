import React from 'react';
import { 
  Home, 
  MessageSquare, 
  FileText, 
  BookOpen, 
  Calculator,
  User, 
  LogOut,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  X,
  HelpCircle
} from 'lucide-react';

const Sidebar = ({ 
  currentPage, 
  onPageChange, 
  systemStatus, 
  isAuthenticated, 
  userInfo, 
  authMethod, 
  onLogout,
  onClose 
}) => {
  const handlePageClick = (page) => {
    console.log('🔍 [DEBUG] Sidebar.js: handlePageClick called with page:', page);
    onPageChange(page);
  };

  const getStatusIcon = (status) => {
    if (status === true) {
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    } else if (status === false) {
      return <AlertCircle className="w-4 h-4 text-red-500" />;
    } else {
      return <RefreshCw className="w-4 h-4 text-yellow-500 animate-spin" />;
    }
  };

  const getStatusText = (status) => {
    if (status === true) return 'Работает';
    if (status === false) return 'Ошибка';
    return 'Проверка...';
  };

  const navigationItems = [
    {
      id: 'dashboard',
      label: 'Дашборд',
      icon: Home,
      onClick: () => handlePageClick('dashboard')
    },
    {
      id: 'chat',
      label: 'Чат с ИИ',
      icon: MessageSquare,
      onClick: () => handlePageClick('chat')
    },
    {
      id: 'ntd-consultation',
      label: 'Консультация НТД от ИИ',
      icon: HelpCircle,
      onClick: () => handlePageClick('ntd-consultation')
    },
    {
      id: 'calculations',
      label: 'Расчеты',
      icon: Calculator,
      onClick: () => handlePageClick('calculations')
    },
    {
      id: 'normcontrol',
      label: 'Нормоконтроль',
      icon: FileText,
      onClick: () => handlePageClick('normcontrol')
    },
    {
      id: 'documents',
      label: 'Нормативные документы',
      icon: BookOpen,
      onClick: () => handlePageClick('documents')
    }
  ];

  const renderNavigationItem = (item) => {
    const Icon = item.icon;
    const isActive = currentPage === item.id;

    return (
      <button
        key={item.id}
        onClick={item.onClick}
        className={`w-full flex items-center px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
          isActive
            ? 'bg-blue-100 text-blue-700'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
        }`}
      >
        <Icon className="w-5 h-5 mr-3" />
        {item.label}
      </button>
    );
  };

  return (
    <div className="w-64 bg-white shadow-lg h-screen flex flex-col">
      {/* Логотип и название */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div 
            className="flex items-center cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => handlePageClick('dashboard')}
          >
            <BookOpen className="h-8 w-8 text-blue-600" />
            <span className="ml-2 text-xl font-bold text-gray-900">AI-НК</span>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="lg:hidden p-1 rounded-lg hover:bg-gray-100 transition-colors"
              title="Закрыть меню"
            >
              <X className="w-5 h-5 text-gray-600" />
            </button>
          )}
        </div>
      </div>

      {/* Навигационные ссылки */}
      <div className="flex-1 p-4 overflow-y-auto">
        <nav className="space-y-2">
          {navigationItems.map(renderNavigationItem)}
        </nav>
      </div>

      {/* Нижняя часть с информацией о пользователе и выходом */}
      <div className="p-4 border-t border-gray-200 space-y-4">
        {/* Статус системы */}
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs font-medium text-gray-700 mb-2">Статус системы</div>
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-600">Gateway:</span>
              <div className="flex items-center space-x-1">
                {getStatusIcon(systemStatus?.gateway)}
                <span>{getStatusText(systemStatus?.gateway)}</span>
              </div>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-600">Ollama:</span>
              <div className="flex items-center space-x-1">
                {getStatusIcon(systemStatus?.ollama)}
                <span>{getStatusText(systemStatus?.ollama)}</span>
              </div>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-600">Keycloak:</span>
              <div className="flex items-center space-x-1">
                {getStatusIcon(systemStatus?.keycloak)}
                <span>{getStatusText(systemStatus?.keycloak)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Информация о пользователе */}
        {isAuthenticated && userInfo && (
          <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
            <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-gray-900 truncate">
                {userInfo.username || 'Пользователь'}
              </div>
              <div className="text-xs text-green-600 font-medium">
                Авторизация отключена
              </div>
            </div>
          </div>
        )}

        {/* Кнопка выхода отключена (авторизация отключена) */}
        {/* {isAuthenticated && (
          <button
            onClick={onLogout}
            className="w-full flex items-center justify-center px-4 py-2 rounded-lg text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 transition-colors"
            title="Выйти из системы"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Выйти
          </button>
        )} */}
      </div>
    </div>
  );
};

export default Sidebar;
