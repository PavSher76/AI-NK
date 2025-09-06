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
  HelpCircle,
  Activity
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
        className={`w-full flex items-center px-4 py-3.5 rounded-xl text-sm font-medium transition-all duration-300 group ${
          isActive
            ? 'bg-gradient-to-r from-primary-50 to-primary-100 text-primary-700 shadow-soft border border-primary-200'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50 hover:shadow-soft'
        }`}
      >
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center mr-3 transition-all duration-300 ${
          isActive 
            ? 'bg-primary-500 text-white shadow-soft' 
            : 'bg-gray-100 text-gray-600 group-hover:bg-primary-100 group-hover:text-primary-600'
        }`}>
          <Icon className="w-4 h-4" />
        </div>
        <span className="flex-1 text-left">{item.label}</span>
        {isActive && (
          <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
        )}
      </button>
    );
  };

  return (
    <div className="w-72 bg-white/95 backdrop-blur-md shadow-large h-screen flex flex-col border-r border-gray-100">
      {/* Логотип и название */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div 
            className="flex items-center cursor-pointer hover:opacity-80 transition-all duration-300 group"
            onClick={() => handlePageClick('dashboard')}
          >
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-soft group-hover:shadow-glow transition-all duration-300">
              <BookOpen className="h-6 w-6 text-white" />
            </div>
            <div className="ml-3">
              <span className="text-xl font-bold text-gray-900 tracking-tight">AI-НК</span>
              <p className="text-xs text-gray-500 font-medium">Система нормоконтроля</p>
            </div>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="lg:hidden p-2 rounded-xl hover:bg-gray-100 transition-all duration-300 group"
              title="Закрыть меню"
            >
              <X className="w-5 h-5 text-gray-600 group-hover:text-gray-900 transition-colors" />
            </button>
          )}
        </div>
      </div>

      {/* Навигационные ссылки */}
      <div className="flex-1 p-4 overflow-y-auto scrollbar-thin">
        <nav className="space-y-1">
          {navigationItems.map(renderNavigationItem)}
        </nav>
      </div>

      {/* Нижняя часть с информацией о пользователе и выходом */}
      <div className="p-4 border-t border-gray-100 space-y-4">
        {/* Статус системы */}
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-4 border border-gray-200">
          <div className="text-sm font-semibold text-gray-800 mb-3 flex items-center">
            <Activity className="w-4 h-4 mr-2 text-primary-600" />
            Статус системы
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 font-medium">Gateway</span>
              <div className="flex items-center space-x-2">
                {getStatusIcon(systemStatus?.gateway)}
                <span className={`text-xs font-medium px-2 py-1 rounded-lg ${
                  systemStatus?.gateway ? 'status-success' : 'status-error'
                }`}>
                  {getStatusText(systemStatus?.gateway)}
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 font-medium">Ollama</span>
              <div className="flex items-center space-x-2">
                {getStatusIcon(systemStatus?.ollama)}
                <span className={`text-xs font-medium px-2 py-1 rounded-lg ${
                  systemStatus?.ollama ? 'status-success' : 'status-error'
                }`}>
                  {getStatusText(systemStatus?.ollama)}
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 font-medium">Keycloak</span>
              <div className="flex items-center space-x-2">
                {getStatusIcon(systemStatus?.keycloak)}
                <span className={`text-xs font-medium px-2 py-1 rounded-lg ${
                  systemStatus?.keycloak ? 'status-success' : 'status-error'
                }`}>
                  {getStatusText(systemStatus?.keycloak)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Информация о пользователе */}
        {isAuthenticated && userInfo && (
          <div className="flex items-center space-x-3 p-4 bg-gradient-to-r from-success-50 to-success-100 rounded-xl border border-success-200">
            <div className="w-10 h-10 bg-gradient-to-br from-success-500 to-success-600 rounded-xl flex items-center justify-center shadow-soft">
              <User className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-gray-900 truncate">
                {userInfo.username || 'Пользователь'}
              </div>
              <div className="text-xs text-success-600 font-medium">
                Авторизация отключена
              </div>
            </div>
          </div>
        )}

        {/* Кнопка выхода отключена (авторизация отключена) */}
        {/* {isAuthenticated && (
          <button
            onClick={onLogout}
            className="w-full flex items-center justify-center px-4 py-3 rounded-xl text-sm font-medium text-error-600 hover:text-error-700 hover:bg-error-50 transition-all duration-300 border border-error-200 hover:border-error-300"
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
