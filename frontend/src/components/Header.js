import React from 'react';
import { Menu, Bell, User, Cog } from 'lucide-react';

const Header = ({ 
  currentPage, 
  onToggleSidebar,
  isSidebarOpen,
  onSystemSettingsClick
}) => {
  const getPageTitle = () => {
    switch (currentPage) {
      case 'dashboard':
        return 'Дашборд';
      case 'chat':
        return 'Чат с ИИ';
      case 'normcontrol':
        return 'Нормоконтроль';
      case 'documents':
        return 'Нормативные документы';
      case 'calculations':
        return 'Расчеты';
      case 'ntd-consultation':
        return 'Консультация НТД';
      default:
        return 'AI-НК';
    }
  };

  const getPageIcon = () => {
    switch (currentPage) {
      case 'dashboard':
        return '📊';
      case 'chat':
        return '💬';
      case 'normcontrol':
        return '📋';
      case 'documents':
        return '📚';
      case 'calculations':
        return '🧮';
      case 'ntd-consultation':
        return '🤖';
      default:
        return '🏠';
    }
  };

  return (
    <header className="bg-white/80 backdrop-blur-md shadow-soft border-b border-gray-100 h-18 flex items-center justify-between px-6 sticky top-0 z-40">
      {/* Левая часть - кнопка меню и заголовок */}
      <div className="flex items-center space-x-4">
        <button
          onClick={onToggleSidebar}
          className="p-2.5 rounded-xl hover:bg-gray-100 transition-all duration-300 lg:hidden group"
          title="Открыть/закрыть меню"
        >
          <Menu className="w-5 h-5 text-gray-600 group-hover:text-gray-900 transition-colors" />
        </button>
        
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-soft">
            <span className="text-lg">{getPageIcon()}</span>
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-900 tracking-tight">
              {getPageTitle()}
            </h1>
            <p className="text-sm text-gray-500">
              {currentPage === 'dashboard' && 'Обзор системы'}
              {currentPage === 'chat' && 'Общение с искусственным интеллектом'}
              {currentPage === 'normcontrol' && 'Проверка документов на соответствие нормам'}
              {currentPage === 'documents' && 'Управление нормативными документами'}
              {currentPage === 'calculations' && 'Инженерные расчеты'}
              {currentPage === 'ntd-consultation' && 'Консультации по нормативно-технической документации'}
            </p>
          </div>
        </div>
      </div>

      {/* Правая часть - действия */}
      <div className="flex items-center space-x-3">
        <button
          className="p-2.5 rounded-xl hover:bg-gray-100 transition-all duration-300 group relative"
          title="Уведомления"
        >
          <Bell className="w-5 h-5 text-gray-600 group-hover:text-gray-900 transition-colors" />
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-error-500 rounded-full"></span>
        </button>
        
        <button
          onClick={onSystemSettingsClick}
          className="p-2.5 rounded-xl hover:bg-gray-100 transition-all duration-300 group"
          title="Системные настройки"
        >
          <Cog className="w-5 h-5 text-gray-600 group-hover:text-gray-900 transition-colors" />
        </button>
        
        <div className="w-px h-8 bg-gray-200"></div>
        
        <button
          className="flex items-center space-x-2 p-2 rounded-xl hover:bg-gray-100 transition-all duration-300 group"
          title="Профиль пользователя"
        >
          <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center">
            <User className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900 transition-colors">
            Пользователь
          </span>
        </button>
      </div>
    </header>
  );
};

export default Header;
