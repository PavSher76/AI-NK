import React, { useState, useEffect } from 'react';
import { 
  Home, 
  MessageSquare, 
  FileText, 
  BookOpen, 
  Calculator,
  User, 
  LogOut,
  X,
  HelpCircle,
  Building,
  Thermometer,
  Wind,
  Zap,
  Droplets,
  Flame,
  Volume2,
  Sun,
  Mountain,
  Shield,
  FileCheck,
  Building2,
  Upload,
  Search,
  BarChart3,
  ChevronDown,
  ChevronRight
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
  // Состояние для отслеживания открытых подменю
  const [openSubmenus, setOpenSubmenus] = useState(new Set());

  // Автоматически открываем подменю, если текущая страница находится в нем
  useEffect(() => {
    const newOpenSubmenus = new Set();
    
    // Проверяем, находится ли текущая страница в каком-либо подменю
    navigationItems.forEach(item => {
      if (item.submenu) {
        const hasActiveSubItem = item.submenu.some(subItem => currentPage === subItem.id);
        if (hasActiveSubItem) {
          newOpenSubmenus.add(item.id);
        }
      }
    });
    
    setOpenSubmenus(newOpenSubmenus);
  }, [currentPage]);

  const handlePageClick = (page) => {
    console.log('🔍 [DEBUG] Sidebar.js: handlePageClick called with page:', page);
    onPageChange(page);
  };

  const toggleSubmenu = (itemId) => {
    setOpenSubmenus(prev => {
      const newSet = new Set(prev);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return newSet;
    });
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
      id: 'outgoing-control',
      label: 'Выходной контроль корреспонденции',
      icon: FileCheck,
      onClick: () => handlePageClick('outgoing-control')
    },
    {
      id: 'ntd-consultation',
      label: 'Консультация НТД от ИИ',
      icon: HelpCircle,
      onClick: () => handlePageClick('ntd-consultation')
    },
    {
      id: 'analog-objects',
      label: 'Объекты аналоги',
      icon: Building2,
      onClick: () => handlePageClick('analog-objects'),
      submenu: [
        {
          id: 'analog-objects-list',
          label: 'Список объектов',
          icon: Building2,
          onClick: () => handlePageClick('analog-objects-list')
        },
        {
          id: 'analog-objects-upload',
          label: 'Пакетная загрузка',
          icon: Upload,
          onClick: () => handlePageClick('analog-objects-upload')
        },
        {
          id: 'analog-objects-search',
          label: 'Поиск аналогов',
          icon: Search,
          onClick: () => handlePageClick('analog-objects-search')
        },
        {
          id: 'analog-objects-analytics',
          label: 'Аналитика',
          icon: BarChart3,
          onClick: () => handlePageClick('analog-objects-analytics')
        }
      ]
    },
    {
      id: 'calculations',
      label: 'Расчеты',
      icon: Calculator,
      onClick: () => handlePageClick('calculations'),
      submenu: [
        {
          id: 'structural-calculations',
          label: 'Строительные конструкции',
          icon: Building,
          onClick: () => handlePageClick('structural-calculations')
        },
        {
          id: 'degasification-calculations',
          label: 'Дегазация угольных шахт',
          icon: Wind,
          onClick: () => handlePageClick('degasification-calculations')
        },
        {
          id: 'foundation-calculations',
          label: 'Основания и фундаменты',
          icon: Mountain,
          onClick: () => handlePageClick('foundation-calculations')
        },
        {
          id: 'thermal-calculations',
          label: 'Теплотехнические',
          icon: Thermometer,
          onClick: () => handlePageClick('thermal-calculations')
        },
        {
          id: 'ventilation-calculations',
          label: 'Вентиляция и кондиционирование',
          icon: Wind,
          onClick: () => handlePageClick('ventilation-calculations')
        },
        {
          id: 'electrical-calculations',
          label: 'Электротехнические',
          icon: Zap,
          onClick: () => handlePageClick('electrical-calculations')
        },
        {
          id: 'water-supply-calculations',
          label: 'Водоснабжение и водоотведение',
          icon: Droplets,
          onClick: () => handlePageClick('water-supply-calculations')
        },
        {
          id: 'fire-safety-calculations',
          label: 'Пожарная безопасность',
          icon: Flame,
          onClick: () => handlePageClick('fire-safety-calculations')
        },
        {
          id: 'acoustic-calculations',
          label: 'Акустические',
          icon: Volume2,
          onClick: () => handlePageClick('acoustic-calculations')
        },
        {
          id: 'lighting-calculations',
          label: 'Освещение и инсоляция',
          icon: Sun,
          onClick: () => handlePageClick('lighting-calculations')
        },
        {
          id: 'geological-calculations',
          label: 'Инженерно-геологические',
          icon: Mountain,
          onClick: () => handlePageClick('geological-calculations')
        },
        {
          id: 'uav-protection-calculations',
          label: 'Защита от БПЛА',
          icon: Shield,
          onClick: () => handlePageClick('uav-protection-calculations')
        }
      ]
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
    const hasSubmenu = item.submenu && item.submenu.length > 0;
    const isSubmenuActive = hasSubmenu && item.submenu.some(subItem => currentPage === subItem.id);
    const isSubmenuOpen = openSubmenus.has(item.id);

    return (
      <div key={item.id} className="space-y-1">
        <button
          onClick={() => {
            if (hasSubmenu) {
              toggleSubmenu(item.id);
            } else {
              item.onClick();
            }
          }}
          className={`w-full flex items-center px-4 py-3.5 rounded-xl text-sm font-medium transition-all duration-300 group ${
            isActive || isSubmenuActive
              ? 'bg-gradient-to-r from-primary-50 to-primary-100 text-primary-700 shadow-soft border border-primary-200'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50 hover:shadow-soft'
          }`}
        >
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center mr-3 transition-all duration-300 ${
            isActive || isSubmenuActive
              ? 'bg-primary-500 text-white shadow-soft' 
              : 'bg-gray-100 text-gray-600 group-hover:bg-primary-100 group-hover:text-primary-600'
          }`}>
            <Icon className="w-4 h-4" />
          </div>
          <span className="flex-1 text-left">{item.label}</span>
          {hasSubmenu && (
            <div className="flex items-center">
              {isSubmenuOpen ? (
                <ChevronDown className="w-4 h-4 text-gray-400 transition-all duration-300" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-400 transition-all duration-300" />
              )}
            </div>
          )}
          {isActive && !hasSubmenu && (
            <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
          )}
        </button>
        
        {/* Подменю с анимацией */}
        {hasSubmenu && (
          <div className={`overflow-hidden transition-all duration-300 ease-in-out ${
            isSubmenuOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
          }`}>
            <div className="ml-4 space-y-1 pt-1">
              {item.submenu.map((subItem) => {
                const SubIcon = subItem.icon;
                const isSubActive = currentPage === subItem.id;
                
                return (
                  <button
                    key={subItem.id}
                    onClick={subItem.onClick}
                    className={`w-full flex items-center px-3 py-2 rounded-lg text-xs font-medium transition-all duration-300 group ${
                      isSubActive
                        ? 'bg-primary-100 text-primary-700 border border-primary-200'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <div className={`w-6 h-6 rounded-md flex items-center justify-center mr-2 transition-all duration-300 ${
                      isSubActive
                        ? 'bg-primary-500 text-white' 
                        : 'bg-gray-100 text-gray-500 group-hover:bg-primary-100 group-hover:text-primary-600'
                    }`}>
                      <SubIcon className="w-3 h-3" />
                    </div>
                    <span className="flex-1 text-left">{subItem.label}</span>
                    {isSubActive && (
                      <div className="w-1.5 h-1.5 bg-primary-500 rounded-full"></div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
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
              <span className="text-xl font-bold text-gray-900 tracking-tight">AI-Engineering</span>
              <p className="text-xs text-gray-500 font-medium">ИИ в проектировании</p>
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
