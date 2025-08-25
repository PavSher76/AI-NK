import React from 'react';
import { Menu } from 'lucide-react';

const Header = ({ 
  currentPage, 
  onToggleSidebar,
  isSidebarOpen 
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
      default:
        return 'AI-НК';
    }
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 h-16 flex items-center justify-between px-6">
      {/* Левая часть - кнопка меню и заголовок */}
      <div className="flex items-center space-x-4">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors lg:hidden"
          title="Открыть/закрыть меню"
        >
          <Menu className="w-5 h-5 text-gray-600" />
        </button>
        
        <h1 className="text-xl font-semibold text-gray-900">
          {getPageTitle()}
        </h1>
      </div>

      {/* Правая часть - пустая для баланса */}
      <div className="flex items-center space-x-2">
      </div>
    </header>
  );
};

export default Header;
